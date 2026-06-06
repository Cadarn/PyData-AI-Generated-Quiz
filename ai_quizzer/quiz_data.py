import json
import random
import yaml
from pathlib import Path

FALLBACK_MCQS = [
    {
        "question": "In Marimo's reactive notebook model, what mechanism determines which cells re-execute when a variable changes?",
        "options": [
            "Static analysis of cell input and output variable names",
            "A runtime event loop that monitors all variable assignments",
            "Manual dependency declarations using a decorator",
            "Alphabetical ordering of cell execution",
        ],
        "correct": "Static analysis of cell input and output variable names",
        "explanation": (
            "Marimo builds a dataflow graph by statically analysing each cell's function signature. "
            "A cell re-runs only when one of the variables it explicitly receives as an argument changes — "
            "runtime calls inside the cell body are invisible to the reactive engine."
        ),
    },
    {
        "question": "When building a RAG pipeline over a structured PDF document, which chunking strategy typically produces the highest-quality retrieval context?",
        "options": [
            "Structure-aware chunking that respects document headings and sections",
            "Fixed-size character chunking with a 512-character window",
            "Sentence-level splitting using a rules-based tokeniser",
            "Whole-page chunking that treats each PDF page as one unit",
        ],
        "correct": "Structure-aware chunking that respects document headings and sections",
        "explanation": (
            "Structure-aware chunking uses the document's own heading hierarchy as the semantic boundary signal. "
            "This keeps tables, bullet lists, and paragraphs together under their logical section, eliminating "
            "the fragmented context that character-count splits produce."
        ),
    },
    {
        "question": "When using an LLM as a judge to evaluate free-text answers, which rubric design produces the most consistent and auditable scores?",
        "options": [
            "One criterion per mark, each describing a single specific concept",
            "A single holistic quality score from 1 to 10",
            "Binary pass/fail based on keyword presence",
            "Multiple weighted criteria summed to a percentage",
        ],
        "correct": "One criterion per mark, each describing a single specific concept",
        "explanation": (
            "Breaking a rubric into discrete single-mark criteria forces the LLM judge to make a binary "
            "decision per concept rather than a holistic judgement. This produces structured, auditable, "
            "and consistent grading with natural language rationale per criterion."
        ),
    },
]

FALLBACK_LONG_FORM = [
    {
        "question": (
            "Describe the three core stages of a Retrieval-Augmented Generation (RAG) pipeline "
            "and explain how the quality of each stage affects the accuracy and trustworthiness of the final output."
        ),
        "ideal_response": (
            "A RAG pipeline has three core stages. "
            "First, indexing: source documents are parsed, chunked into semantically coherent units, and embedded "
            "into a vector store. The quality of chunking — whether it respects document structure or uses naive "
            "character splitting — directly determines whether the retrieved context is coherent. "
            "Second, retrieval: at query time, the user's question is embedded and the most semantically similar "
            "chunks are retrieved from the vector store. Retrieval quality depends on embedding model choice, "
            "chunk size, and similarity metric. Poor retrieval returns irrelevant context, causing the generator "
            "to hallucinate or produce off-topic answers. "
            "Third, generation: the retrieved chunks are injected into an LLM prompt alongside the original question. "
            "The LLM synthesises an answer grounded in the retrieved evidence. If the retrieved context is accurate "
            "and relevant, the generator can produce a factual, cited response; if the context is poor, even a "
            "capable LLM cannot compensate."
        ),
        "mark_scheme": [
            "1 mark for correctly identifying and naming all three stages: indexing, retrieval, and generation.",
            "1 mark for explaining that chunking strategy during indexing determines context coherence.",
            "1 mark for explaining that retrieval quality depends on embedding similarity and affects what context the LLM receives.",
            "1 mark for explaining that the generator is grounded by the retrieved context and cannot compensate for poor retrieval.",
            "1 mark for discussing a specific failure mode or quality trade-off across any stage (e.g. chunk size, embedding drift, hallucination from missing context).",
        ],
        "keywords": ["indexing", "retrieval", "generation", "embeddings", "context", "chunking"],
        "explanation": (
            "RAG grounds LLM generation in external knowledge, reducing hallucination. "
            "Each stage introduces its own quality ceiling: a weak parser or chunker at indexing time limits "
            "everything downstream, regardless of how powerful the retrieval or generation models are."
        ),
    },
]


def load_quiz_questions(
    questions_path: str | Path = "data/generated/quiz_questions.json",
    mcq_count: int | None = None,
    lf_count: int | None = None,
) -> tuple[list[dict], list[dict]]:
    """Load MCQ and long-form questions, falling back to defaults if the file is missing or empty.

    If mcq_count or lf_count are given, a reproducible random sample (seed=42) of that size is
    returned rather than the full set.
    """
    questions_path = Path(questions_path)
    mcqs: list[dict] = []
    lf_questions: list[dict] = []

    if questions_path.is_file():
        try:
            with open(questions_path, encoding="utf-8") as f:
                data = json.load(f)
                mcqs = data.get("mcq", [])
                lf_questions = data.get("long_form", [])
        except Exception as e:
            print(f"Warning: could not load {questions_path}: {e}")

    mcqs = mcqs or FALLBACK_MCQS
    lf_questions = lf_questions or FALLBACK_LONG_FORM

    rng = random.Random(42)
    if mcq_count is not None and mcq_count < len(mcqs):
        mcqs = rng.sample(mcqs, mcq_count)
    if lf_count is not None and lf_count < len(lf_questions):
        lf_questions = rng.sample(lf_questions, lf_count)

    return mcqs, lf_questions


def load_config(config_path: str | Path = "quiz_config.yaml") -> dict:
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)
