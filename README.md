# Etherscan Labels Scraper

This project is designed to scrape Ethereum accounts or token data from Etherscan.

The dumped label data for both accounts and tokens is provided from the last scrape conducted in December 2024.

Some labels for accounts are empty due to errors from the Etherscan backend server.

## **Setup Instructions**

### **1. Install Python and Dependencies**

Install the required Python packages by running:
```bash
pip install -r requirements.txt
```

### **2. Configure the `config.json` File**
1. Open the `config.json` file in a text editor.
2. Specify the path to your Chromium **user data directory** and profile:
   ```json
   {
       "user_data_dir": "/path/to/your/chromium/user/data/dir",
       "profile_directory": "Default"
   }
   ```
   Replace `/path/to/your/chromium/user/data/dir` with the absolute path to your Chromium user data directory.

   Example for a Snap installation of Chromium:
   ```json
   {
       "user_data_dir": "/home/username/snap/chromium/common/chromium",
       "profile_directory": "Default"
   }
   ```

### **3. Log in to Etherscan**
1. Open Chromium manually using the same profile specified in `config.json`:
   ```bash
   chromium --user-data-dir=/path/to/your/chromium/user/data/dir --profile-directory=Default
   ```
2. Navigate to [Etherscan Label Cloud](https://etherscan.io/labelcloud).
3. Log in to your Etherscan account to ensure access to the required pages.
4. Visit one of the labels (e.g., "Exchange") to ensure you're logged in and can view label data.

### **4. Run the Scraper**
Choose the appropriate script for your use case:

#### **For Account Scraping:**
Run the `accounts.py` script to scrape Ethereum accounts:
```bash
python accounts.py
```

#### **For Token Scraping:**
Run the `tokens.py` script to scrape Ethereum tokens:
```bash
python tokens.py
```

## **Output**
The scripts will save the scraped data in CSV format under the `accounts/` or `tokens/` directory. Each label will have its own CSV file.

## **Notes**
- Modify the `config.json` as needed to point to the correct user data directory and profile.
- Ensure you are authenticated on the Etherscan pages by manually logging in to one of the label pages.
- Some labels may return no data even though they exist, due to Etherscan backend server errors.