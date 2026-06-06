from ai_quizzer.pdf_parser import PDFParser
from pathlib import Path

def main():
    # Define paths
    pdf_path = Path("data/documents/SoFC26_Guide.pdf")
    output_dir = Path("data/parsed")
    
    print(f"Parsing {pdf_path}...")
    
    # Initialize parser and process the document
    parser = PDFParser()
    saved_paths = parser.parse_and_save(pdf_path, output_dir)
    
    print(f"Successfully parsed and saved to:")
    print(f"  Markdown: {saved_paths['markdown']}")
    print(f"  JSON:     {saved_paths['json']}")

if __name__ == "__main__":
    main()
