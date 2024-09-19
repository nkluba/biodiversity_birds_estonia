import os
import subprocess
from pathlib import Path
import shlex

def convert_pdf_to_txt(pdf_file_path, output_dir=None) -> bool:
    try:
        # Determine the output directory
        pdf_path = Path(pdf_file_path)
        output_directory = Path(output_dir) if output_dir else pdf_path.parent

        # Construct the output text file path
        txt_file_name = pdf_path.stem + "_cleaned.txt"
        txt_file_path = output_directory / txt_file_name

        # Ensure the PDF file exists
        if not pdf_path.is_file():
            print(f"The specified file does not exist: {pdf_file_path}")
            return False

        # Ensure the output directory exists
        output_directory.mkdir(parents=True, exist_ok=True)

        # Run the pdftotext command
        cmd = f"pdftotext -layout {shlex.quote(str(pdf_file_path))} {shlex.quote(str(txt_file_path))}"
        subprocess.run(cmd, shell=True, check=True)

        print(f"PDF file has been converted to text file: {txt_file_path}")
        return True

    except subprocess.CalledProcessError as e:
        print(f"An error occurred while converting PDF to text: {e}")
        return False

def process_pdfs(pdf_folder):
    pdf_folder_path = Path(pdf_folder)

    for pdf_path in pdf_folder_path.glob('*.pdf'):
        updated_txt_path = pdf_folder_path / (pdf_path.stem + "_cleaned.txt")

        if not updated_txt_path.exists():
            convert_pdf_to_txt(pdf_path)


if __name__ == "__main__":
    os.chdir('/home/teks/PycharmProjects/biodiversity')
    pdf_folder = 'strategy_materials'  # Folder containing the PDF files
    process_pdfs(pdf_folder)
