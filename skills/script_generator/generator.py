# generator.py — Agente Gemini que gera roteiros

import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

from skills.script_generator.prompts import SYSTEM_PROMPT, build_generation_prompt

_ENV_PATH = Path(__file__).parents[2] / "skills" / "secrets" / ".env"
_CONTEXT_DIR = Path(__file__).parent / "context"

DEFAULT_VOICE_CONFIG = {
    "language": "en-US",
    "voice_type": "en-US-Journey-D",
    "speed": 1.0,
    "pitch": -1.0,
}


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


def _clean_ssml_response(text: str) -> str:
    """Clean model response to extract raw SSML content.

    Strips markdown code fences and surrounding whitespace.

    Args:
        text: Raw model response text.

    Returns:
        Clean SSML string starting with <speak> and ending with </speak>.
    """
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    return text


def _count_words_without_ssml(ssml: str) -> int:
    """Count words in SSML content, ignoring tags.

    Args:
        ssml: SSML-formatted string.

    Returns:
        Word count of the text content only.
    """
    clean = re.sub(r"<[^>]+>", " ", ssml)
    return len(clean.split())


def generate(tema: str) -> list[dict]:
    """Generate 3 distinct scripts for the given theme using Gemini API.

    Makes 3 separate API calls, one per style (emotional, informative, controversial).
    Each script is returned as a dict with ssml_content and voice_configurations.

    Args:
        tema: The video theme/briefing.

    Returns:
        List of 3 script dicts, each containing 'ssml_content' and
        'voice_configurations' keys.
    """
    load_dotenv(dotenv_path=_ENV_PATH)
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment. Check skills/secrets/.env")

    client = genai.Client(api_key=api_key)
    references = load_references()
    print(f"[script_generator] {len(references)} reference(s) loaded.")

    scripts: list[dict] = []
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
            ssml_content = _clean_ssml_response(response.text)
            word_count = _count_words_without_ssml(ssml_content)
            script_dict = {
                "ssml_content": ssml_content,
                "voice_configurations": DEFAULT_VOICE_CONFIG.copy(),
            }
            scripts.append(script_dict)
            print(f"[script_generator] Script {i}/3 generated ({word_count} words).")
        except Exception as e:
            print(f"[script_generator] Error generating script {i}: {e}")
            raise

    return scripts
