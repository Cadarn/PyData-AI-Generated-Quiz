import sys
import argparse
from pathlib import Path

# Add project root to path to avoid ModuleNotFoundError when running directly
sys.path.append(str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv
from ai_quizzer.question_generator import QuestionGenerator

def main():
    # 1. Load environment variables from .env
    load_dotenv()
    
    # 2. Parse command line arguments
    parser = argparse.ArgumentParser(description="Pre-generate synthetic MCQ and Long-Form quiz questions using DeepEval and OpenAI.")
    parser.add_argument(
        "--pdf",
        type=str,
        default="data/documents/SoFC26_Guide.pdf",
        help="Path to the PDF document to parse and generate quiz questions from."
    )
    parser.add_argument(
        "--config",
        type=str,
        default="quiz_config.yaml",
        help="Path to the quiz_config.yaml configuration file."
    )
    parser.add_argument(
        "--mcqs",
        type=int,
        default=None,
        help="Override the number of MCQ questions to generate."
    )
    parser.add_argument(
        "--lf",
        type=int,
        default=None,
        help="Override the number of Long-Form questions to generate."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Override the output path for the generated questions JSON (default: from config)."
    )

    args = parser.parse_args()
    pdf_path = Path(args.pdf)
    config_path = Path(args.config)
    
    if not pdf_path.is_file():
        print(f"Error: PDF document not found at: {pdf_path}")
        print("Please place the source PDF in data/documents/ or specify the path with --pdf.")
        return
        
    if not config_path.is_file():
        print(f"Error: Config file not found at: {config_path}")
        return
        
    print("=" * 60)
    print("🚀 Starting structured Quiz Generation Engine")
    print(f"   Source PDF: {pdf_path}")
    print(f"   Config:     {config_path}")
    print("=" * 60)
    
    try:
        # Initialize generator
        generator = QuestionGenerator(config_path=config_path)
        if args.output:
            generator.output_path = Path(args.output)

        # Run generation
        generator.generate_quiz(
            pdf_path=pdf_path,
            num_mcq=args.mcqs,
            num_lf=args.lf
        )
        print("\n🎉 Quiz generation completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during quiz generation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
