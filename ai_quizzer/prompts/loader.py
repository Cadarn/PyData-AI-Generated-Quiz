from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Locate prompts directory
PROMPTS_DIR = Path(__file__).resolve().parent

# Initialize Jinja2 environment loading from the local prompts dir
env = Environment(
    loader=FileSystemLoader(PROMPTS_DIR),
    autoescape=select_autoescape()
)

def render_prompt(template_name: str, **kwargs) -> str:
    """
    Loads a Jinja2 template from the prompts directory and renders it 
    with the provided context variables.
    """
    template = env.get_template(template_name)
    return template.render(**kwargs)
