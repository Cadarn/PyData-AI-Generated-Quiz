import sys
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

def main():
    load_dotenv()
    
    questions_path = Path("data/generated/quiz_questions.json")
    if not questions_path.is_file():
        print(f"Error: Pre-generated questions file not found at: {questions_path}")
        print("Please run scripts/generate_quiz.py first.")
        return
        
    print("=" * 60)
    print("🇬🇧 Running British English Quiz Localizer...")
    print(f"   Target File: {questions_path}")
    print("=" * 60)
    
    try:
        # Load existing JSON questions
        with open(questions_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
            
        print("Existing quiz data loaded. Localizing all spelling variations...")
        
        # Invoke OpenAI with JSON mode
        client = OpenAI()
        
        prompt = f"""You are an expert editor specializing in British English and compliance.
Your task is to take the following JSON object representing generated quiz questions, and translate all American English spellings to British English.

SPELLING RULES:
- Use British English spellings throughout (e.g. 'industrialisation', 'organisation', 'syndicates', 'behaviour', 'programme', 'minimise', 'analysed', 'laundering', 'industrialised').
- NEVER use American spellings (e.g. 'industrialization', 'organization', 'behavior', 'program', 'minimize', 'analyzed', 'industrialized').
- Change nothing else: do NOT summarize, do NOT rewrite the questions or options, and do NOT alter the JSON structure, keys, or correct answers. Just perform spelling localization.

INPUT JSON:
{json.dumps(raw_data, indent=2)}
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.0 # Absolute determinism
        )
        
        localized_data = json.loads(response.choices[0].message.content)
        
        # Save back to file
        with open(questions_path, "w", encoding="utf-8") as f:
            json.dump(localized_data, f, indent=2, ensure_ascii=False)
            
        print("🎉 Successfully localized all questions to British English!")
        print("   Saved back to data/generated/quiz_questions.json")
        
    except Exception as e:
        print(f"❌ Error during localization: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
