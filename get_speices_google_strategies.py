import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
from googlesearch import search
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Define the directory to store downloaded PDF files
strategy_materials_dir = "strategy_materials"
csv_file = "EELIS_additional_data.csv"

def create_strategy_materials_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
        logging.info(f"Directory '{directory}' created.")

def load_csv(file_path):
    return pd.read_csv(file_path)

def save_csv(df, file_path):
    df.to_csv(file_path, index=False)
    logging.info(f"Updated CSV file saved to {file_path}")

def search_pdfs(query, num_results=10):
    logging.info(f"Searching for: {query}")
    pdf_links = []
    for result in search(query, num_results=num_results):
        if result.lower().endswith(".pdf"):
            pdf_links.append(result)
        if len(pdf_links) >= 3:
            break
    return pdf_links

def download_pdf(url, folder):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            file_name = os.path.join(folder, url.split('/')[-1])
            with open(file_name, 'wb') as f:
                f.write(response.content)
            logging.info(f"Downloaded: {url}")
            return file_name
        else:
            logging.warning(f"Failed to download {url}: Status code {response.status_code}")
    except Exception as e:
        logging.error(f"Failed to download {url}: {e}")
    return None

def update_dataframe(df, directory):
    for index, row in df.iterrows():
        if not row['strategy_present']:  # Check if strategy_present is False
            query = f'"kaitse tegevuskava" "{row["Estonian Name"]}" pdf'
            pdf_links = search_pdfs(query)
            downloaded_files = []
            for link in pdf_links:
                file_name = download_pdf(link, directory)
                if file_name:
                    downloaded_files.append(file_name)
            if downloaded_files:
                df.at[index, 'strategy_present'] = True
                df.at[index, 'strategy_file'] = ",".join(downloaded_files)
    return df

def main():
    create_strategy_materials_dir(strategy_materials_dir)
    df = load_csv(csv_file)
    df = update_dataframe(df, strategy_materials_dir)
    save_csv(df, csv_file)

if __name__ == "__main__":
    main()
