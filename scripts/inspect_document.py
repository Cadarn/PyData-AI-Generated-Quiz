from ai_quizzer.pdf_parser import PDFParser
from pathlib import Path

def print_document_map(document):
    """Prints a summary of the document's internal element tree."""
    print(f"{'Element Type':<15} | {'Level':<6} | {'Content Snippet'}")
    print("-" * 60)
    
    # In Docling 2.x, document.body is the root GroupItem
    # We want to iterate through its children (Nodes)
    if hasattr(document, "body") and hasattr(document.body, "children"):
        nodes = document.body.children
    else:
        print("Could not find hierarchical body. Falling back to flat elements.")
        nodes = getattr(document, "elements", [])

    for i, node in enumerate(nodes):
        # In Docling 2.x hierarchy, nodes have an 'item' which is the actual content
        item = getattr(node, "item", node)
        
        # Resolve if it's a reference (common in some versions)
        if hasattr(item, "resolve"):
            item = item.resolve(document)

        label = getattr(item, "label", "unknown")
        # Handle Enum labels
        if hasattr(label, "value"):
            label = label.value
            
        text = getattr(item, "text", "")
        level = getattr(item, "level", "-")

        if label == "table":
            snippet = f"[Table]"
        else:
            snippet = text[:60].replace("\n", " ")

        print(f"{str(label):<15} | {str(level):<6} | {snippet}...")
        
        if i > 50: 
            print("...")
            break
        
        # Limit output for brevity if needed
        if i > 100: 
            print("...")
            break

def main():
    pdf_path = Path("data/documents/SoFC26_Guide.pdf")
    if not pdf_path.exists():
        print(f"Error: Could not find {pdf_path}")
        return

    print(f"Analyzing structure of {pdf_path.name}...\n")
    
    # Use existing parser
    parser = PDFParser()
    result = parser.converter.convert(pdf_path)
    document = result.document
    
    print_document_map(document)

if __name__ == "__main__":
    main()
