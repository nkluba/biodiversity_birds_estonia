import os
import fitz  # PyMuPDF
import pytesseract
from pdf2image import convert_from_path
from openai import OpenAI

openai_api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=openai_api_key)

def is_scanned_pdf(pdf_path):
    """
    Check if a PDF is a scanned document.
    """
    pdf_document = fitz.open(pdf_path)
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        if page.get_text("text"):
            return False
    return True


def extract_text_from_scanned_pdf(pdf_path):
    """
    Use OCR to extract text from a scanned PDF.
    """
    images = convert_from_path(pdf_path)
    text = ''
    for image in images:
        text += pytesseract.image_to_string(image, lang='est')
    return text


def clean_text_with_gpt(text):
    """
    Clean and logically update text using GPT.
    """
    prompt = f"This text was detected with OCR and it might contain errors. Please clean it and update it to be logical: \n\n{text}"

    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system",
             "content": "You are a helpful assistant that cleans and enhances text extracted with OCR."},
            {"role": "user", "content": prompt}
        ],
        stream=True
    )

    cleaned_text = ""
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            cleaned_text += chunk.choices[0].delta.content

    return cleaned_text.strip()


def process_directory(directory):
    """
    Process directory to find and clean scanned PDFs.
    """
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.pdf'):
                pdf_path = os.path.join(root, file)
                if is_scanned_pdf(pdf_path):
                    print(f'Processing scanned PDF: {pdf_path}')
                    raw_text = extract_text_from_scanned_pdf(pdf_path)
                    cleaned_text = clean_text_with_gpt(raw_text)
                    output_path = os.path.splitext(pdf_path)[0] + '_cleaned.txt'
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(cleaned_text)


if __name__ == '__main__':
    process_directory('strategy_materials')
