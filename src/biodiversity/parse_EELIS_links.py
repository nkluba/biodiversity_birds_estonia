from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd


def read_csv(file_path):
    """Read the CSV file and return a DataFrame."""
    return pd.read_csv(file_path)


def init_webdriver(headless=True):
    """Initialize the Selenium WebDriver using webdriver_manager."""
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless")
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=options
    )
    wait = WebDriverWait(driver, 10)
    return driver, wait


def search_with_name(driver, wait, url, name):
    """Search for the species on the provided URL using the second search window and return the first link found."""
    driver.get(url)

    search_field = wait.until(EC.presence_of_element_located((By.ID, "otsi_nimi")))
    search_field.clear()
    search_field.send_keys(name)

    search_button = driver.find_element(
        By.XPATH, "//input[@type='submit' and @form='sObjSearchFormId']"
    )
    search_button.click()

    try:
        result_link = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".Body_MiddlePanel a[href*='/lnim/']")
            )
        )
        link = result_link.get_attribute("href")
    except Exception:
        link = "NotFound"

    return link


def search_and_get_link(driver, wait, url, estonian_name, latin_name):
    """Search for the species on the provided URL using the second search window and return the first link found."""
    combined_name = f"{estonian_name} ({latin_name})"
    link = search_with_name(driver, wait, url, combined_name)
    if link == "NotFound":
        link = search_with_name(driver, wait, url, estonian_name)
    return link


def process_csv_and_search_links(csv_file_path, updated_csv_file_path, url, headless=True):
    """Main function to read CSV, search for each species using the second search window, and save updated CSV."""
    df = read_csv(csv_file_path)
    driver, wait = init_webdriver(headless=headless)

    def process_row(row):
        return search_and_get_link(driver, wait, url, row["Estonian Name"], row["Latin Name"])

    df["EELIS link"] = df.apply(lambda row: process_row(row), axis=1)

    driver.quit()

    df.to_csv(updated_csv_file_path, index=False)
    print(f"Updated CSV saved to {updated_csv_file_path}")


def main(
    input_csv_path: str = "st1_kaitsekategooria_selgroogsed_loomad.csv",
    output_csv_path: str = "st2_EELIS_kaitsekategooria_selgroogsed_loomad.csv",
    url: str = "https://infoleht.keskkonnainfo.ee/artikkel/1389049207",
    headless: bool = True,
) -> None:
    process_csv_and_search_links(input_csv_path, output_csv_path, url, headless=headless)


if __name__ == "__main__":
    main()
