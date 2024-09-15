import pandas as pd
import fitz  # PyMuPDF
import re


def extract_text_from_pdf(pdf_path):
    """ Extract text from a PDF file """
    try:
        document = fitz.open(pdf_path)
        text = ""
        for page_num in range(len(document)):
            page = document.load_page(page_num)
            text += page.get_text()
        return text
    except Exception as e:
        print(f"Could not extract text from {pdf_path}: {e}")
        return None


def count_occurrences(text, name):
    """ Count the occurrences of a name in the text """
    if not text:
        return 0
    return len(re.findall(name, text, re.IGNORECASE))


def process_pdfs_in_csv(filename):
    """ Process each row in the CSV file """
    df = pd.read_csv(filename)
    for index, row in df.iterrows():
        files = row['strategy_file'].split(',')
        if len(files) > 1:
            # Extract the Estonian name from the file string - you might need to adjust this
            name_match = re.search(r'^([^_]+)', row['strategy_file'])
            if not name_match:
                continue
            name = name_match.group(1)

            max_mentions = 0
            most_mentions_file = None

            for pdf in files:
                text = extract_text_from_pdf(pdf)
                if text is None:
                    continue
                mentions = count_occurrences(text, name)
                if mentions > max_mentions:
                    max_mentions = mentions
                    most_mentions_file = pdf

            if most_mentions_file:
                df.at[index, 'strategy_file'] = most_mentions_file.split('/')[-1]
            else:
                df.at[index, 'strategy_file'] = 'No match found'

    # Save the updated DataFrame back to CSV
    df.to_csv('updated_pdf_gathered.csv', index=False)


# Run the function with the filename
process_pdfs_in_csv('pdf_gathered.csv')
