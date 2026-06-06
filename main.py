import marimo

__generated_with = "0.20.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import marimo._output.data.data as mo_data
    import dataclasses
    import json
    from pathlib import Path

    from openai import OpenAI
    import dotenv

    dotenv.load_dotenv()

    from ai_quizzer.quiz_logic import QuizState
    from ai_quizzer.prompts import render_prompt

    return OpenAI, Path, QuizState, json, mo, mo_data, render_prompt


@app.cell
def _(mo):
    # CSS injection for high-fidelity compliance officer dashboard styling
    mo.Html("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

    /* Apply custom font globally across interactive elements */
    .marimo-app, .mo-markdown, .mo-hstack, .mo-vstack, body {
        font-family: 'Outfit', sans-serif !important;
    }

    /* Curved Premium Glassmorphic Callouts */
    .marimo-callout {
        border-radius: 16px !important;
        border: 1px solid rgba(240, 246, 252, 0.08) !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.15) !important;
        backdrop-filter: blur(6px) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }

    .marimo-callout.kind-success {
        background: rgba(46, 160, 67, 0.08) !important;
        border: 1px solid rgba(46, 160, 67, 0.2) !important;
    }

    .marimo-callout.kind-danger {
        background: rgba(248, 81, 73, 0.08) !important;
        border: 1px solid rgba(248, 81, 73, 0.2) !important;
    }

    .marimo-callout.kind-info {
        background: rgba(56, 139, 253, 0.08) !important;
        border: 1px solid rgba(56, 139, 253, 0.2) !important;
    }

    /* Slick Button hover micro-animations */
    button {
        font-family: 'Outfit', sans-serif !important;
        border-radius: 10px !important;
        font-weight: 500 !important;
        letter-spacing: 0.3px !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }

    button:hover:not(:disabled) {
        transform: translateY(-1.5px) !important;
        box-shadow: 0 4px 15px rgba(56, 139, 253, 0.3) !important;
    }

    textarea {
        font-family: 'Outfit', sans-serif !important;
        border-radius: 10px !important;
        border: 1px solid rgba(240, 246, 252, 0.15) !important;
        background: rgba(22, 27, 34, 0.5) !important;
        color: #e6edf3 !important;
        transition: border-color 0.2s ease !important;
    }

    textarea:focus {
        border-color: #58a6ff !important;
    }

    /* Ensure long radio options wrap gracefully instead of distorting the page layout */
    div[role="radiogroup"] {
        display: flex !important;
        flex-direction: column !important;
        gap: 12px !important;
        max-width: 100% !important;
    }

    div[role="radiogroup"] label {
        display: flex !important;
        align-items: flex-start !important;
        gap: 10px !important;
        white-space: normal !important;
        word-break: break-word !important;
        overflow-wrap: break-word !important;
        max-width: 100% !important;
        line-height: 1.4 !important;
        cursor: pointer !important;
    }
    /* Modal close button styling */
    div[style*="position: fixed"] button {
        background: #f85149 !important;
        color: white !important;
        border: none !important;
    }
    div[style*="position: fixed"] button:hover:not(:disabled) {
        background: #da3633 !important;
        box-shadow: 0 4px 15px rgba(248, 81, 73, 0.4) !important;
        transform: translateY(-1.5px) !important;
    }
    </style>
    """)
    return


@app.cell
def _(Path, json):
    # Setup fallbacks for initial test and offline resilience
    FALLBACK_MCQS = [
        {
            "question": "According to the report, what percentage of the global illicit economy does cybercrime account for?",
            "options": ["10-20%", "30-45%", "59-75%", "Over 90%"],
            "correct": "59-75%",
            "explanation": "Cybercrime has rapidly expanded to become the dominant force in the global illicit economy, now significantly outpacing traditional illicit markets. 🌐"
        },
        {
            "question": "What does the acronym 'MLaaS' stand for in the context of financial crime?",
            "options": ["Machine Learning as a Service", "Money Laundering as a Service", "Modern Leasing and Security", "Mobile Lending and Savings"],
            "correct": "Money Laundering as a Service",
            "explanation": "MLaaS represents the 'industrialisation' of financial crime, where specialised criminal syndicates provide professional laundering infrastructure to other groups for a fee. 💼"
        },
        {
            "question": "Which group was designated by the US Treasury in October 2025 for its role in Southeast Asian scam centres?",
            "options": ["The Lazarus Group", "Huione Group", "LockBit", "ShinyHunters"],
            "correct": "Huione Group",
            "explanation": "The Huione Group was sanctioned for its pivotal role in providing the financial 'backbone' for scam centres that rely on human trafficking and forced labour. 🏛️"
        }
    ]

    FALLBACK_LONG_FORM = [
        {
            "question": "Explain the concept of 'MLaaS' (Money Laundering as a Service) and discuss its implications for modern financial compliance.",
            "ideal_response": "MLaaS refers to the commercialization of money laundering services by specialized criminal syndicates, providing ready-made infrastructure to laundering clients for a fee. Key implications include the rapid scale and speed of illicit transaction routing, substantial difficulties for standard rules-based transaction monitoring systems, and the necessity for compliance officers to shift toward AI-driven semantic and behavior-based detection methods.",
            "mark_scheme": [
                "1 mark for explaining that MLaaS represents the 'commercialization' of money laundering infrastructure.",
                "1 mark for noting that laundering services are rented or outsourced by criminal syndicates.",
                "1 mark for discussing the implication of increased speed or scale of illicit routing.",
                "1 mark for highlighting how this bypasses traditional legacy rule-based compliance systems.",
                "1 mark for suggesting modern AI/behavioral monitoring countermeasures."
            ],
            "keywords": ["money laundering", "service", "infrastructure", "compliance", "syndicate"],
            "explanation": "MLaaS shifts financial crime from isolated events to highly scaleable, platform-style criminal operations."
        }
    ]

    # Dynamically load pre-generated quiz questions
    questions_path = Path("data/generated/quiz_questions.json")
    loaded_mcqs = []
    loaded_lf = []

    if questions_path.is_file():
        try:
            with open(questions_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                loaded_mcqs = data.get("mcq", [])
                loaded_lf = data.get("long_form", [])
        except Exception as e:
            print(f"Warning loading quiz_questions.json: {e}")

    # Use pre-generated questions if available; otherwise use robust fallbacks
    mcqs = loaded_mcqs if loaded_mcqs else FALLBACK_MCQS
    lf_questions = loaded_lf if loaded_lf else FALLBACK_LONG_FORM
    return lf_questions, mcqs


@app.cell
def _(OpenAI, json, render_prompt):
    # Live Judge AI grading logic
    def run_live_judge(question: str, ideal_response: str, mark_scheme: list[str], keywords: list[str], user_answer: str) -> dict:
        """Invokes OpenAI with JSON output mode to grade candidate long-form responses against a 5-point rubric."""
        client = OpenAI()

        prompt = render_prompt(
            "live_judge.jinja",
            question=question,
            ideal_response=ideal_response,
            mark_scheme=mark_scheme,
            keywords=keywords,
            user_answer=user_answer,
            max_marks=len(mark_scheme)
        )

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            # Safe grading fallback if key is missing or API errors
            return {
                "score": 0.60,
                "marks_awarded": 3,
                "reasoning": f"Live grading unavailable or encountered an error ({e}). Defaulted to offline baseline score."
            }

    return (run_live_judge,)


@app.cell
def _(state):
    def generate_score_message() -> str:
        if state.is_expert_mode:
            max_possible = state.total_questions * 5
            percentage = (state.score / max_possible) * 100
        else:
            percentage = (state.score / state.total_questions) * 100

        if percentage >= 80:
            feedback = "Compliance Mastery! 🏆🌟"
        elif percentage >= 50:
            feedback = "Solid Compliance Officer! 💼👍"
        else:
            feedback = "Needs Remedial Training! 📚🚨"
        return feedback

    return (generate_score_message,)


@app.cell
def _(state):
    def get_hover_text(row, column, value):
        row_idx = int(row)
        q = state.question_list[row_idx]

        if not state.is_expert_mode:
            if column == "Result":
                correct_ans = q.get("correct")
                if not state.answer_history[row_idx]:
                    return f"Incorrect. Correct option: {correct_ans}"
                else:
                    return f"Correct! 👍: {correct_ans}"
        else:
            if column == "Marks":
                grading = state.grading_results[row_idx]
                if grading:
                    return f"Feedback: {grading['reasoning'][:120]}..."
        return ""

    return (get_hover_text,)


@app.cell
def _(generate_score_message, get_hover_text, mo, state):
    def generate_final_visual():
        feedback_text = generate_score_message()

        # Build appropriate results table depending on MCQ vs. Expert Mode
        if not state.is_expert_mode:
            results_table = [
                {
                    "Q#": i+1, 
                    "Result": "✅" if pass_status else "❌", 
                    "Question": q["question"]
                } 
                for i, (q, pass_status) in enumerate(zip(state.question_list, state.answer_history))
            ]
            final_score_str = f"Final Score: {state.score} / {state.total_questions}"
        else:
            results_table = []
            for i, (q, pass_status, grading) in enumerate(zip(state.question_list, state.answer_history, state.grading_results)):
                marks_awarded = grading.get("marks_awarded", 0) if grading else 0
                max_marks = len(q.get("mark_scheme", []))
                results_table.append({
                    "Q#": i+1,
                    "Marks": f"{marks_awarded} / {max_marks}",
                    "Status": "Passed ✅" if pass_status else "Needs Work ❌",
                    "Question": q["question"]
                })
            max_possible = state.total_questions * 5
            final_score_str = f"Total Marks Awarded: {state.score} / {max_possible} ({ (state.score / max_possible)*100:.1f}%)"

        final_score_visual = mo.vstack([
            mo.md(f"# {feedback_text}"),
            mo.md(f"## {final_score_str}"),
            mo.md("Hover over cells for detailed feedback snippet and corrections."),
            mo.ui.table(
                results_table,
                pagination=False,
                selection=None,
                wrapped_columns=["Question"],
                hover_template=get_hover_text
            )
        ])
        return final_score_visual

    return (generate_final_visual,)


@app.cell
def _(mo):
    # Interactive compliance header
    mo.md(r"""
    # 🏛️ Financial Crime Interactive Quizzer
    *Powered by Semantic parsing with IBM Docling, DeepEval synthesis, and Live Judge AI evaluations.*
    """)
    return


@app.cell
def _(mo):
    # Mode selector
    mode_select = mo.ui.radio(
        options={"mcq": "Easy Mode (MCQs)", "expert": "Expert Mode (Long-Form Essay + Live Rubric Grading)"},
        value="mcq",
        label="Select Quiz Difficulty Mode:"
    )

    welcome_card = mo.md(f"""
    ### Welcome to the State of Financial Crime Quiz
    Test your mastery of the latest global compliance guides, scam centers, MLaaS syndicates, and regulatory frameworks.

    {mode_select}
    """).callout(kind="info")
    return mode_select, welcome_card


@app.cell
def _(mo):
    get_state, set_state = mo.state(None)
    get_active_citation, set_active_citation = mo.state(None)
    return get_active_citation, get_state, set_active_citation, set_state


@app.cell
def _(get_active_citation):
    active_citation = get_active_citation()
    return (active_citation,)


@app.cell
def _(QuizState, get_state, lf_questions, mcqs, mode_select, set_state):
    state = get_state()

    def start_quiz(_):
        is_expert = (mode_select.value == "expert")
        questions = lf_questions if is_expert else mcqs
        set_state(QuizState(question_list=questions, is_expert_mode=is_expert))

    return start_quiz, state


@app.cell
def _(
    active_citation,
    generate_final_visual,
    mo,
    mo_data,
    Path,
    run_live_judge,
    set_active_citation,
    set_state,
    start_quiz,
    state,
    welcome_card,
):
    # Start quiz action button
    quiz_start = mo.ui.button(
        label="Start Quiz Dashboard 🚀",
        on_click=start_quiz
    )

    if state is None:
        display_content = mo.vstack([welcome_card, quiz_start])
    elif state.is_finished:
        reset_btn = mo.ui.button(
            label="Restart Quiz 🔄",
            on_click=lambda _: set_state(None)
        )
        display_content = mo.vstack([generate_final_visual(), reset_btn])
    else:
        q_idx = state.current_question_index
        current_q = state.question_list[q_idx]

        # Define the Show Evidence button so it can be embedded in explanation panels
        evidence_btn = mo.ui.button(
            label="Show Evidence 📖",
            on_click=lambda _: set_active_citation(current_q)
        )

        # -------------------------------------------------------------
        # MCQ Mode Visuals
        # -------------------------------------------------------------
        if not state.is_expert_mode:
            original_options = current_q["options"]
            options_dict = {label: label for label in original_options}

            answer_input = mo.ui.radio(
                options=options_dict,
                label=f"**Question {q_idx + 1} of {state.total_questions}**\n\n{current_q['question']}",
                value=state.selected_answer,
                on_change=lambda val: state.select_answer(val) or set_state(state),
                disabled=state.is_submitted
            )

            if state.is_submitted:
                text = current_q.get("explanation", "No explanation provided.")
                explanation_box = mo.vstack([
                    mo.md(f"**Correct Answer**: {current_q['correct']}\n\n**Explanation:**\n{text}"),
                    evidence_btn
                ], gap=1).callout(kind="info")
            else:
                explanation_box = mo.md("")

            callout_kind = "neutral"
            if state.is_submitted:
                callout_kind = "success" if state.selected_answer == current_q["correct"] else "danger"

            quiz_panel = mo.hstack([
                answer_input.callout(kind=callout_kind),
                explanation_box
            ] if explanation_box else [answer_input], align="start", gap=2)

        # -------------------------------------------------------------
        # Expert Mode Visuals (Long-Form Free Text)
        # -------------------------------------------------------------
        else:
            answer_input = mo.ui.text_area(
                label=f"**Question {q_idx + 1} of {state.total_questions}**\n\n{current_q['question']}",
                value=state.selected_answer or "",
                placeholder="Type your comprehensive written response here. (Reference MLaaS, syndicates, scale, or compliance implications where relevant)...",
                on_change=lambda val: state.select_answer(val) or set_state(state),
                disabled=state.is_submitted,
                rows=7
            )

            if state.is_submitted:
                grading = state.grading_results[q_idx]
                if grading:
                    points_list = "\n".join([f"- {p}" for p in current_q.get("mark_scheme", [])])
                    keywords_str = ", ".join([f"`{k}`" for k in current_q.get("keywords", [])])
                    
                    explanation_box = mo.vstack([
                        mo.md(f"""### ⚖️ Live Judge Evaluation
    **Marks Awarded**: `{grading['marks_awarded']} / {len(current_q['mark_scheme'])}` (Relevance Score: `{grading['score']:.2f}`)

    **Grading Rationale & Rubric Breakdown**:
    {grading['reasoning']}

    ---
    #### 🗺️ Ideal Model Answer
    > {current_q['ideal_response']}

    #### 📌 Reference Mark Scheme Rubric:
    {points_list}

    **Expected Keywords**: {keywords_str}
    """),
                        evidence_btn
                    ], gap=1).callout(kind="success" if grading['marks_awarded'] >= 3 else "danger")
                else:
                    explanation_box = mo.vstack([
                        mo.md("⌛ *AI Live Judge grading in progress...*"),
                        evidence_btn
                    ], gap=1)
            else:
                explanation_box = mo.md("")

            callout_kind = "success" if (state.is_submitted and state.answer_history[q_idx]) else ("danger" if state.is_submitted else "neutral")

            quiz_panel = mo.vstack([
                answer_input.callout(kind=callout_kind),
                explanation_box
            ], gap=2)

        # -------------------------------------------------------------
        # Navigation & Submit Button Orchestration
        # -------------------------------------------------------------
        def submit_and_grade(_):
            state.submit_answer()
            set_state(state) # Trigger loading state immediately

            if state.is_expert_mode:
                # Grade the free text candidate answer using the Live Judge
                eval_res = run_live_judge(
                    question=current_q["question"],
                    ideal_response=current_q["ideal_response"],
                    mark_scheme=current_q["mark_scheme"],
                    keywords=current_q["keywords"],
                    user_answer=state.selected_answer
                )
                state.set_grading_result(
                    score=eval_res["score"],
                    reasoning=eval_res["reasoning"],
                    marks_awarded=eval_res["marks_awarded"]
                )
                set_state(state)

        submit_btn = mo.ui.button(
            label="Submit Answer 📤",
            on_click=submit_and_grade,
            disabled=state.is_submitted or state.selected_answer is None or not state.selected_answer.strip()
        )

        is_last = state.current_question_index == state.total_questions - 1
        next_btn = mo.ui.button(
            label="Reveal Final Results 📊" if is_last else "Next Question ➡️",
            on_click=lambda _: state.next_question() or set_state(state)
        )

        button_panel = mo.hstack(
            [submit_btn, next_btn] if state.is_submitted else [submit_btn],
            justify="start",
            gap=2
        )

        # Build modal overlay if active
        print("[main.py debug] active_citation is:", active_citation)
        modal_overlay = None
        if active_citation is not None:
            ref = active_citation.get("reference", {})
            pages_list = ref.get("page_numbers", [])
            page_no = pages_list[0] if pages_list else 1
            section_str = ref.get("section", "General")
            snippet_str = ref.get("source_snippet", "")
            
            # Load PDF to correct page
            pdf_path = Path("data/documents/SoFC26_Guide.pdf")
            pdf_url = mo_data.pdf(pdf_path.read_bytes()).url
            pdf_url += f"#page={page_no}&view=FitV"
            
            pdf_viewer = mo.pdf(
                src=pdf_url,
                width="100%",
                height="50vh"
            )
            
            close_btn = mo.ui.button(
                label="Close ✕",
                on_click=lambda _: set_active_citation(None)
            )
            
            modal_body = mo.vstack([
                mo.hstack([
                    mo.md(f"### 📖 Source Reference: Page {pages_list} (Section: *{section_str}*)"),
                    close_btn
                ], justify="space-between", align="center"),
                mo.md("*Double click or scroll inside the viewer to zoom/pan the PDF.*"),
                pdf_viewer,
                mo.accordion({
                    "📄 View Markdown Text Snippet": mo.md(f"""
                    ```markdown
                    {snippet_str}
                    ```
                    """)
                })
            ], gap=1).style({
                "background": "#0d1117",
                "border": "1px solid rgba(240, 246, 252, 0.15)",
                "border-radius": "16px",
                "padding": "24px",
                "width": "100%",
                "max-width": "900px",
                "max-height": "85vh",
                "box-shadow": "0 20px 40px rgba(0,0,0,0.6)",
                "overflow-y": "auto",
                "color": "#e6edf3"
            })
            
            modal_overlay = mo.vstack([
                modal_body
            ], align="center", justify="center").style({
                "position": "fixed",
                "top": "0",
                "left": "0",
                "width": "100vw",
                "height": "100vh",
                "background": "rgba(10, 12, 16, 0.75)",
                "backdrop-filter": "blur(8px)",
                "z-index": "9999",
                "display": "flex",
                "align-items": "center",
                "justify-content": "center"
            })

        display_content = mo.vstack([
            quiz_panel,
            button_panel
        ], gap=2)

        if modal_overlay is not None:
            display_content = mo.vstack([
                display_content,
                modal_overlay
            ])

    display_content
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
