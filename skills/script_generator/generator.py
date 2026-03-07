# generator.py — Agente Gemini que gera roteiros

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

from skills.script_generator.prompts import SYSTEM_PROMPT, build_generation_prompt

_ENV_PATH = Path(__file__).parents[2] / "skills" / "secrets" / ".env"
_CONTEXT_DIR = Path(__file__).parent / "context"


def load_references() -> dict[str, str]:
    """Load all reference JSON files from the context directory.

    Returns:
        Dict mapping theme name to ssml_content string.
    """
    references: dict[str, str] = {}
    for json_file in sorted(_CONTEXT_DIR.glob("*.json")):
        with open(json_file, encoding="utf-8") as f:
            data = json.load(f)
        references[json_file.stem] = data.get("ssml_content", "")
    return references


def generate(tema: str) -> list[str]:
    """Generate 3 distinct scripts for the given theme using Gemini API.

    Makes 3 separate API calls, one per style (emotional, informative, controversial).

    Args:
        tema: The video theme/briefing.

    Returns:
        List of 3 script strings.
    """
    load_dotenv(dotenv_path=_ENV_PATH)
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment. Check skills/secrets/.env")

    client = genai.Client(api_key=api_key)
    references = load_references()
    print(f"[script_generator] {len(references)} reference(s) loaded.")

    scripts: list[str] = []
    for i in range(1, 4):
        prompt = build_generation_prompt(tema, references, i)
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.7,
                ),
            )
            script = response.text.strip()
            scripts.append(script)
            print(f"[script_generator] Script {i}/3 generated ({len(script.split())} words).")
        except Exception as e:
            print(f"[script_generator] Error generating script {i}: {e}")
            raise

    return scripts
