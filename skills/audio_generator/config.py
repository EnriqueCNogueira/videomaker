# config.py — Voice, speed, and language settings for TTS

from google.cloud.texttospeech import SsmlVoiceGender, AudioEncoding

# Language and voice
LANGUAGE_CODE = "en-US"
VOICE_NAME = "en-US-Neural2-D"  # Male neural voice; alternatives: en-US-Neural2-F (female)
SSML_GENDER = SsmlVoiceGender.MALE

# Audio output
AUDIO_ENCODING = AudioEncoding.MP3
SPEAKING_RATE = 1.0   # 0.25–4.0
PITCH = 0.0           # -20.0–20.0 semitones
