from pathlib import Path
import pytest
from ai_quizzer.pdf_parser import PDFParser

# --- Fixtures ---

@pytest.fixture
def default_parser():
    """Provides a fresh instance of the PDFParser for each test."""
    return PDFParser()

@pytest.fixture
def sample_pdf_path(request):
    """
    Returns the absolute path to the test PDF fixture.
    Points to: tests/fixtures/test_doc.pdf
    """
    # Finds the directory where this current test file (test_pdf_parser.py) lives
    test_dir = Path(request.node.fspath).parent
    path = test_dir / "fixtures" / "test_doc.pdf"
    
    if not path.exists():
        pytest.fail(f"Test fixture not found at {path}. Check your directory structure.")
    return path

# --- Tests ---

def test_parse_to_markdown(default_parser, sample_pdf_path):
    """Integration test: Verifies real PDF extraction logic."""
    result = default_parser.convert_to_markdown(sample_pdf_path)
    
    assert isinstance(result, str)
    assert len(result) > 0
    # Check for markdown header symbol
    assert "#" in result 

def test_save_parsed_content(tmp_path, default_parser, monkeypatch):
    """Unit test: Verifies file saving logic using a mock to isolate filesystem behavior."""
    # 1. Arrange: Create a dummy input file in the temp directory
    fake_pdf = tmp_path / "input.pdf"
    fake_pdf.write_text("dummy pdf bytes") 
    
    output_dir = tmp_path / "parsed_results"
    # Note: We don't manually mkdir() here to test if your code handles it!
    
    # 2. Mock: Intercept the heavy lifting
    mock_content = "# Mocked Markdown Content"
    mock_json = '{"mock": "json"}'
    
    class MockDocument:
        def export_to_markdown(self):
            return mock_content
        def model_dump_json(self):
            return mock_json
            
    class MockResult:
        def __init__(self):
            self.document = MockDocument()

    monkeypatch.setattr(default_parser.converter, "convert", lambda x: MockResult())

    # 3. Act
    saved_paths = default_parser.parse_and_save(fake_pdf, output_dir)
    
    # 4. Assert
    assert saved_paths["markdown"].exists()
    assert saved_paths["markdown"].suffix == ".md"
    assert saved_paths["json"].exists()
    assert saved_paths["json"].suffix == ".json"
    assert saved_paths["markdown"].read_text() == mock_content
    assert saved_paths["json"].read_text() == mock_json