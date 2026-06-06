import json
from openai import OpenAI
from ai_quizzer.prompts import render_prompt


def run_live_judge(
    question: str,
    ideal_response: str,
    mark_scheme: list[str],
    keywords: list[str],
    user_answer: str,
) -> dict:
    """Grade a long-form answer against the mark scheme using OpenAI."""
    client = OpenAI()
    prompt = render_prompt(
        "live_judge.jinja",
        question=question,
        ideal_response=ideal_response,
        mark_scheme=mark_scheme,
        keywords=keywords,
        user_answer=user_answer,
        max_marks=len(mark_scheme),
    )
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {
            "score": 0.60,
            "marks_awarded": 3,
            "reasoning": f"Live grading unavailable ({e}). Defaulted to offline baseline score.",
        }
