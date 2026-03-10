# transcriber.py — Generate SRT subtitles from audio using Google Cloud Speech-to-Text

import os
from pathlib import Path

from dotenv import load_dotenv
from google.cloud import speech

from skills.subtitle_generator import config

_ENV_PATH = Path(__file__).parents[2] / "skills" / "secrets" / ".env"


def _seconds_to_srt_time(seconds: float) -> str:
    """Convert seconds to SRT timestamp format HH:MM:SS,mmm."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _transcribe_audio(audio_path: str, language_code: str) -> list[dict]:
    """Transcribe audio and return word-level timestamps.

    Uses Google Cloud Speech-to-Text with long_running_recognize to handle
    audio up to 1:30 in length. Returns each word with its start and end time.

    Args:
        audio_path: Path to the MP3 file.
        language_code: BCP-47 language code (e.g., 'en-US').

    Returns:
        List of dicts with keys: 'word' (str), 'start_time' (float),
        'end_time' (float) in seconds.
    """
    client = speech.SpeechClient()

    with open(audio_path, "rb") as f:
        audio_content = f.read()

    audio = speech.RecognitionAudio(content=audio_content)

    recognition_config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.MP3,
        language_code=language_code,
        enable_word_time_offsets=True,
        enable_automatic_punctuation=True,
        model=config.STT_MODEL,
    )

    operation = client.long_running_recognize(config=recognition_config, audio=audio)
    print("[subtitle_generator] Waiting for transcription to complete...")
    response = operation.result(timeout=120)

    words = []
    for result in response.results:
        if not result.alternatives:
            continue
        for word_info in result.alternatives[0].words:
            words.append({
                "word": word_info.word,
                "start_time": word_info.start_time.total_seconds(),
                "end_time": word_info.end_time.total_seconds(),
            })

    return words


def _group_words_into_segments(words: list[dict]) -> list[dict]:
    """Group transcribed words into subtitle segments.

    Uses a hybrid strategy: respects natural speech pauses and punctuation
    boundaries, with word-count guardrails for readability on mobile screens.

    Args:
        words: List of word dicts from _transcribe_audio().

    Returns:
        List of segment dicts with keys: 'text' (str),
        'start_time' (float), 'end_time' (float).
    """
    if not words:
        return []

    segments = []
    current_segment = [words[0]]

    for i in range(1, len(words)):
        word = words[i]
        prev_word = words[i - 1]
        segment_len = len(current_segment)

        # Calculate gap between this word and the previous one
        gap = word["start_time"] - prev_word["end_time"]

        # Determine if we should break here
        force_break = segment_len >= config.WORDS_PER_SUBTITLE_MAX
        pause_break = (
            gap >= config.PAUSE_BREAK_THRESHOLD
            and segment_len >= config.WORDS_PER_SUBTITLE_MIN
        )
        punctuation_break = (
            prev_word["word"].rstrip().endswith((".", "!", "?"))
            and segment_len >= config.WORDS_PER_SUBTITLE_MIN
        )

        if force_break or pause_break or punctuation_break:
            # Flush current segment
            segments.append({
                "text": " ".join(w["word"] for w in current_segment),
                "start_time": current_segment[0]["start_time"],
                "end_time": current_segment[-1]["end_time"],
            })
            current_segment = [word]
        else:
            current_segment.append(word)

    # Flush remaining words
    if current_segment:
        segments.append({
            "text": " ".join(w["word"] for w in current_segment),
            "start_time": current_segment[0]["start_time"],
            "end_time": current_segment[-1]["end_time"],
        })

    return segments


def _format_srt(segments: list[dict]) -> str:
    """Format subtitle segments as an SRT string.

    Args:
        segments: List of segment dicts with 'text', 'start_time', 'end_time'.

    Returns:
        Complete SRT file content as a string.
    """
    lines = []
    for i, segment in enumerate(segments, start=1):
        start = _seconds_to_srt_time(segment["start_time"])
        end = _seconds_to_srt_time(segment["end_time"])
        lines.append(f"{i}")
        lines.append(f"{start} --> {end}")
        lines.append(segment["text"])
        lines.append("")  # blank line separator

    return "\n".join(lines)


def generate(audio_path: str, script: dict, output_dir: str) -> str:
    """Transcribe audio and generate an SRT subtitle file.

    Uses Google Cloud Speech-to-Text to obtain word-level timestamps from
    the audio, groups words into short subtitle segments suitable for
    short-form vertical video, and writes an SRT file.

    Args:
        audio_path: Absolute path to the MP3 audio file.
        script: Dict with 'ssml_content' and 'voice_configurations'
                (language is extracted from voice_configurations).
        output_dir: Directory path where subtitles.srt will be saved.

    Returns:
        Absolute path to the generated .srt file.

    Raises:
        FileNotFoundError: If audio_path does not exist.
        ValueError: If Speech-to-Text returns no words.
        Exception: If the Speech-to-Text API call fails.
    """
    if not Path(audio_path).exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    voice_cfg = script.get("voice_configurations", {})

    # Load credentials
    load_dotenv(dotenv_path=_ENV_PATH)
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if creds_path:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path

    # Determine language from script or config fallback
    language_code = voice_cfg.get("language", config.LANGUAGE_CODE)

    print(f"[subtitle_generator] Processing audio: {audio_path}")
    print(f"[subtitle_generator] Language: {language_code}")

    # Transcribe with word-level timestamps
    print("[subtitle_generator] Calling Speech-to-Text API...")
    try:
        words = _transcribe_audio(audio_path, language_code)
    except Exception as e:
        print(f"[subtitle_generator] Speech-to-Text API error: {e}")
        raise

    print(f"[subtitle_generator] Transcribed {len(words)} words.")

    if not words:
        raise ValueError("Speech-to-Text returned no words. Check audio file.")

    # Group words into subtitle segments
    segments = _group_words_into_segments(words)
    print(f"[subtitle_generator] Grouped into {len(segments)} subtitle segments.")

    # Format as SRT
    srt_content = _format_srt(segments)

    # Write SRT file
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    srt_file = out_path / "subtitles.srt"

    with open(srt_file, "w", encoding="utf-8") as f:
        f.write(srt_content)

    srt_path = str(srt_file.resolve())
    print(f"[subtitle_generator] Subtitles saved: {srt_path} ({len(segments)} entries)")

    return srt_path
