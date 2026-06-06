import marimo

__generated_with = "0.20.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import asyncio
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

    import dataclasses
    import marimo as mo
    import marimo._output.data.data as mo_data
    import dotenv

    dotenv.load_dotenv()

    from ai_quizzer.grader import run_live_judge
    from ai_quizzer.quiz_data import load_config, load_quiz_questions
    from ai_quizzer.quiz_logic import QuizState
    from ai_quizzer.quiz_styles import CSS
    from ai_quizzer.quiz_ui import build_irag_modal

    return (
        CSS,
        QuizState,
        asyncio,
        build_irag_modal,
        dataclasses,
        load_config,
        load_quiz_questions,
        mo,
        mo_data,
        run_live_judge,
    )


@app.cell
def _(CSS, mo):
    mo.Html(CSS)
    return


@app.cell
def _(load_config, load_quiz_questions):
    config = load_config()
    lf_count = config.get("question_types", {}).get("long_form", {}).get("quiz_count")
    _, lf_questions = load_quiz_questions(
        questions_path=config.get("output_path", "data/generated/quiz_questions.json"),
        lf_count=lf_count,
    )
    pdf_path = config.get("pdf_path", "data/documents/SoFC26_Guide.pdf")
    return lf_questions, pdf_path


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
        max_possible = state.total_questions * 5
        percentage = (state.score / max_possible) * 100
        if percentage >= 80:
            return "Compliance Mastery! 🏆🌟"
        elif percentage >= 50:
            return "Solid Compliance Officer! 💼👍"
        return "Needs Remedial Training! 📚🚨"

    def get_hover_text(row, column, value):
        row_idx = int(row)
        if column == "Marks":
            grading = state.grading_results[row_idx]
            if grading:
                return f"Feedback: {grading['reasoning'][:120]}..."
        return ""

    return generate_score_message, get_hover_text


@app.cell
def _(generate_score_message, get_hover_text, mo, state):
    def generate_final_visual():
        results_table = []
        for i, (q, pass_status, grading) in enumerate(
            zip(state.question_list, state.answer_history, state.grading_results)
        ):
            marks = grading.get("marks_awarded", 0) if grading else 0
            max_marks = len(q.get("mark_scheme", []))
            results_table.append(
                {
                    "Q#": i + 1,
                    "Marks": f"{marks} / {max_marks}",
                    "Status": "Passed ✅" if pass_status else "Needs Work ❌",
                    "Question": q["question"],
                }
            )
        max_possible = state.total_questions * 5
        pct = (state.score / max_possible) * 100 if max_possible else 0
        score_str = f"Total Marks: {state.score} / {max_possible} ({pct:.1f}%)"
        return mo.vstack(
            [
                mo.md(f"# {generate_score_message()}"),
                mo.md(f"## {score_str}"),
                mo.md("Hover over **Marks** cells for grading feedback."),
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
    # 🏛️ Financial Crime Quizzer — Expert Mode
    *Long-form questions graded by an AI judge against a structured mark scheme.*
    """)
    return


@app.cell
def _(
    QuizState,
    active_citation,
    asyncio,
    build_irag_modal,
    dataclasses,
    generate_final_visual,
    lf_questions,
    mo,
    mo_data,
    pdf_path,
    run_live_judge,
    set_active_citation,
    set_state,
    state,
):
    def start_quiz(_):
        set_state(QuizState(question_list=lf_questions, is_expert_mode=True))

    if state is None:
        start_btn = mo.ui.button(label="Start Expert Quiz 🚀", on_click=start_quiz)
        welcome = mo.md("""
        ### Welcome to Expert Mode
        Test your in-depth knowledge with free-text questions drawn from your source document.

        - Write a comprehensive answer in the text box provided
        - Click **Submit Answer** — an AI judge will score it against the mark scheme
        - Review your marks, the grading rationale, and the model ideal response
        - Use **Show Evidence** to view the source passage in the original PDF
        """).callout(kind="success")
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

        max_marks = len(current_q.get("mark_scheme", []))
        text_area_kwargs = dict(
            label=(
                f"**Question {q_idx + 1} of {state.total_questions}**\n\n"
                f"{current_q['question']}\n\n*({max_marks} marks)*"
            ),
            placeholder="Write your comprehensive answer here, address all the points of the question.",
            disabled=state.is_submitted,
            rows=7,
            full_width=True,
        )
        if state.is_submitted:
            text_area_kwargs["value"] = state.selected_answer or ""

        answer_input = mo.ui.text_area(**text_area_kwargs)

        def submit_and_grade(_):
            val = answer_input.value.strip()
            if not val:
                return
            state.select_answer(val)
            state.submit_answer()
            set_state(state.copy())  # Render "thinking" state immediately

            async def do_grading():
                loop = asyncio.get_running_loop()
                eval_res = await loop.run_in_executor(None, lambda: run_live_judge(
                    question=current_q["question"],
                    ideal_response=current_q.get("ideal_response", ""),
                    mark_scheme=current_q.get("mark_scheme", []),
                    keywords=current_q.get("keywords", []),
                    user_answer=val,
                ))
                state.set_grading_result(
                    score=eval_res.get("score", 0.0),
                    reasoning=eval_res.get("reasoning", ""),
                    marks_awarded=eval_res.get("marks_awarded", 0),
                )
                set_state(state.copy())

            asyncio.ensure_future(do_grading())

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

        grading = state.grading_results[q_idx] if state.is_submitted else None

        if state.is_submitted and grading is not None:
            callout_kind = "success" if state.answer_history[q_idx] else "danger"
            mark_scheme = current_q.get("mark_scheme", [])
            points_list = "\n".join(f"- {p}" for p in mark_scheme)
            keywords_str = ", ".join(f"`{k}`" for k in current_q.get("keywords", []))
            parts = [
                mo.md(f"""### ⚖️ Live Judge Evaluation

**Marks Awarded**: `{grading['marks_awarded']} / {len(mark_scheme)}` &nbsp;·&nbsp; Relevance Score: `{grading['score']:.2f}`

**Grading Rationale**:
{grading['reasoning']}

---
#### 🗺️ Ideal Model Answer
> {current_q.get('ideal_response', '')}

#### 📌 Mark Scheme:
{points_list}

**Expected keywords**: {keywords_str}
""")
            ]
            if evidence_btn is not None:
                parts.append(evidence_btn)
            explanation_box = mo.vstack(parts, gap=1).callout(kind=callout_kind)

        elif state.is_submitted and grading is None:
            callout_kind = "info"
            explanation_box = mo.md(
                "**Grading your answer...**\n\n"
                "*The AI judge is reviewing your response against the mark scheme. "
                "Usually 5–15 seconds.*"
            ).callout(kind="info")

        else:
            callout_kind = "neutral"
            explanation_box = None

        is_grading = state.is_submitted and grading is None
        show_next = state.is_submitted and grading is not None

        if is_grading:
            button_panel = mo.md("*Grading in progress — please wait...*")
        elif show_next:
            button_panel = mo.hstack([submit_btn, next_btn], justify="start", gap=2)
        else:
            button_panel = mo.hstack([submit_btn], justify="start", gap=2)

        if explanation_box is not None:
            quiz_panel = mo.vstack(
                [answer_input.callout(kind=callout_kind), explanation_box],
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
