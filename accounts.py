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
        href.split("/accounts/label/")[1].replace("+", "") for href in (elem.get_attribute("href") 
        for elem in driver.find_elements("xpath", "//a[@href]")) if "/accounts/label/" in href
    ]
    
    return labels

def get_labels(driver, labels, start_label=None, end_label=None):  
    start_index = labels.index(start_label) if start_label and start_label in labels else 0
    end_index = labels.index(end_label) + 1 if end_label and end_label in labels else len(labels)

    for label in labels[start_index:end_index]:
        driver.get(f"https://etherscan.io/accounts/label/{label}")
        cookies = {cookie["name"]: cookie["value"] for cookie in driver.get_cookies()}

        subcats = [
            elem.get_attribute("id").split("table-subcatid-")[-1]
            for elem in driver.find_elements("css selector", "table[id^='table-subcatid-']")
        ]

        df = pd.DataFrame(columns=["Address", "Name Tag", "Label"])

        label_name = driver.find_element("css selector", "div.text-muted.text-break").text.strip()

        for subcat in subcats:
            index = 0
            while True:
                page = index // 1000 + 1
                api_url = "https://etherscan.io/accounts.aspx/GetTableEntriesBySubLabel"
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
                            {"data": "address"},
                            {"data": "nameTag"},
                            {"data": "balance"},
                            {"data": "txnCount"},
                        ],
                        "order": [],
                        "start": index,
                        "length": 1000,
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
                        address_match = re.search(r'data-bs-title=["\']([^"\']+)["\']', item.get("address", ""))
                        address = address_match.group(1)
                    except Exception:
                        contract_address = None

                    try:
                        name_tag = item.get("nameTag", "")
                    except Exception:
                        name_tag = None

                    new_row = pd.DataFrame([[address, name_tag, label_name]], columns=["Address", "Name Tag", "Label"])
                    df = pd.concat([df, new_row], ignore_index=True)

                index += 1000

        df.to_csv(f"accounts/{label}.csv", index=False)
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
    finished = [os.path.splitext(filename)[0] for filename in os.listdir("accounts") if filename.endswith(".csv")]
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