import os
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


def process_pdfs_in_csv(filename, output_filename="st5_relevant_pdf_reports.csv"):
    """ Process each row in the CSV file """
    df = pd.read_csv(filename)

    for index, row in df.iterrows():
        files = str(row["strategy_file"]).split(",")
        if len(files) > 1:
            name = row["Estonian Name"]
            if not name:
                continue

            max_mentions = 0
            most_mentions_file = None

            for pdf in files:
                pdf = pdf.strip()
                if not pdf:
                    continue
                text = extract_text_from_pdf(pdf)
                if text is None:
                    continue
                mentions = count_occurrences(text, name)
                if mentions > max_mentions:
                    max_mentions = mentions
                    most_mentions_file = pdf

            if most_mentions_file:
                df.at[index, "strategy_file"] = most_mentions_file.replace(
                    "strategy_materials/", ""
                )
            else:
                df.at[index, "strategy_file"] = "Not Present"

    df.to_csv(output_filename, index=False)


def main(
    input_filename: str = "st4_pdf_gathered.csv",
    output_filename: str = "st5_relevant_pdf_reports.csv",
) -> None:
    process_pdfs_in_csv(input_filename, output_filename)


if __name__ == "__main__":
    main()