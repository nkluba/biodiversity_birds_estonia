import requests
import re
import pandas as pd


def fetch_page(url):
    """
    Fetch the plain text content of the web page.

    :param url: URL of the web page.
    :return: Plain text content of the web page.
    """
    response = requests.get(url)
    response.raise_for_status()  # Raise an exception for HTTP errors
    return response.text


def extract_species_data(text, section_title, category):
    """
    Extract species data from the plain text content.

    :param text: The plain text content of the page.
    :param section_title: The section title to search for (e.g., 'I kaitsekategooria selgroogsed loomad').
    :param category: The extinction category.
    :return: List of extracted species data.
    """
    data = []
    # Find the section in the text
    section_pattern = re.compile(rf'{section_title}(.*?)(?:§|\Z)', re.DOTALL)
    section_match = section_pattern.search(text)

    if section_match:
        section_text = section_match.group(1)
        # Match the pattern of Estonian Name and Latin Name within the section
        species_pattern = re.compile(r'\d+\)\s+([^\n]+?)[\t\s]+([\w\s]+);')
        for match in species_pattern.finditer(section_text):
            estonian_name = match.group(1).strip()
            latin_name = match.group(2).strip()
            data.append([estonian_name, latin_name, category])

    return data


def parse_species_data(url, sections):
    """
    Parse species data from a web page.

    :param url: URL of the web page.
    :param sections: Dictionary of section titles and their corresponding categories.
    :return: List of all extracted species data.
    """
    all_data = []
    text = fetch_page(url)

    print(text)

    for section_title, category in sections.items():
        all_data.extend(extract_species_data(text, section_title, category))

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
