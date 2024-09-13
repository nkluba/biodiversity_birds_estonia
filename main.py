import requests
from bs4 import BeautifulSoup
import pandas as pd


def fetch_page(url):
    """
    Fetch the HTML content of the web page.

    :param url: URL of the webpage.
    :return: The raw HTML content.
    """
    response = requests.get(url)
    response.raise_for_status()  # Raise an exception for HTTP errors
    return response.content


def extract_species_data(soup, section_title, category):
    """
    Extract species data from a specific section of the HTML content.

    :param soup: BeautifulSoup object of the parsed HTML content.
    :param section_title: The section title to search for (e.g., 'I kaitsekategooria selgroogsed loomad').
    :param category: The extinction category.
    :return: List of extracted species data.
    """
    data = []
    # Find the section in the text
    section_header = soup.find('a', {'name': section_title})
    if section_header:
        table = section_header.find_next('table')
        if table:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    estonian_name = cells[0].text.strip()
                    latin_name = cells[1].text.strip(';').strip()
                    data.append([estonian_name, latin_name, category])

    return data


def parse_species_data(url, sections):
    """
    Parse species data from a web page.

    :param url: URL of the web page.
    :param sections: Dictionary of section titles and their corresponding categories.
    :return: List of extracted species data.
    """
    all_data = []
    html_content = fetch_page(url)
    soup = BeautifulSoup(html_content, "html.parser")

    for section_title, category in sections.items():
        all_data.extend(extract_species_data(soup, section_title, category))

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
        'para4': 'I',  # I kaitsekategooria selgroogsed loomad
        'lg11': 'II'  # II kaitsekategooria selgroogsed loomad
    }

    sections_url_2 = {
        'lg5': 'III'  # III kaitsekategooria selgroogsed loomad
    }

    data_1 = parse_species_data(url_1, sections_url_1)
    data_2 = parse_species_data(url_2, sections_url_2)

    all_data = data_1 + data_2
    save_to_csv(all_data, "kaitsekategooria_selgroogsed_loomad.csv")


if __name__ == "__main__":
    main()
