import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from ai_quizzer.question_generator import QuestionGenerator
from ai_quizzer.prompts import render_prompt

def test_render_prompt():
    """Verifies that all three Jinja2 templates render correctly without syntax errors."""
    # 1. MCQ distractor rendering
    mcq_prompt = render_prompt(
        "mcq_post_process.jinja",
        context="Mock context content.",
        question="Mock question?",
        correct_answer="Mock answer."
    )
    assert "Mock context content." in mcq_prompt
    assert "Mock question?" in mcq_prompt
    assert "Mock answer." in mcq_prompt
    assert "British English" in mcq_prompt
    
    # 2. Long-Form post process rendering
    lf_prompt = render_prompt(
        "long_form_post_process.jinja",
        context="Financial crime context.",
        question="Explain syndicate scaling?",
        correct_answer="They route via scams.",
        min_words=50,
        max_words=200,
        max_marks=5
    )
    assert "Financial crime context." in lf_prompt
    assert "Explain syndicate scaling?" in lf_prompt
    assert "50" in lf_prompt
    assert "200" in lf_prompt
    assert "5" in lf_prompt
    assert "British English" in lf_prompt

    # 3. Live Judge rendering
    judge_prompt = render_prompt(
        "live_judge.jinja",
        question="What is MLaaS?",
        ideal_response="It stands for Money Laundering as a Service.",
        mark_scheme=["Point 1", "Point 2"],
        keywords=["laundering", "service"],
        user_answer="I think it is laundering.",
        max_marks=2
    )
    assert "What is MLaaS?" in judge_prompt
    assert "Money Laundering as a Service" in judge_prompt
    assert "Point 1" in judge_prompt
    assert "laundering" in judge_prompt
    assert "I think it is laundering." in judge_prompt
    assert "British English" in judge_prompt

# --- Dummy Config and Data Fixtures ---

@pytest.fixture
def temp_config_file(tmp_path):
    config_content = """
model_name: "mock-model"
output_path: "mock_output.json"
question_types:
  mcq:
    count: 2
    distractor_count: 3
  long_form:
    count: 1
    max_marks: 5
    target_length_min: 10
    target_length_max: 50
    rubric_detail: "detailed"
"""
    config_file = tmp_path / "quiz_config.yaml"
    config_file.write_text(config_content)
    return config_file


# --- Tests ---

@patch("ai_quizzer.question_generator.OpenAI")
def test_config_loading(mock_openai_class, temp_config_file):
    """Verifies that QuestionGenerator correctly reads the YAML configuration file."""
    generator = QuestionGenerator(config_path=temp_config_file)
    assert generator.model_name == "mock-model"
    assert generator.output_path == Path("mock_output.json")
    assert generator.mcq_config["count"] == 2
    assert generator.mcq_config["distractor_count"] == 3
    assert generator.lf_config["count"] == 1
    assert generator.lf_config["max_marks"] == 5


@patch("ai_quizzer.question_generator.OpenAI")
def test_post_process_mcq_success(mock_openai_class, temp_config_file):
    """Tests successful conversion of raw Q&A into structured MCQ with distractors."""
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    
    # Mocking OpenAI response
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content=json.dumps({
                    "question": "Refined MCQ question?",
                    "options": ["A", "B", "C", "D"],
                    "correct": "B",
                    "explanation": "Test explanation."
                })
            )
        )
    ]
    mock_client.chat.completions.create.return_value = mock_response

    generator = QuestionGenerator(config_path=temp_config_file)
    result = generator._post_process_mcq("raw q", "raw a", "context")

    assert result["question"] == "Refined MCQ question?"
    assert result["options"] == ["A", "B", "C", "D"]
    assert result["correct"] == "B"
    assert result["explanation"] == "Test explanation."


@patch("ai_quizzer.question_generator.OpenAI")
def test_post_process_mcq_fallback(mock_openai_class, temp_config_file):
    """Tests that the MCQ generator falls back gracefully if the API fails or returns bad data."""
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    
    # Mocking an API error
    mock_client.chat.completions.create.side_effect = Exception("API error")

    generator = QuestionGenerator(config_path=temp_config_file)
    result = generator._post_process_mcq("What is X?", "Correct X", "context")

    assert result["question"] == "What is X?"
    assert "Correct X" in result["options"]
    assert result["correct"] == "Correct X"
    assert "fallback" in result["explanation"].lower()


@patch("ai_quizzer.question_generator.OpenAI")
def test_post_process_long_form_success(mock_openai_class, temp_config_file):
    """Tests successful generation of a Long-Form question and model answer object."""
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    
    # Mocking OpenAI response for Long-Form
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content=json.dumps({
                    "question": "Discuss the impact of X.",
                    "ideal_response": "This is the perfect long answer.",
                    "mark_scheme": ["Mark 1 info", "Mark 2 info"],
                    "keywords": ["money", "laundering"],
                    "explanation": "Compliance context."
                })
            )
        )
    ]
    mock_client.chat.completions.create.return_value = mock_response

    generator = QuestionGenerator(config_path=temp_config_file)
    result = generator._post_process_long_form("raw q", "raw a", "context")

    assert result["question"] == "Discuss the impact of X."
    assert result["ideal_response"] == "This is the perfect long answer."
    assert len(result["mark_scheme"]) == 2
    assert "money" in result["keywords"]
    assert result["explanation"] == "Compliance context."


@patch("ai_quizzer.question_generator.OpenAI")
def test_post_process_long_form_fallback(mock_openai_class, temp_config_file):
    """Tests that the Long-Form generator falls back gracefully if the API fails."""
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    mock_client.chat.completions.create.side_effect = Exception("API error")

    generator = QuestionGenerator(config_path=temp_config_file)
    result = generator._post_process_long_form("Why is X important?", "X is vital.", "context")

    assert result["question"] == "Why is X important?"
    assert result["ideal_response"] == "X is vital."
    assert len(result["mark_scheme"]) == 5  # default max_marks in config
    assert result["keywords"] == ["important?"]
    assert "compliance" in result["explanation"].lower()


@patch("ai_quizzer.question_generator.PDFParser")
@patch("ai_quizzer.question_generator.Synthesizer")
@patch("ai_quizzer.question_generator.OpenAI")
def test_generate_quiz_pipeline(mock_openai_class, mock_synthesizer_class, mock_pdf_parser_class, temp_config_file, tmp_path):
    """Tests the full generation pipeline from parsed semantic chunks to structured JSON output."""
    # 1. Mock Parser
    mock_parser = MagicMock()
    mock_pdf_parser_class.return_value = mock_parser
    mock_parser.get_semantic_chunks.return_value = [
        {"header": "H1", "text": "This is chunk 1 context."},
        {"header": "H2", "text": "This is chunk 2 context."},
        {"header": "H3", "text": "This is chunk 3 context."}
    ]

    # 2. Mock Synthesizer
    mock_synthesizer = MagicMock()
    mock_synthesizer_class.return_value = mock_synthesizer
    
    # Mocking the Golden objects produced by DeepEval Synthesizer
    class MockGolden:
        def __init__(self, input_q, expected, ctx):
            self.input = input_q
            self.expected_output = expected
            self.context = ctx

    mock_synthesizer.generate_goldens_from_contexts.return_value = [
        MockGolden("raw q1", "ans 1", ["ctx 1"]),
        MockGolden("raw q2", "ans 2", ["ctx 2"]),
        MockGolden("raw q3", "ans 3", ["ctx 3"])
    ]

    # 3. Mock OpenAI for both MCQs and Long-Form
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    
    # Setup generator with custom output path to temp dir
    generator = QuestionGenerator(config_path=temp_config_file)
    output_json = tmp_path / "quiz_questions.json"
    generator.output_path = output_json
    
    # Mock the internal post processors to avoid double mocking the OpenAI chat
    generator._post_process_mcq = MagicMock(side_effect=[
        {"question": "MCQ 1?", "options": ["A", "B"], "correct": "A", "explanation": "E1"},
        {"question": "MCQ 2?", "options": ["C", "D"], "correct": "C", "explanation": "E2"}
    ])
    
    generator._post_process_long_form = MagicMock(return_value={
        "question": "LF 1?",
        "ideal_response": "ideal 1",
        "mark_scheme": ["P1", "P2"],
        "keywords": ["kw"],
        "explanation": "EL1"
    })

    # 4. Act: Create a fake PDF file
    fake_pdf = tmp_path / "SoFC26_Guide.pdf"
    fake_pdf.write_text("fake pdf bytes")
    
    quiz_data = generator.generate_quiz(fake_pdf)

    # 5. Assertions
    assert "mcq" in quiz_data
    assert "long_form" in quiz_data
    assert len(quiz_data["mcq"]) == 2  # count from config
    assert len(quiz_data["long_form"]) == 1  # count from config
    
    # Check that output JSON was actually written
    assert output_json.is_file()
    with open(output_json, "r") as f:
        saved_data = json.load(f)
        assert len(saved_data["mcq"]) == 2
        assert len(saved_data["long_form"]) == 1
        assert saved_data["mcq"][0]["question"] == "MCQ 1?"
        assert saved_data["long_form"][0]["question"] == "LF 1?"
