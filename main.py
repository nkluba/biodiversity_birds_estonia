import requests
from bs4 import BeautifulSoup
import pandas as pd


def fetch_page(url):
    """
    Fetch the content of the web page.

    :param url: URL of the web page.
    :return: BeautifulSoup object of the parsed HTML content.
    """
    response = requests.get(url)
    print(response.content)
    response.raise_for_status()  # Raise an exception for HTTP errors
    return BeautifulSoup(response.content, "html.parser")


def extract_species_data(soup, title_text, category):
    """
    Extract species data from a specific section of the HTML content.

    :param soup: BeautifulSoup object of the parsed HTML content.
    :param title_text: The title text to search for (e.g., 'I kaitsekategooria selgroogsed loomad').
    :param category: The extinction category.
    :return: List of extracted species data.
    """
    data = []

    section_header = soup.find(string=title_text)
    if section_header:
        section = section_header.find_parent("section")
        if section:  # Ensure the section is found
            items = section.find_all("p")
            for item in items:
                text = item.get_text().strip()
                if text:
                    parts = text.split('\n')
                    if len(parts) >= 2:
                        estonian_name = parts[0].split()[0]
                        latin_name = parts[1].strip(";")
                        data.append([estonian_name, latin_name, category])

    return data


def parse_species_data(url, sections):
    """
    Parse species data from a web page.

    :param url: URL of the web page.
    :param sections: Dictionary of title texts and their corresponding categories.
    :return: List of all extracted species data.
    """
    all_data = []
    soup = fetch_page(url)

    for title_text, category in sections.items():
        all_data.extend(extract_species_data(soup, title_text, category))

    return all_data


def save_to_csv(data, filename):
    """
    Save the data to a CSV file.

    :param data: List of species data.
    :param filename: The output CSV file name.
    """
    df = pd.DataFrame(data, columns=["Estonian Name", "Latin Name", "Category"])
    df.to_csv(filename, index=False)
    print(f"CSV file '{filename}' created successfully.")


def main():
    url_1 = "https://www.riigiteataja.ee/akt/118062014020"
    url_2 = "https://www.riigiteataja.ee/akt/104072014022"

    sections_url_1 = {
        'I kaitsekategooria selgroogsed loomad': 'I',
        'II kaitsekategooria selgroogsed loomad': 'II'
    }

    sections_url_2 = {
        'III kaitsekategooria selgroogsed loomad': 'III'
    }

    data_1 = parse_species_data(url_1, sections_url_1)
    data_2 = parse_species_data(url_2, sections_url_2)

    all_data = data_1 + data_2
    save_to_csv(all_data, "kaitsekategooria_selgroogsed_loomad.csv")


if __name__ == "__main__":
    main()
