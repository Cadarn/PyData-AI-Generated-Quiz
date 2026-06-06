import yaml
import json
import random
from pathlib import Path
from openai import OpenAI
from deepeval.synthesizer import Synthesizer
from ai_quizzer.pdf_parser import PDFParser
from ai_quizzer.prompts import render_prompt

class QuestionGenerator:
    def __init__(self, config_path: str | Path = "quiz_config.yaml"):
        self.config_path = Path(config_path)
        self.load_config()
        # Initialize OpenAI client (loads API key automatically from environment)
        self.client = OpenAI()

    def load_config(self):
        """Loads configuration from yaml file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found at: {self.config_path}")
        
        with open(self.config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
            
        # Extract configurations with reasonable defaults
        self.model_name = self.config.get("model_name", "gpt-4o-mini")
        self.output_path = Path(self.config.get("output_path", "data/generated/quiz_questions.json"))
        
        question_types = self.config.get("question_types", {})
        self.mcq_config = question_types.get("mcq", {"count": 5, "distractor_count": 3})
        self.lf_config = question_types.get("long_form", {
            "count": 3,
            "max_marks": 5,
            "target_length_min": 50,
            "target_length_max": 200,
            "rubric_detail": "detailed"
        })

    def generate_quiz(self, pdf_path: str | Path, num_mcq: int = None, num_lf: int = None) -> dict:
        """
        Parses the PDF retaining rich metadata, runs DeepEval Synthesizer,
        maps QA pairs back to source metadata chunks, and outputs schema-compliant i-RAG quizzes.
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.is_file():
            raise FileNotFoundError(f"PDF document not found at: {pdf_path}")
            
        mcq_count = num_mcq if num_mcq is not None else self.mcq_config.get("count", 5)
        lf_count = num_lf if num_lf is not None else self.lf_config.get("count", 3)
        total_questions = mcq_count + lf_count
        
        if total_questions == 0:
            return {"mcq": [], "long_form": []}
            
        print(f"1. Extracting semantic metadata-rich chunks from {pdf_path.name}...")
        parser = PDFParser()
        chunks = parser.get_semantic_chunks(pdf_path)
        
        if not chunks:
            raise ValueError("No semantic chunks could be extracted from the PDF.")
            
        print(f"Found {len(chunks)} chunks. Selecting {total_questions} chunks for question generation.")
        
        # Distribute selection evenly
        selected_chunks = []
        if len(chunks) <= total_questions:
            selected_chunks = chunks * (total_questions // len(chunks) + 1)
            selected_chunks = selected_chunks[:total_questions]
        else:
            step = len(chunks) / total_questions
            selected_chunks = [chunks[int(i * step)] for i in range(total_questions)]
            
        # Prepare contexts for deepeval
        contexts = [[chunk["text"]] for chunk in selected_chunks]
        
        print(f"2. Launching DeepEval Synthesizer (Model: {self.model_name}) to generate {total_questions} QA pairs...")
        synthesizer = Synthesizer(model=self.model_name)
        
        raw_goldens = synthesizer.generate_goldens_from_contexts(
            contexts=contexts,
            include_expected_output=True,
            max_goldens_per_context=1
        )
        
        if not raw_goldens:
            raise RuntimeError("DeepEval Synthesizer failed to generate raw QA pairs.")
            
        print(f"Successfully generated {len(raw_goldens)} raw QA pairs. Mapping back to coordinate sources...")

        # Split raw goldens into MCQ and Long-Form groups
        raw_mcq_goldens = raw_goldens[:mcq_count]
        raw_lf_goldens = raw_goldens[mcq_count:mcq_count + lf_count]
        
        processed_mcqs = []
        processed_lf = []
        
        # 3. Post-process MCQ Questions (i-RAG mapping)
        if raw_mcq_goldens:
            print(f"3. Refining MCQ Questions with location-first coordinates...")
            for idx, golden in enumerate(raw_mcq_goldens):
                context_str = "\n".join(golden.context) if golden.context else ""
                
                # Search back to find matching metadata chunk
                source_chunk = next((c for c in selected_chunks if c["text"] == context_str), selected_chunks[0])
                
                # Generate structured MCQ with citations
                mcq = self._post_process_mcq(golden.input, golden.expected_output, source_chunk)
                processed_mcqs.append(mcq)
                page_numbers = mcq.get("reference", {}).get("page_numbers", [])
                print(f"   [{idx+1}/{len(raw_mcq_goldens)}] MCQ Generated (Page {page_numbers}): {mcq['question'][:50]}...")
                
        # 4. Post-process Long-Form Questions (i-RAG mapping)
        if raw_lf_goldens:
            print(f"4. Refining Expert Long-Form Questions with location-first coordinates...")
            for idx, golden in enumerate(raw_lf_goldens):
                context_str = "\n".join(golden.context) if golden.context else ""
                
                # Search back to find matching metadata chunk
                source_chunk = next((c for c in selected_chunks if c["text"] == context_str), selected_chunks[0])
                
                # Generate structured Essay with citations
                lf = self._post_process_long_form(golden.input, golden.expected_output, source_chunk)
                processed_lf.append(lf)
                page_numbers = lf.get("reference", {}).get("page_numbers", [])
                print(f"   [{idx+1}/{len(raw_lf_goldens)}] Long-Form Generated (Page {page_numbers}): {lf['question'][:50]}...")
                
        quiz_data = {
            "mcq": processed_mcqs,
            "long_form": processed_lf
        }
        
        # Save to output file
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_path, "w", encoding="utf-8") as f:
            json.dump(quiz_data, f, indent=2, ensure_ascii=False)
            
        print(f"5. i-RAG Quiz data saved successfully to {self.output_path}")
        return quiz_data

    def _post_process_mcq(self, question: str, correct_answer: str, chunk: dict | str) -> dict:
        """Refines MCQ and injects location coordinates into the JSON Schema."""
        if isinstance(chunk, str):
            chunk = {
                "text": chunk,
                "page_numbers": [1],
                "header": "General",
                "element_types": ["paragraph"],
                "source_snippet": chunk
            }

        prompt = render_prompt(
            "mcq_post_process.jinja",
            context=chunk["text"],
            question=question,
            correct_answer=correct_answer,
            page_no=str(chunk["page_numbers"]),
            header=chunk["header"]
        )

        # Build structured fallback
        fallback_ref = {
            "page_numbers": chunk["page_numbers"],
            "section": chunk["header"],
            "element_types": chunk["element_types"],
            "source_snippet": chunk["source_snippet"]
        }

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.4
            )
            result = json.loads(response.choices[0].message.content)
            result["reference"] = fallback_ref
            return result
        except Exception as e:
            print(f"Error post-processing MCQ: {e}")
            
        options = [correct_answer, "Option B (Incorrect)", "Option C (Incorrect)", "Option D (Incorrect)"]
        random.shuffle(options)
        return {
            "question": question,
            "options": options,
            "correct": correct_answer,
            "explanation": f"The correct answer is: {correct_answer}. (Refer to Page {chunk['page_numbers']} under Section: '{chunk['header']}'). [Fallback due to post-processing error]",
            "reference": fallback_ref
        }

    def _post_process_long_form(self, question: str, correct_answer: str, chunk: dict | str) -> dict:
        """Refines Essay question and injects location coordinates into the JSON Schema."""
        if isinstance(chunk, str):
            chunk = {
                "text": chunk,
                "page_numbers": [1],
                "header": "General",
                "element_types": ["paragraph"],
                "source_snippet": chunk
            }

        max_marks = self.lf_config.get("max_marks", 5)
        min_words = self.lf_config.get("target_length_min", 50)
        max_words = self.lf_config.get("target_length_max", 200)
        
        prompt = render_prompt(
            "long_form_post_process.jinja",
            context=chunk["text"],
            question=question,
            correct_answer=correct_answer,
            min_words=min_words,
            max_words=max_words,
            max_marks=max_marks,
            page_no=str(chunk["page_numbers"]),
            header=chunk["header"]
        )

        fallback_ref = {
            "page_numbers": chunk["page_numbers"],
            "section": chunk["header"],
            "element_types": chunk["element_types"],
            "source_snippet": chunk["source_snippet"]
        }

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.4
            )
            result = json.loads(response.choices[0].message.content)
            result["reference"] = fallback_ref
            return result
        except Exception as e:
            print(f"Error post-processing Long-Form: {e}")
            
        return {
            "question": question,
            "ideal_response": correct_answer,
            "mark_scheme": [f"1 mark for each logical portion of: {correct_answer[:60]}..."] * max_marks,
            "keywords": [word.lower() for word in question.split() if len(word) > 5][:4],
            "explanation": f"Please ensure your answer aligns with the compliance concepts on Page {chunk['page_numbers']} under Section '{chunk['header']}'. [Fallback due to post-processing error]",
            "reference": fallback_ref
        }
