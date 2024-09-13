from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import os
import requests

def read_csv(file_path):
    """Read the CSV file and return a DataFrame."""
    return pd.read_csv(file_path)

def init_webdriver(headless=True):
    """Initialize the Selenium WebDriver using webdriver_manager."""
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 10)
    return driver, wait

def gather_table_data(driver, wait):
    """Extract all data from the table on the webpage and return as a dictionary."""
    table_data = {}
    # Locate the table rows
    rows = wait.until(EC.presence_of_all_elements_located(
        (By.XPATH, "//div[@class='Body_MiddlePanel']//tr[not(ancestor::tbody[@style='display:none'])]")))

    for row in rows:
        cells = row.find_elements(By.TAG_NAME, "td")
        if len(cells) < 2:
            continue
        key = cells[0].text.strip().replace("\n", " ")
        value = cells[1].text.strip().replace("\n", " ")
        table_data[key] = value

    return table_data

def check_and_download_strategy(driver):
    """Check for links in the 'Liigi tegevuskava' section and download if they contain 'getdoc'."""
    strategy_present = False
    strategy_files = []
    strategy_folder = "strategy_materials"
    os.makedirs(strategy_folder, exist_ok=True)

    try:
        links = driver.find_elements(By.XPATH,
                                     "//td[contains(text(), 'Liigi tegevuskava')]//following-sibling::td/a[contains(@href, 'getdok')]")
        for link in links:
            href = link.get_attribute("href")
            file_name = "{}.pdf".format(link.text.strip().replace("\n", " ") or "strategy_document")
            response = requests.get(href)

            if response.status_code == 200:
                with open(os.path.join(strategy_folder, file_name), 'wb') as file:
                    file.write(response.content)
                strategy_present = True
                strategy_files.append(file_name)
    except Exception as e:
        print(f"Error downloading strategy: {e}")

    return strategy_present, strategy_files

def process_csv_and_extract_data(csv_file_path, updated_csv_file_path):
    """Main function to read CSV, extract data from EELIS links, and save updated CSV."""
    df = read_csv(csv_file_path)
    driver, wait = init_webdriver(headless=False)  # Change to headless=True for headless mode

    all_columns = set(df.columns)

    # Ensure necessary columns exist
    strategy_present_column = 'strategy_present'
    strategy_file_column = 'strategy_file'

    if strategy_present_column not in all_columns:
        df[strategy_present_column] = False

    if strategy_file_column not in all_columns:
        df[strategy_file_column] = None

    # Function to process each row
    for idx, row in df.iterrows():
        eelis_link = row['EELIS link']
        if eelis_link == "NotFound":
            continue

        driver.get(eelis_link)

        # Extract table data
        table_data = gather_table_data(driver, wait)

        # Check for strategy
        strategy_present, strategy_files = check_and_download_strategy(driver)
        df.at[idx, strategy_present_column] = strategy_present
        if strategy_present:
            df.at[idx, strategy_file_column] = "; ".join(strategy_files)

        # Add new data to DataFrame
        for key, value in table_data.items():
            key = key.replace("\n", " ").strip()
            value = value.replace("\n", " ").strip()
            if key not in all_columns:
                df[key] = None
                all_columns.add(key)
            df.at[idx, key] = value

    # Close the browser
    driver.quit()

    # Save the updated DataFrame back to CSV
    df.to_csv(updated_csv_file_path, index=False)
    print(f"Updated CSV saved to {updated_csv_file_path}")


# Example usage
process_csv_and_extract_data('EELIS_kaitsekategooria_selgroogsed_loomad.csv', 'EELIS_additional_data.csv')
