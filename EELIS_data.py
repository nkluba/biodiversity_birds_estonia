from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd


def read_csv(file_path):
    """ Read the CSV file and return a DataFrame. """
    return pd.read_csv(file_path)


def init_webdriver(headless=True):
    """Initialize the Selenium WebDriver using webdriver_manager."""
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument('--headless')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 10)
    return driver, wait


def search_and_get_link(driver, wait, url, estonian_name, latin_name):
    """Search for the species on the provided URL using the second search window and return the first link found."""
    driver.get(url)

    # Find the second search input field and enter the search keyword
    search_field = wait.until(EC.presence_of_element_located((By.ID, 'otsi_nimi')))
    search_field.clear()
    search_field.send_keys(f"{estonian_name} ({latin_name})")

    # Find and click the search button in the second search window
    search_button = driver.find_element(By.XPATH, "//input[@type='submit' and @form='sObjSearchFormId']")
    search_button.click()

    try:
        # Wait for search results and capture the first result link
        result_link = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".Body_MiddlePanel a[href*='/lnim/']")))
        link = result_link.get_attribute('href')
    except Exception:
        link = "NotFound"

    return link


def process_csv_and_search_links(csv_file_path, updated_csv_file_path, url):
    """ Main function to read CSV, search for each species using the second search window, and save updated CSV. """
    df = read_csv(csv_file_path)
    driver, wait = init_webdriver(headless=False)  # Change to headless=True for headless mode

    # Function to process each row
    def process_row(row):
        return search_and_get_link(driver, wait, url, row['Estonian Name'], row['Latin Name'])

    # Apply the process_row function to each row
    df['EELIS link'] = df.apply(lambda row: process_row(row), axis=1)

    # Close the browser
    driver.quit()

    # Save the updated DataFrame back to CSV
    df.to_csv(updated_csv_file_path, index=False)
    print(f"Updated CSV saved to {updated_csv_file_path}")


# Define file paths and URLs
csv_file_path = 'kaitsekategooria_selgroogsed_loomad.csv'
updated_csv_file_path = 'updated_kaitsekategooria_selgroogsed_loomad.csv'
url = 'https://infoleht.keskkonnainfo.ee/artikkel/1389049207'

# Run the script
process_csv_and_search_links(csv_file_path, updated_csv_file_path, url)
