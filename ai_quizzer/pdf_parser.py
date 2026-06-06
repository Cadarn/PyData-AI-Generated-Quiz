from pathlib import Path
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat
from langchain_text_splitters import RecursiveCharacterTextSplitter


class PDFParser:
    def __init__(self):
        # Configure pipeline options for higher fidelity
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = True  # Enable OCR for images/scanned text
        pipeline_options.do_table_structure = True  # Enhanced table recognition

        # We can also enable image/figure extraction if needed for Phase 3
        # pipeline_options.images_scale = 2.0

        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )


    def convert_to_markdown(self, pdf_path: str | Path) -> str:
        """Converts a PDF document to Markdown structure."""
        if isinstance(pdf_path, str):
            pdf_path = Path(pdf_path)

        if pdf_path.is_file():
            document = self.converter.convert(pdf_path).document
        else:
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        return document.export_to_markdown()

    def parse_and_save(self, pdf_path: str | Path, output_dir: str | Path) -> dict[str, Path]:
        """Converts a PDF document to Markdown and JSON and saves them to the specified directory."""
        output_dir = Path(output_dir)
        pdf_path = Path(pdf_path)

        if isinstance(pdf_path, str):
            pdf_path = Path(pdf_path)

        if not pdf_path.is_file():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        # Convert and get the document object
        result = self.converter.convert(pdf_path)
        document = result.document

        output_dir.mkdir(parents=True, exist_ok=True)

        # Save Markdown
        markdown_content = document.export_to_markdown()
        md_path = output_dir / f"{pdf_path.stem}.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        # Save JSON
        json_path = output_dir / f"{pdf_path.stem}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(document.model_dump_json())

        return {"markdown": md_path, "json": json_path}

    def get_semantic_chunks(self, pdf_path: str | Path, max_chunk_size: int = 1500) -> list[dict]:
        """
        Parses a PDF and splits it into semantic, layout-aware chunks
        preserving exact page numbers, headers, and element layout types from IBM Docling.
        """
        if isinstance(pdf_path, str):
            pdf_path = Path(pdf_path)

        if not pdf_path.is_file():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        result = self.converter.convert(pdf_path)
        document = result.document

        # Handle different Docling versions for element access
        if hasattr(document, "elements"):
            elements = document.elements
        elif hasattr(document, "body") and hasattr(document.body, "children"):
            elements = document.body.children
        else:
            elements = []

        final_chunks = []
        current_header = "General"
        
        # Temporary buffers for active chunk aggregation
        active_chunk_text = []
        active_chunk_pages = set()
        active_chunk_types = set()
        active_char_count = 0

        def emit_current_chunk():
            nonlocal active_chunk_text, active_chunk_pages, active_chunk_types, active_char_count
            if not active_chunk_text:
                return
            
            combined_text = "\n\n".join(active_chunk_text)
            # Include Section header prefix for robust synthesis context
            context_text = f"Section: {current_header}\n\n{combined_text}"
            
            final_chunks.append({
                "header": current_header,
                "text": context_text,
                "page_numbers": sorted(list(active_chunk_pages)),
                "element_types": sorted(list(active_chunk_types)),
                "source_snippet": combined_text
            })
            
            # Reset buffers
            active_chunk_text = []
            active_chunk_pages = set()
            active_chunk_types = set()
            active_char_count = 0

        for element in elements:
            item = element
            if hasattr(element, "resolve"):
                item = element.resolve(document)

            item = getattr(item, "item", item)
            label = getattr(item, "label", "unknown")
            
            if label == "table" and hasattr(item, "export_to_markdown"):
                try:
                    text = item.export_to_markdown(document)
                except Exception:
                    try:
                        text = item.export_to_markdown()
                    except Exception:
                        text = getattr(item, "text", "")
            else:
                text = getattr(item, "text", "")

            # If it's a section header, emit current active chunk and transition
            if label == "section_header":
                emit_current_chunk()
                current_header = text if text else "General"
                continue

            # Only index valuable content layers (text, table, list items)
            if label in ["text", "table", "list_item", "paragraph"] and text.strip():
                # Extract page number from Docling element provenance
                page_no = None
                if hasattr(item, "prov") and item.prov:
                    page_no = item.prov[0].page_no
                
                # If this item alone exceeds the limit, emit first
                if active_char_count + len(text) > max_chunk_size:
                    emit_current_chunk()

                # Add to buffers
                active_chunk_text.append(text)
                if page_no:
                    active_chunk_pages.add(page_no)
                active_chunk_types.add(label)
                active_char_count += len(text)

        # Emit any trailing content
        emit_current_chunk()
        return final_chunks

