# tts.py — Integração com Google Cloud Text-to-Speech

import os
from pathlib import Path

from dotenv import load_dotenv
from google.cloud import texttospeech

from skills.audio_generator import config

_ENV_PATH = Path(__file__).parents[2] / "skills" / "secrets" / ".env"


def generate(script: dict, output_dir: str) -> str:
    """Synthesize speech from a script dict and save as MP3.

    Takes the output of script_evaluator (dict with ssml_content and
    voice_configurations) and generates an audio file via Google Cloud TTS.

    Args:
        script: Dict with 'ssml_content' (SSML string) and
                'voice_configurations' (dict with language, voice_type, speed, pitch).
        output_dir: Directory path where audio.mp3 will be saved.

    Returns:
        Absolute path to the generated .mp3 file.

    Raises:
        ValueError: If script is missing required keys.
        Exception: If the TTS API call fails.
    """
    ssml_content = script.get("ssml_content")
    if not ssml_content:
        raise ValueError("Script dict missing 'ssml_content' key.")

    voice_cfg = script.get("voice_configurations", {})

    # Load credentials path from .env
    load_dotenv(dotenv_path=_ENV_PATH)
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if creds_path:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path

    print("[audio_generator] Initializing TTS client...")
    client = texttospeech.TextToSpeechClient()

    # Voice selection: use script's voice_configurations with config.py fallbacks
    language_code = voice_cfg.get("language", config.LANGUAGE_CODE)
    voice_name = voice_cfg.get("voice_type", config.VOICE_NAME)

    # Journey and Studio voices do not support SSML, pitch, or speaking_rate.
    # Fall back to Neural2 voice from config.py to preserve SSML markup.
    limited_voice = any(t in voice_name for t in ("Journey", "Studio"))
    if limited_voice:
        print(f"[audio_generator] {voice_name} does not support SSML. Using {config.VOICE_NAME} instead.")
        voice_name = config.VOICE_NAME

    synthesis_input = texttospeech.SynthesisInput(ssml=ssml_content)

    voice = texttospeech.VoiceSelectionParams(
        language_code=language_code,
        name=voice_name,
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=config.AUDIO_ENCODING,
        speaking_rate=voice_cfg.get("speed", config.SPEAKING_RATE),
        pitch=voice_cfg.get("pitch", config.PITCH),
    )

    print(f"[audio_generator] Voice: {voice_name} ({language_code}), rate={audio_config.speaking_rate}, pitch={audio_config.pitch}")
    print("[audio_generator] Calling TTS API...")

    try:
        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )
    except Exception as e:
        print(f"[audio_generator] TTS API error: {e}")
        raise

    # Ensure output directory exists
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # Save audio
    audio_file = out_path / "audio.mp3"
    with open(audio_file, "wb") as f:
        f.write(response.audio_content)

    audio_path = str(audio_file.resolve())
    size_kb = len(response.audio_content) / 1024
    print(f"[audio_generator] Audio saved: {audio_path} ({size_kb:.1f} KB)")

    return audio_path
