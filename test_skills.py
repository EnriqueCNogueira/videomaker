"""Test script to verify script_generator and script_evaluator skills."""

import re
import sys

TEMA = "morning coffee routines"


def test_generator():
    """Test script_generator.generate() with a real API call."""
    print("=" * 60)
    print("TEST 1: script_generator.generate()")
    print("=" * 60)

    from skills.script_generator.generator import generate

    scripts = generate(TEMA)

    # Validate output
    assert isinstance(scripts, list), f"Expected list, got {type(scripts)}"
    assert len(scripts) == 3, f"Expected 3 scripts, got {len(scripts)}"

    for i, script in enumerate(scripts):
        assert "ssml_content" in script, f"Script {i+1} missing 'ssml_content'"
        assert "voice_configurations" in script, f"Script {i+1} missing 'voice_configurations'"

        ssml = script["ssml_content"]
        assert ssml.strip().startswith("<speak"), f"Script {i+1} SSML doesn't start with <speak>"
        assert "</speak>" in ssml, f"Script {i+1} SSML doesn't contain </speak>"

        # Count words (excluding tags)
        clean = re.sub(r"<[^>]+>", " ", ssml)
        word_count = len(clean.split())
        print(f"\n--- Script {i+1} ({word_count} words) ---")
        print(ssml[:300] + ("..." if len(ssml) > 300 else ""))

    print(f"\n[PASS] script_generator returned {len(scripts)} valid scripts.")
    return scripts


def test_evaluator(scripts):
    """Test script_evaluator.evaluate() with the generated scripts."""
    print("\n" + "=" * 60)
    print("TEST 2: script_evaluator.evaluate()")
    print("=" * 60)

    from skills.script_evaluator.evaluator import evaluate

    winner = evaluate(scripts)

    # Validate output
    assert isinstance(winner, dict), f"Expected dict, got {type(winner)}"
    assert "ssml_content" in winner, "Winner missing 'ssml_content'"
    assert "voice_configurations" in winner, "Winner missing 'voice_configurations'"

    # Check it's one of the originals
    found = any(winner["ssml_content"] == s["ssml_content"] for s in scripts)
    assert found, "Winner is not one of the original scripts!"

    clean = re.sub(r"<[^>]+>", " ", winner["ssml_content"])
    word_count = len(clean.split())
    print(f"\n--- Winner ({word_count} words) ---")
    print(winner["ssml_content"][:300] + ("..." if len(winner["ssml_content"]) > 300 else ""))
    print(f"\n[PASS] script_evaluator selected a valid script.")
    return winner


if __name__ == "__main__":
    try:
        scripts = test_generator()
        winner = test_evaluator(scripts)
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED")
        print("=" * 60)
    except Exception as e:
        print(f"\n[FAIL] {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
