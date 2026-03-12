# config.py — Video assembly and subtitle styling settings

# --- Input/output file names ---
VIDEO_FILENAME = "video.mp4"
AUDIO_FILENAME = "audio.mp3"
SUBTITLE_FILENAME = "subtitles.srt"
OUTPUT_FILENAME = "output.mp4"

# --- Video codec settings ---
VIDEO_CODEC = "libx264"
VIDEO_PRESET = "medium"
VIDEO_CRF = 23               # 0 (lossless) to 51 (worst); 23 is default

# --- Audio codec settings ---
AUDIO_CODEC = "aac"
AUDIO_BITRATE = "192k"

# --- Subtitle style (ASS override tags for FFmpeg subtitles filter) ---
SUBTITLE_FONT_NAME = "Arial"
SUBTITLE_FONT_SIZE = 20
SUBTITLE_PRIMARY_COLOUR = "&H00FFFFFF"   # White (ASS &HAABBGGRR)
SUBTITLE_OUTLINE_COLOUR = "&H00000000"   # Black outline
SUBTITLE_BACK_COLOUR = "&H80000000"      # Semi-transparent black shadow
SUBTITLE_BORDER_STYLE = 1    # 1 = outline + drop shadow
SUBTITLE_OUTLINE = 2         # Outline thickness
SUBTITLE_SHADOW = 1          # Shadow depth
SUBTITLE_ALIGNMENT = 2       # 2 = bottom-center (SSA/ASS numpad)
SUBTITLE_MARGIN_V = 60       # Vertical margin from bottom
SUBTITLE_BOLD = 1             # 1 = bold
