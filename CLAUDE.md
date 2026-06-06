# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**rag-quizzer** transforms dense PDF documents into interactive quizzes using a RAG pipeline. It parses PDFs with IBM Docling, generates MCQ and long-form questions via DeepEval's Synthesizer, and presents a reactive Marimo-based UI with live semantic grading.

## Commands

```bash
# Install dependencies
uv sync

# Run the interactive app (editable Marimo notebook)
marimo edit main.py

# Run the app as a static server
marimo run main.py

# Generate quiz questions from a PDF
python scripts/generate_quiz.py [--pdf <path>] [--config quiz_config.yaml] [--mcqs <n>] [--lf <n>]

# Run all tests
./.venv/bin/pytest

# Run a single test file
./.venv/bin/pytest tests/test_pdf_parser.py

# Run with coverage
./.venv/bin/pytest --cov=ai_quizzer
```

No linting or type-checking toolchain is currently configured.

## Architecture

The system has three major phases, with Phase 3 (RAG evidence retrieval via Chroma) still planned:

```
PDF → PDFParser (Docling) → semantic chunks with page/header metadata
    → QuestionGenerator (DeepEval Synthesizer) → raw QA pairs
    → Jinja2 post-processing prompts → structured MCQ/LF JSON (quiz_questions.json)
    → Marimo UI (main.py) → user interaction + live grading → results
```

### Core Modules (`ai_quizzer/`)

- **`pdf_parser.py`** — `PDFParser` class wraps IBM Docling for OCR-enabled PDF-to-Markdown conversion. Outputs metadata-rich chunks including page numbers, headers, and element types. These coordinates flow through to questions for evidence retrieval.
- **`question_generator.py`** — `QuestionGenerator` orchestrates DeepEval's Synthesizer, then calls the Jinja2 templates to post-process raw pairs into schema-compliant MCQ/long-form JSON. Each question carries a `reference` field with `page_numbers` and `header` for i-RAG evidence popups.
- **`quiz_logic.py`** — `QuizState` dataclass manages session state: current question index, user answers, score, and grading feedback. MCQ checking is synchronous; long-form answers are buffered for the DeepEval live judge.
- **`prompts/`** — Jinja2 templates for prompt engineering. `loader.py` sets up the Jinja2 environment. Style guide rules (British English, conciseness) are shared across templates via `style_guide.jinja`.

### Frontend (`main.py`)

A 600+ line Marimo reactive notebook. UI state flows through a `QuizState` instance shared across cells. Heavy CSS injection at the top of the file implements the glassmorphic dashboard design. Two modes:
- **Easy** — MCQ with immediate correctness feedback
- **Expert** — Free-text graded asynchronously via `AnswerRelevancyMetric` from DeepEval and an OpenAI-backed live judge prompt

The i-RAG popup modal opens the source PDF to the exact page cited in the question's `reference` field.

### Configuration

`quiz_config.yaml` drives quiz generation parameters (model name, MCQ count, long-form question count, marks). This is the intended entry point for non-code configuration changes.

Environment variables (`OPENAI_API_KEY`, model name) are loaded from `.env`.

## Key Libraries

| Library | Role |
|---|---|
| IBM Docling | PDF parsing, OCR, table/layout recognition |
| DeepEval | Synthetic QA generation (`Synthesizer`), semantic evaluation metrics |
| Marimo | Reactive notebook frontend |
| OpenAI SDK | LLM calls (default: `gpt-4o-mini`) |
| Jinja2 | Prompt template rendering |
| Chroma | Vector DB (planned for Phase 3 RAG) |

## Non-Obvious Patterns

- **i-RAG metadata is first-class**: `PDFParser` preserves exact page and header context per chunk. `QuestionGenerator` maps these coordinates onto every generated question so the UI can open the source PDF to the evidence page.
- **Marimo is not a traditional web framework**: reactive cells replace request/response cycles. Treat `main.py` as a stateful notebook, not a Flask app.
- **`conductor/`** is the internal knowledge base (product decisions, tech stack rationale, Linear task tracking) — not a build tool. Check `conductor/product.md` and `conductor/tech-stack.md` for design decisions.
- **Python 3.14** is required; `uv` manages the `.venv/` virtual environment.
