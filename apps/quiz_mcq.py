import marimo

__generated_with = "0.20.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

    import dataclasses
    import marimo as mo
    import marimo._output.data.data as mo_data
    import dotenv

    dotenv.load_dotenv()

    from ai_quizzer.quiz_data import load_config, load_quiz_questions
    from ai_quizzer.quiz_logic import QuizState
    from ai_quizzer.quiz_styles import CSS
    from ai_quizzer.quiz_ui import build_irag_modal

    return CSS, QuizState, build_irag_modal, dataclasses, load_config, load_quiz_questions, mo, mo_data


@app.cell
def _(CSS, mo):
    mo.Html(CSS)
    return


@app.cell
def _(load_config, load_quiz_questions):
    config = load_config()
    mcq_count = config.get("question_types", {}).get("mcq", {}).get("quiz_count")
    mcqs, _ = load_quiz_questions(mcq_count=mcq_count)
    pdf_path = config.get("pdf_path", "data/documents/SoFC26_Guide.pdf")
    return mcqs, pdf_path


@app.cell
def _(mo):
    get_state, set_state = mo.state(None)
    get_active_citation, set_active_citation = mo.state(None)
    return get_active_citation, get_state, set_active_citation, set_state


@app.cell
def _(get_state):
    state = get_state()
    return (state,)


@app.cell
def _(get_active_citation):
    active_citation = get_active_citation()
    return (active_citation,)


@app.cell
def _(state):
    def generate_score_message() -> str:
        percentage = (state.score / state.total_questions) * 100
        if percentage >= 80:
            return "Compliance Mastery! 🏆🌟"
        elif percentage >= 50:
            return "Solid Compliance Officer! 💼👍"
        return "Needs Remedial Training! 📚🚨"

    def get_hover_text(row, column, value):
        row_idx = int(row)
        q = state.question_list[row_idx]
        if column == "Result":
            correct = q.get("correct")
            if not state.answer_history[row_idx]:
                return f"Incorrect. Correct answer: {correct}"
            return f"Correct! ✓: {correct}"
        return ""

    return generate_score_message, get_hover_text


@app.cell
def _(generate_score_message, get_hover_text, mo, state):
    def generate_final_visual():
        results_table = [
            {"Q#": i + 1, "Result": "✅" if p else "❌", "Question": q["question"]}
            for i, (q, p) in enumerate(zip(state.question_list, state.answer_history))
        ]
        return mo.vstack(
            [
                mo.md(f"# {generate_score_message()}"),
                mo.md(f"## Final Score: {state.score} / {state.total_questions}"),
                mo.md("Hover over **Result** cells for correct answer detail."),
                mo.ui.table(
                    results_table,
                    pagination=False,
                    selection=None,
                    wrapped_columns=["Question"],
                    hover_template=get_hover_text,
                ),
            ]
        )

    return (generate_final_visual,)


@app.cell
def _(mo):
    mo.md(r"""
    # 🏛️ Financial Crime Quizzer — Easy Mode
    *Multiple-choice questions with instant feedback and source evidence.*
    """)
    return


@app.cell
def _(
    QuizState,
    active_citation,
    build_irag_modal,
    dataclasses,
    generate_final_visual,
    mcqs,
    mo,
    mo_data,
    pdf_path,
    set_active_citation,
    set_state,
    state,
):
    def start_quiz(_):
        set_state(QuizState(question_list=mcqs, is_expert_mode=False))

    if state is None:
        start_btn = mo.ui.button(label="Start Quiz 🚀", on_click=start_quiz)
        welcome = mo.md("""
        ### Welcome to Easy Mode
        Test your knowledge with multiple-choice questions drawn from your source document.

        - Select one of the four options for each question
        - Click **Submit Answer** to check your response
        - Use **Show Evidence** to view the source passage in the original PDF
        - Navigate through all questions to see your final score
        """).callout(kind="info")
        display_content = mo.vstack([welcome, start_btn], gap=2)

    elif state.is_finished:
        reset_btn = mo.ui.button(
            label="Restart Quiz 🔄",
            on_click=lambda _: set_state(None),
        )
        display_content = mo.vstack([generate_final_visual(), reset_btn], gap=2)

    else:
        q_idx = state.current_question_index
        current_q = state.question_list[q_idx]

        radio_kwargs = dict(
            options={opt: opt for opt in current_q["options"]},
            label=f"**Question {q_idx + 1} of {state.total_questions}**\n\n{current_q['question']}",
            disabled=state.is_submitted,
        )
        if state.is_submitted and state.selected_answer:
            radio_kwargs["value"] = state.selected_answer

        answer_input = mo.ui.radio(**radio_kwargs)

        def submit_and_grade(_):
            val = answer_input.value
            if not val:
                return
            state.select_answer(val)
            state.submit_answer()
            set_state(state.copy())

        submit_btn = mo.ui.button(
            label="Submit Answer 📤",
            on_click=submit_and_grade,
            disabled=state.is_submitted,
        )

        is_last = q_idx == state.total_questions - 1
        next_btn = mo.ui.button(
            label="Reveal Final Results 📊" if is_last else "Next Question ➡️",
            on_click=lambda _: state.next_question() or set_state(state.copy()),
        )

        has_reference = bool(current_q.get("reference", {}).get("page_numbers"))
        evidence_btn = (
            mo.ui.button(
                label="Show Evidence 📖",
                on_click=lambda _: set_active_citation(current_q),
            )
            if has_reference
            else None
        )

        if state.is_submitted:
            callout_kind = "success" if state.answer_history[q_idx] else "danger"
            text = current_q.get("explanation", "No explanation provided.")
            parts = [mo.md(f"**Correct Answer**: {current_q['correct']}\n\n**Explanation:**\n{text}")]
            if evidence_btn is not None:
                parts.append(evidence_btn)
            explanation_box = mo.vstack(parts, gap=1).callout(kind="info")
        else:
            callout_kind = "neutral"
            explanation_box = None

        button_panel = mo.hstack(
            [submit_btn, next_btn] if state.is_submitted else [submit_btn],
            justify="start",
            gap=2,
        )

        if explanation_box is not None:
            quiz_panel = mo.hstack(
                [answer_input.callout(kind=callout_kind), explanation_box],
                align="start",
                gap=2,
            )
        else:
            quiz_panel = answer_input.callout(kind=callout_kind)

        close_btn = mo.ui.button(label="Close ✕", on_click=lambda _: set_active_citation(None))
        modal_overlay = build_irag_modal(
            active_citation, pdf_path, mo, mo_data, close_btn
        )

        quit_btn = mo.ui.button(
            label="⬅ Quit Quiz",
            on_click=lambda _: set_state(None),
        )
        quit_overlay = mo.hstack([quit_btn]).style({
            "position": "fixed",
            "bottom": "24px",
            "right": "24px",
            "z-index": "100",
        })

        display_content = mo.vstack([quiz_panel, button_panel, quit_overlay], gap=2)
        if modal_overlay is not None:
            display_content = mo.vstack([display_content, modal_overlay])

    display_content
    return


if __name__ == "__main__":
    app.run()
