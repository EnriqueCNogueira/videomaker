# assembler.py — Combine background video, narration audio, and subtitles into final output

import json
import os
import shutil
import subprocess
from pathlib import Path

from skills.video_assembler import config

# Cached paths for ffmpeg/ffprobe executables
_ffmpeg_path: str | None = None
_ffprobe_path: str | None = None


def _find_tool(name: str) -> str:
    """Find an FFmpeg tool (ffmpeg or ffprobe) on the system.

    Checks PATH first, then common Windows installation directories.

    Args:
        name: Tool name ('ffmpeg' or 'ffprobe').

    Returns:
        Absolute path to the tool executable.

    Raises:
        FileNotFoundError: If the tool is not found anywhere.
    """
    # 1. Check PATH
    found = shutil.which(name)
    if found:
        return found

    # 2. Check common Windows locations
    home = Path.home()
    candidates = [
        home / "AppData" / "Local" / "Microsoft" / "WinGet" / "Links" / f"{name}.exe",
        Path("C:/ffmpeg/bin") / f"{name}.exe",
        Path("C:/Program Files/ffmpeg/bin") / f"{name}.exe",
    ]
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        candidates.append(Path(local_app_data) / "ffmpeg" / "bin" / f"{name}.exe")
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    raise FileNotFoundError(
        f"{name} not found. Install FFmpeg and add it to PATH. "
        "Download from https://ffmpeg.org/download.html"
    )


def _get_ffmpeg() -> str:
    """Get the path to the ffmpeg executable (cached)."""
    global _ffmpeg_path
    if _ffmpeg_path is None:
        _ffmpeg_path = _find_tool("ffmpeg")
    return _ffmpeg_path


def _get_ffprobe() -> str:
    """Get the path to the ffprobe executable (cached)."""
    global _ffprobe_path
    if _ffprobe_path is None:
        _ffprobe_path = _find_tool("ffprobe")
    return _ffprobe_path


def _get_audio_duration(audio_path: Path) -> float:
    """Get the duration of an audio file in seconds using ffprobe.

    Args:
        audio_path: Path to the audio file.

    Returns:
        Duration in seconds as a float.

    Raises:
        RuntimeError: If ffprobe fails or returns no duration.
    """
    cmd = [
        _get_ffprobe(), "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        str(audio_path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        duration = float(data["format"]["duration"])
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"ffprobe failed: {e.stderr}") from e
    except (KeyError, json.JSONDecodeError, ValueError) as e:
        raise RuntimeError(f"Could not parse audio duration: {e}") from e

    print(f"[video_assembler] Audio duration: {duration:.2f}s")
    return duration


def _build_force_style() -> str:
    """Build the ASS force_style string from config values.

    Returns:
        Comma-separated ASS override string for FFmpeg's subtitles filter.
    """
    parts = [
        f"FontName={config.SUBTITLE_FONT_NAME}",
        f"FontSize={config.SUBTITLE_FONT_SIZE}",
        f"PrimaryColour={config.SUBTITLE_PRIMARY_COLOUR}",
        f"OutlineColour={config.SUBTITLE_OUTLINE_COLOUR}",
        f"BackColour={config.SUBTITLE_BACK_COLOUR}",
        f"BorderStyle={config.SUBTITLE_BORDER_STYLE}",
        f"Outline={config.SUBTITLE_OUTLINE}",
        f"Shadow={config.SUBTITLE_SHADOW}",
        f"Alignment={config.SUBTITLE_ALIGNMENT}",
        f"MarginV={config.SUBTITLE_MARGIN_V}",
        f"Bold={config.SUBTITLE_BOLD}",
    ]
    return ",".join(parts)


def _build_ffmpeg_command(duration: float) -> list[str]:
    """Build the FFmpeg command as a list of arguments.

    Uses relative filenames — must be run with cwd set to the video
    directory to avoid Windows path escaping issues in the subtitles filter.

    Args:
        duration: Audio duration in seconds for the -t trim flag.

    Returns:
        List of command-line arguments for subprocess.run().
    """
    force_style = _build_force_style()
    vf_filter = f"subtitles={config.SUBTITLE_FILENAME}:force_style='{force_style}'"

    return [
        _get_ffmpeg(), "-y",
        "-i", config.VIDEO_FILENAME,
        "-i", config.AUDIO_FILENAME,
        "-vf", vf_filter,
        "-map", "0:v",
        "-map", "1:a",
        "-c:v", config.VIDEO_CODEC,
        "-preset", config.VIDEO_PRESET,
        "-crf", str(config.VIDEO_CRF),
        "-c:a", config.AUDIO_CODEC,
        "-b:a", config.AUDIO_BITRATE,
        "-t", str(duration),
        config.OUTPUT_FILENAME,
    ]


def assemble(video_dir: str) -> str:
    """Assemble final video from video.mp4, audio.mp3, and subtitles.srt.

    Combines the background video with narration audio (replacing original
    audio), burns in subtitles with TikTok/Shorts styling, and trims the
    output to match the audio duration.

    Args:
        video_dir: Path to the videoN directory containing the 3 input files.

    Returns:
        Absolute path to the generated output.mp4 file.

    Raises:
        FileNotFoundError: If any required input file or FFmpeg is missing.
        RuntimeError: If FFmpeg encoding fails.
    """
    dir_path = Path(video_dir)

    # 1. Check FFmpeg availability (will raise FileNotFoundError if missing)
    ffmpeg_bin = _get_ffmpeg()
    print(f"[video_assembler] Using FFmpeg: {ffmpeg_bin}")

    # 2. Validate input files
    for filename in (config.VIDEO_FILENAME, config.AUDIO_FILENAME, config.SUBTITLE_FILENAME):
        file_path = dir_path / filename
        if not file_path.exists():
            raise FileNotFoundError(f"Required file not found: {file_path}")

    print(f"[video_assembler] Input directory: {dir_path.resolve()}")
    print(f"[video_assembler] Found: {config.VIDEO_FILENAME}, {config.AUDIO_FILENAME}, {config.SUBTITLE_FILENAME}")

    # 3. Get audio duration
    audio_path = dir_path / config.AUDIO_FILENAME
    duration = _get_audio_duration(audio_path)

    # 4. Build and run FFmpeg command (cwd=video_dir for relative paths)
    cmd = _build_ffmpeg_command(duration)
    print(f"[video_assembler] Running FFmpeg...")

    try:
        subprocess.run(
            cmd,
            cwd=str(dir_path.resolve()),
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"[video_assembler] FFmpeg error:\n{e.stderr}")
        raise RuntimeError(f"FFmpeg encoding failed: {e.stderr}") from e

    # 5. Verify output
    output_path = dir_path / config.OUTPUT_FILENAME
    if not output_path.exists() or output_path.stat().st_size == 0:
        raise RuntimeError(f"FFmpeg produced no output or empty file: {output_path}")

    output_abs = str(output_path.resolve())
    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"[video_assembler] Output saved: {output_abs} ({size_mb:.1f} MB, {duration:.1f}s)")

    return output_abs
