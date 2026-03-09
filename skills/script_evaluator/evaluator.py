# evaluator.py — Agente Gemini que avalia e refina o roteiro

import os
import re
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

from skills.script_evaluator.prompts import SYSTEM_PROMPT, build_evaluation_prompt

_ENV_PATH = Path(__file__).parents[2] / "skills" / "secrets" / ".env"


def _strip_ssml(ssml: str) -> str:
    """Remove SSML/XML tags from text, returning clean readable content.

    Args:
        ssml: String potentially containing SSML markup.

    Returns:
        Clean text with all XML tags removed and whitespace normalized.
    """
    clean = re.sub(r"<[^>]+>", " ", ssml)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean


def _parse_selection(response_text: str) -> int | None:
    """Extract the selected script number from model response.

    Looks for 'SELECTED: N' pattern anywhere in the response.

    Args:
        response_text: The full model response text.

    Returns:
        The 1-based script number, or None if parsing fails.
    """
    match = re.search(r"SELECTED:\s*(\d+)", response_text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def _call_and_parse(
    client: genai.Client, prompt: str, num_scripts: int
) -> int | None:
    """Make a single API call and attempt to parse the selection.

    Args:
        client: Initialized Gemini client.
        prompt: The complete user prompt.
        num_scripts: Total number of scripts (for bounds checking).

    Returns:
        1-based index of the selected script, or None if parsing fails.

    Raises:
        Exception: If the API call itself fails.
    """
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.3,
            ),
        )
        text = response.text.strip()
        print(f"[script_evaluator] Model response length: {len(text)} chars.")
    except Exception as e:
        print(f"[script_evaluator] API error: {e}")
        raise

    selected = _parse_selection(text)
    if selected is not None and 1 <= selected <= num_scripts:
        return selected

    if selected is not None:
        print(f"[script_evaluator] Selection {selected} out of range (1-{num_scripts}).")
    return None


def evaluate(scripts: list[dict]) -> dict:
    """Evaluate a list of script dicts and return the best one unchanged.

    Sends the clean text of each script to Gemini for comparative analysis,
    then returns the original dict (with SSML and voice_configurations intact)
    for the selected script.

    Args:
        scripts: List of script dicts, each containing 'ssml_content' and
                 'voice_configurations' keys.

    Returns:
        The winning script dict, exactly as received (no modifications).

    Raises:
        ValueError: If scripts list has fewer than 2 items.
    """
    if not scripts or len(scripts) < 2:
        raise ValueError(
            f"Expected at least 2 scripts for evaluation, got {len(scripts) if scripts else 0}"
        )

    load_dotenv(dotenv_path=_ENV_PATH)
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment. Check skills/secrets/.env")

    client = genai.Client(api_key=api_key)

    # Extract and clean text for evaluation
    clean_texts: list[str] = []
    for i, script in enumerate(scripts):
        ssml = script.get("ssml_content", "")
        clean = _strip_ssml(ssml)
        clean_texts.append(clean)
        print(f"[script_evaluator] Script {i + 1}: {len(clean.split())} words.")

    prompt = build_evaluation_prompt(clean_texts)

    # First attempt
    selected = _call_and_parse(client, prompt, len(scripts))

    if selected is not None:
        print(f"[script_evaluator] Selected script {selected} of {len(scripts)}.")
        return scripts[selected - 1]

    # Retry with a more constrained prompt
    print("[script_evaluator] Could not parse selection. Retrying with constrained prompt...")
    retry_prompt = (
        prompt
        + "\n\nIMPORTANT: Your response MUST end with exactly 'SELECTED: N' "
        "where N is the number of the best script. This is the last line."
    )
    selected = _call_and_parse(client, retry_prompt, len(scripts))

    if selected is not None:
        print(f"[script_evaluator] Selected script {selected} of {len(scripts)} (retry).")
        return scripts[selected - 1]

    # Fallback: pick the first script
    print("[script_evaluator] WARNING: Parsing failed after retry. Defaulting to script 1.")
    return scripts[0]
