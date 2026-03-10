# config.py — Speech-to-Text and subtitle grouping settings

# Language (must match TTS language used for the audio)
LANGUAGE_CODE = "en-US"

# Speech-to-Text model
# "latest_long" handles audio up to 480 min; safe for 1:00–1:30 videos
STT_MODEL = "latest_long"

# Subtitle segment grouping
WORDS_PER_SUBTITLE_MIN = 2    # Minimum words per subtitle line
WORDS_PER_SUBTITLE_MAX = 6    # Maximum words per subtitle line
PAUSE_BREAK_THRESHOLD = 0.4   # Seconds — gap between words that forces a new segment
