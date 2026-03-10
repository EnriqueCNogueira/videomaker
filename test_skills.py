"""Test script to verify script_generator, script_evaluator, and audio_generator skills."""

import os
import re
import shutil
import sys

TEMA = "morning coffee routines"
TEST_AUDIO_DIR = "videos/test_audio"


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


def test_audio_generator(winner, output_dir):
    """Test audio_generator.generate() with the winning script."""
    print("\n" + "=" * 60)
    print("TEST 3: audio_generator.generate()")
    print("=" * 60)

    from skills.audio_generator.tts import generate

    # Generate audio
    audio_path = generate(winner, TEST_AUDIO_DIR)

    # Validate output
    assert isinstance(audio_path, str), f"Expected str path, got {type(audio_path)}"
    assert os.path.exists(audio_path), f"Audio file not found: {audio_path}"

    file_size = os.path.getsize(audio_path)
    assert file_size > 0, "Audio file is empty (0 bytes)"

    print(f"\n--- Audio Generated ---")
    print(f"Path: {audio_path}")
    print(f"Size: {file_size / 1024:.1f} KB")

    print(f"\n[PASS] audio_generator created a valid MP3 file.")
    return audio_path


def test_subtitle_generator(audio_path, winner, output_dir):
    """Test subtitle_generator.generate() with the generated audio."""
    print("\n" + "=" * 60)
    print("TEST 4: subtitle_generator.generate()")
    print("=" * 60)

    from skills.subtitle_generator.transcriber import generate

    srt_path = generate(audio_path, winner, output_dir)

    # Validate output
    assert isinstance(srt_path, str), f"Expected str path, got {type(srt_path)}"
    assert os.path.exists(srt_path), f"SRT file not found: {srt_path}"

    file_size = os.path.getsize(srt_path)
    assert file_size > 0, "SRT file is empty (0 bytes)"

    # Validate SRT format
    with open(srt_path, "r", encoding="utf-8") as f:
        srt_content = f.read()

    assert re.search(r"^\d+$", srt_content, re.MULTILINE), "SRT has no sequence numbers"
    assert re.search(r"\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}", srt_content), \
        "SRT has no valid timestamps"

    entries = re.findall(r"^\d+$", srt_content, re.MULTILINE)

    print(f"\n--- Subtitles Generated ---")
    print(f"Path: {srt_path}")
    print(f"Size: {file_size / 1024:.1f} KB")
    print(f"Entries: {len(entries)} subtitle segments")
    print(f"\nFirst 5 entries:")
    blocks = srt_content.strip().split("\n\n")
    for block in blocks[:5]:
        print(f"  {block}")

    print(f"\n[PASS] subtitle_generator created a valid SRT file.")
    return srt_path


if __name__ == "__main__":
    import datetime

    # Cria uma pasta nova com timestamp dentro de videos/
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"videos/{timestamp}"
    os.makedirs(output_dir, exist_ok=True)

    try:
        scripts = test_generator()
        winner = test_evaluator(scripts)
        audio_path = test_audio_generator(winner, output_dir)
        srt_path = test_subtitle_generator(audio_path, winner, output_dir)
        print("\n" + "=" * 60)
        print(f"ALL TESTS PASSED — output em: {output_dir}")
        print("=" * 60)
    except Exception as e:
        print(f"\n[FAIL] {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        # Remove a pasta só em caso de falha
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
            print(f"\n[CLEANUP] Removido {output_dir} após falha")
        sys.exit(1)
