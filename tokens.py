import os
import json
import re
import pandas as pd
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

def list_labels(driver):
    driver.get("https://etherscan.io/labelcloud")

    labels = [
        href.split("/tokens/label/")[1].replace("+", "") for href in (elem.get_attribute("href") 
        for elem in driver.find_elements("xpath", "//a[@href]")) if "/tokens/label/" in href
    ]
    
    return labels

def get_labels(driver, labels, start_label=None, end_label=None):  
    start_index = labels.index(start_label) if start_label and start_label in labels else 0
    end_index = labels.index(end_label) + 1 if end_label and end_label in labels else len(labels)

    for label in labels[start_index:end_index]:
        driver.get(f"https://etherscan.io/tokens/label/{label}")
        cookies = {cookie["name"]: cookie["value"] for cookie in driver.get_cookies()}

        subcats = [
            elem.get_attribute("id").split("table-subcatid-")[-1]
            for elem in driver.find_elements("css selector", "table[id^='table-subcatid-']")
        ]

        df = pd.DataFrame(columns=["Contract Address", "Token Name", "Website", "Label"])

        label_name = driver.find_element("css selector", "div.text-muted.text-break").text.strip()

        for subcat in subcats:
            index = 0
            while True:
                page = index // 100 + 1
                api_url = "https://etherscan.io/tokens.aspx/GetTokensBySubLabel"
                headers = {
                    "accept": "application/json, text/javascript, */*; q=0.01",
                    "content-type": "application/json",
                    "user-agent": driver.execute_script("return navigator.userAgent;"),
                    "x-requested-with": "XMLHttpRequest",
                }

                payload = {
                    "dataTableModel": {
                        "draw": 1,
                        "columns": [
                            {"data": "number"},
                            {"data": "contractAddress"},
                            {"data": "tokenName"},
                            {"data": "marketCap"},
                            {"data": "holders"},
                            {"data": "website"},
                        ],
                        "order": [],
                        "start": index,
                        "length": 100,
                        "search": {"value": "", "regex": False},
                    },
                    "labelModel": {"label": label, "subCategoryId": subcat},
                }

                response = requests.post(api_url, headers=headers, json=payload, cookies=cookies)
                data = response.json().get("d", {}).get("data", [])

                if not data:
                    print(f"There are no data received. Breaking...")
                    break

                print(f"Scraping page {page} for label: {label}, subcategory: {subcat}")

                for item in data:
                    try:
                        contract_match = re.search(r'data-bs-title="([^"]+)"', item.get("contractAddress", ""))
                        contract_address = contract_match.group(1)
                    except Exception:
                        contract_address = None

                    try:
                        token_match = re.search(r"title='([^']+)'", item.get("tokenName", ""))
                        token_name = token_match.group(1) if token_match else None

                        if not token_name:
                            fallback_match = re.search(r'<span class="hash-tag text-truncate">([^<]+)</span>', item.get("tokenName", ""))
                            token_name = fallback_match.group(1)
                    except Exception:
                        token_name = None

                    try:
                        symbol_match = re.search(r'<span class="text-muted">([^<]+)</span>', item.get("tokenName", ""))
                        token_symbol = symbol_match.group(1)
                    except Exception:
                        token_symbol = None

                    if token_name and token_symbol:
                        token_name = f"{token_name} ({token_symbol})"
                    elif token_name:
                        token_name = token_name
                    else:
                        token_name = None

                    try:
                        website_match = re.search(r'data-bs-title="([^"]+)"', item.get("website", ""))
                        website = website_match.group(1)
                    except Exception:
                        website = None

                    new_row = pd.DataFrame([[contract_address, token_name, website, label_name]], columns=["Contract Address", "Token Name", "Website", "Label"])
                    df = pd.concat([df, new_row], ignore_index=True)

                index += 100

        df.to_csv(f"tokens/{label}.csv", index=False)
        print(f"Data for label: {label} has been saved to {label}.csv.")

def main():
    with open("config.json", "r") as file:
        config = json.load(file)

    user_data_dir = config.get("user_data_dir")
    profile_directory = config.get("profile_directory", "Default")
    
    if not user_data_dir:
        raise ValueError("The 'user_data_dir' is missing in the configuration file.")

    options = webdriver.ChromeOptions()
    options.add_argument(f"--user-data-dir={user_data_dir}")
    options.add_argument(f"--profile-directory={profile_directory}")

    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

    labels = list_labels(driver)
    finished = [os.path.splitext(filename)[0] for filename in os.listdir("tokens") if filename.endswith(".csv")]
    remaining = [label for label in labels if label not in finished]

    print(f"Remaining labels: {remaining}")

    while True:
        start_label = input("Enter the starting label (default to the first label on the list): ").strip()
        if not start_label:
            start_label = None
            break
        if start_label in remaining:
            break
        print("Select a valid label from the list.")

    while True:
        end_label = input("Enter the ending label (default to the last label on the list): ").strip()
        if not end_label:
            end_label = None
            break
        if end_label in remaining:
            break
        print("Select a valid label from the list.")

    get_labels(driver, remaining, start_label, end_label)

if __name__ == "__main__":
    main()