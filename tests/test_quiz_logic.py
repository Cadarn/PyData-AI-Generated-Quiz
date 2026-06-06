import pytest
from ai_quizzer.quiz_logic import QuizState

# --- Sample Fixtures ---

@pytest.fixture
def sample_mcq_questions():
    return [
        {
            "question": "What is 1 + 1?",
            "options": ["1", "2", "3", "4"],
            "correct": "2",
            "explanation": "Simple arithmetic."
        },
        {
            "question": "What is the capital of France?",
            "options": ["London", "Paris", "Berlin"],
            "correct": "Paris",
            "explanation": "Paris is the capital."
        }
    ]

@pytest.fixture
def sample_lf_questions():
    return [
        {
            "question": "Explain the role of MLaaS.",
            "ideal_response": "MLaaS commercialises laundering using professional infrastructure.",
            "mark_scheme": ["Commercialisation noted", "Outsourced infrastructure", "AI behavioral monitoring"],
            "keywords": ["laundering", "infrastructure", "compliance"],
            "explanation": "Deep compliance concept."
        }
    ]

# --- Tests ---

def test_quiz_state_mcq_initialization(sample_mcq_questions):
    """Verifies MCQ QuizState initializes correctly."""
    state = QuizState(question_list=sample_mcq_questions, is_expert_mode=False)
    assert state.total_questions == 2
    assert state.current_question_index == 0
    assert state.score == 0
    assert not state.is_finished
    assert not state.is_submitted
    assert state.selected_answer is None
    assert state.answer_history == [None, None]

def test_quiz_state_expert_initialization(sample_lf_questions):
    """Verifies Expert/Long-form QuizState initializes correctly."""
    state = QuizState(question_list=sample_lf_questions, is_expert_mode=True)
    assert state.total_questions == 1
    assert state.is_expert_mode
    assert state.answer_history == [None]
    assert state.grading_results == [None]

def test_select_and_submit_mcq_correct(sample_mcq_questions):
    """Verifies correct MCQ submission updates score and answer history."""
    state = QuizState(question_list=sample_mcq_questions)
    
    # Select and submit correct answer
    state.select_answer("2")
    assert state.selected_answer == "2"
    
    state.submit_answer()
    assert state.is_submitted
    assert state.score == 1
    assert state.answer_history[0] is True
    
    # Try changing answer after submission (should be blocked)
    state.select_answer("3")
    assert state.selected_answer == "2"

def test_select_and_submit_mcq_incorrect(sample_mcq_questions):
    """Verifies incorrect MCQ submission handles scores properly."""
    state = QuizState(question_list=sample_mcq_questions)
    
    # Select and submit incorrect answer
    state.select_answer("3")
    state.submit_answer()
    assert state.score == 0
    assert state.answer_history[0] is False

def test_next_question_and_finish(sample_mcq_questions):
    """Verifies navigating through questions and finishing works correctly."""
    state = QuizState(question_list=sample_mcq_questions)
    
    # Submit first
    state.select_answer("2")
    state.submit_answer()
    
    # Advance to next
    state.next_question()
    assert state.current_question_index == 1
    assert not state.is_submitted
    assert state.selected_answer is None
    assert not state.is_finished
    
    # Submit second
    state.select_answer("Paris")
    state.submit_answer()
    
    # Advance to end
    state.next_question()
    assert state.is_finished

def test_expert_grading_flow(sample_lf_questions):
    """Verifies that expert long-form grading logic updates scores and histories correctly."""
    state = QuizState(question_list=sample_lf_questions, is_expert_mode=True)
    
    # Select and submit text response
    state.select_answer("My written answer about MLaaS.")
    state.submit_answer()
    
    assert state.is_submitted
    assert state.submitted_texts[0] == "My written answer about MLaaS."
    
    # External Live Judge grading applied
    state.set_grading_result(score=0.8, reasoning="Excellent work.", marks_awarded=4)
    assert state.grading_results[0] == {
        "score": 0.8,
        "reasoning": "Excellent work.",
        "marks_awarded": 4
    }
    assert state.score == 4
    assert state.answer_history[0] is True  # Marks >= 3 counts as pass
