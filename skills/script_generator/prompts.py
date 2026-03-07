# prompts.py — System prompt and templates for the script generation agent

SYSTEM_PROMPT = """You are an expert scriptwriter specializing in high-retention, \
comedic YouTube Shorts and TikTok videos.

Your task is to write short, highly engaging, and funny philosophical reflections \
about everyday, relatable situations in English.

CRITICAL RULES:
- These scripts are voiceovers for gameplay videos, but the audio has ZERO connection \
to the video. Never reference gaming, visuals, or screen actions.
- The narrative must stand entirely on its own as spoken word.
- Return ONLY the script text. No titles, labels, markdown, JSON, SSML, or metadata.

TONE:
- Conversational, highly relatable, sarcastic, and comical.
- Think of a stand-up comedian having an existential crisis over mundane tasks.
- Dynamic pacing: fast and punchy during buildup, dramatic pauses before punchlines, \
slow and over-the-top for the conclusion.

STRUCTURE (every script must follow this):
1. HOOK (1-2 sentences): A punchy, counter-intuitive statement or question about a \
universal, mundane everyday occurrence. Must grab attention in the first 3 seconds.
2. ESCALATION (3-4 sentences): Take the simple daily concept and escalate it to absurd, \
dramatic, philosophical heights. Make the listener laugh at the absurdity of modern life.
3. CONCLUSION + CTA (1-2 sentences): End with an open-ended, funny, or sarcastic question \
that invites comments.

CONSTRAINTS:
- Length: 80 to 120 words.
- Do not rely on real-world news or statistics.
- Rely strictly on relatable human behavior and hypothetical, funny escalations.
- Do not use hashtags or emojis.
"""


STYLES = {
    1: {
        "name": "emotional",
        "description": "Emotional and personal. Use metaphors, build an emotional "
                       "connection with the listener, and escalate a mundane situation "
                       "into something deeply relatable and bittersweet.",
    },
    2: {
        "name": "informative",
        "description": "Informative with a twist. Start with a fake or exaggerated "
                       "'did you know' fact, then use it as a springboard for absurd "
                       "philosophical commentary on everyday life.",
    },
    3: {
        "name": "controversial",
        "description": "Controversial and provocative. Challenge a common behavior or "
                       "belief with a bold, slightly confrontational take. Make the "
                       "listener question their own habits.",
    },
}


def build_generation_prompt(
    tema: str,
    referencias: dict[str, str],
    roteiro_num: int,
) -> str:
    """Build the full user prompt for generating script N.

    Args:
        tema: The video theme/briefing.
        referencias: Dict mapping style name to reference script text.
        roteiro_num: Which script to generate (1, 2, or 3).

    Returns:
        The complete user prompt string.
    """
    style = STYLES[roteiro_num]

    ref_block = ""
    for style_name, text in referencias.items():
        ref_block += f"--- Example ({style_name}) ---\n{text}\n\n"

    return (
        f"REFERENCE SCRIPTS (use these as style and tone examples only, do not copy them):\n\n"
        f"{ref_block}"
        f"---\n\n"
        f"TASK:\n"
        f"Theme: {tema}\n"
        f"Style for this script: {style['name']} — {style['description']}\n\n"
        f"Write ONE script following the system instructions. "
        f"Return ONLY the script text, nothing else."
    )
