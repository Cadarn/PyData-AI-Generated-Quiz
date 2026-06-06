from dataclasses import dataclass, field, replace

@dataclass
class QuizState:
    question_list: list[dict]
    is_expert_mode: bool = False
    total_questions: int = field(init=False)
    current_question_index: int = 0
    score: int = 0  # MCQ correct count, or sum of marks for Expert mode
    is_finished: bool = False

    # Question fields
    is_submitted: bool = False
    selected_answer: str | None = None  # Holds selected MCQ option, or user's free text input
    
    # Histories
    answer_history: list = field(init=False)       # List of bools (for MCQ correctness or Expert pass status)
    submitted_texts: list = field(init=False)      # List of str (for Expert mode user answers)
    grading_results: list = field(init=False)      # List of dicts (for Expert mode DeepEval feedback)

    def __post_init__(self):
        if not self.question_list:
            raise ValueError("Question list cannot be empty.")
        self.total_questions = len(self.question_list)
        # Pre-initialize histories to match question count
        self.answer_history = [None] * self.total_questions
        self.submitted_texts = [None] * self.total_questions
        self.grading_results = [None] * self.total_questions

    def select_answer(self, answer: str):
        """Updates the selected answer or free-text response for the current question."""
        if self.is_submitted:
            return  # Prevent changing answer after submission
        self.selected_answer = answer

    def submit_answer(self):
        """Handles the logic when a user submits an answer."""
        if self.is_submitted or self.selected_answer is None:
            return

        question_details = self.question_list[self.current_question_index]
        
        if not self.is_expert_mode:
            # MCQ Mode
            is_correct = (self.selected_answer == question_details["correct"])
            self.is_submitted = True
            self.score += 1 if is_correct else 0
            self.answer_history[self.current_question_index] = is_correct
        else:
            # Expert Mode (Live grading is triggered externally in main.py)
            self.is_submitted = True
            self.submitted_texts[self.current_question_index] = self.selected_answer

    def set_grading_result(self, score: float, reasoning: str, marks_awarded: int):
        """Sets the DeepEval Live Judge grading feedback for the current long-form question."""
        self.grading_results[self.current_question_index] = {
            "score": score,
            "reasoning": reasoning,
            "marks_awarded": marks_awarded
        }
        self.score += marks_awarded
        # Consider a score of 3/5 or higher as a "passing/correct" answer in final summary
        self.answer_history[self.current_question_index] = (marks_awarded >= 3)

    def copy(self):
        """Return a new QuizState instance for Marimo state updates, preserving all progress.

        dataclasses.replace() calls __post_init__ which resets the init=False list fields
        (answer_history, submitted_texts, grading_results). This method creates the replace()
        copy then restores those fields from the original.
        """
        new = replace(self)
        new.answer_history = list(self.answer_history)
        new.submitted_texts = list(self.submitted_texts)
        new.grading_results = list(self.grading_results)
        return new

    def next_question(self):
        """Advances to the next question or marks the quiz as finished."""
        if self.current_question_index < self.total_questions - 1:
            self.current_question_index += 1
            self.is_submitted = False  # Reset submission state for the next question
            self.selected_answer = None  # Clear selected answer for the next question
        else:
            self.is_finished = True