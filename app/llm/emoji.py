from __future__ import annotations

import re

from app.config import Settings

# Keyword to emoji mapping for stub mode
# More specific keywords should come first to avoid generic matches
KEYWORD_EMOJI_MAP: dict[str, str] = {
    # Specific programming languages (before generic tech)
    "python": "🐍",
    "javascript": "💛",
    "rust": "🦀",
    # Finance & Crypto (before generic "it" matches "bitcoin")
    "crypto": "₿",
    "bitcoin": "₿",
    "finance": "💰",
    "money": "💰",
    "invest": "📈",
    "trading": "📈",
    "stock": "📈",
    # Business & Work (startup before art to avoid "st-art-up" matching art)
    "startup": "🚀",
    # Entertainment (before generic matches)
    "gaming": "🎮",
    "game": "🎮",
    "music": "🎵",
    "movie": "🎬",
    "film": "🎬",
    "art": "🎨",
    "photo": "📷",
    # Technology (generic)
    "tech": "💻",
    "code": "💻",
    "dev": "💻",
    "programming": "💻",
    "software": "💻",
    "work": "💼",
    "business": "💼",
    "office": "💼",
    "job": "💼",
    "career": "💼",
    "project": "📊",
    "team": "👥",
    # Learning & Education
    "book": "📚",
    "read": "📚",
    "learn": "📚",
    "study": "📚",
    "course": "🎓",
    "education": "🎓",
    "university": "🎓",
    "school": "🎓",
    # News & Media
    "news": "📰",
    "media": "📺",
    "channel": "📢",
    "blog": "📝",
    # Health & Fitness
    "health": "🏥",
    "fitness": "💪",
    "gym": "💪",
    "football": "⚽",
    "soccer": "⚽",
    "basketball": "🏀",
    "tennis": "🎾",
    "sport": "⚽",
    # Food & Lifestyle
    "food": "🍴",
    "cook": "👨‍🍳",
    "recipe": "🍳",
    "travel": "✈️",
    "trip": "✈️",
    "vacation": "🏖️",
    # Community & Social
    "community": "🏘️",
    "chat": "💬",
    "discussion": "💬",
    "family": "👨‍👩‍👧‍👦",
    "friends": "👯",
    # Science & Nature
    "science": "🔬",
    "research": "🔬",
    "nature": "🌿",
    "animal": "🐾",
    "pet": "🐾",
    "dog": "🐕",
    "cat": "🐈",
    # Other
    "robot": "🤖",
    "meme": "😂",
    "humor": "😂",
    "funny": "😂",
    "politics": "🏛️",
    "event": "📅",
    "sale": "🛒",
    "shop": "🛒",
    # AI should be last since "ai" is a common substring
    "ai": "🤖",
}

DEFAULT_EMOJI = "💬"

EMOJI_PROMPT_SYSTEM = """You are an emoji selector. Given a chat/channel title and optional description, select ONE emoji that best represents the topic or theme.

Rules:
- Return ONLY the emoji character, nothing else
- Choose the most specific and relevant emoji
- If unsure, prefer common category emojis (💬 for chat, 📢 for channel, etc.)
"""

EMOJI_PROMPT_USER = """Title: {title}
Description: {about}

Select one emoji:"""


def _starts_with_emoji(text: str) -> bool:
    """Check if text already starts with an emoji."""
    if not text:
        return False
    # Unicode emoji ranges
    emoji_pattern = re.compile(
        "^["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002702-\U000027B0"  # dingbats
        "\U000024C2-\U0001F251"  # enclosed characters
        "\U0001F900-\U0001F9FF"  # supplemental symbols
        "\U0001FA00-\U0001FA6F"  # chess symbols
        "\U0001FA70-\U0001FAFF"  # symbols and pictographs extended-a
        "\U00002600-\U000026FF"  # misc symbols
        "]"
    )
    return bool(emoji_pattern.match(text))


def _stub_select_emoji(title: str, about: str | None) -> str:
    """Select emoji based on keyword matching (stub mode)."""
    text = f"{title} {about or ''}".lower()

    for keyword, emoji in KEYWORD_EMOJI_MAP.items():
        if keyword in text:
            return emoji

    return DEFAULT_EMOJI


def _llm_select_emoji(title: str, about: str | None, settings: Settings) -> str | None:
    """Select emoji using LLM (OpenAI)."""
    if not settings.openai_api_key:
        return None

    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": EMOJI_PROMPT_SYSTEM},
                {
                    "role": "user",
                    "content": EMOJI_PROMPT_USER.format(
                        title=title, about=about or "No description"
                    ),
                },
            ],
            max_tokens=10,
            temperature=0.3,
        )
        content = response.choices[0].message.content or ""
        # Extract first emoji-like character
        content = content.strip()
        if content and len(content) <= 4:  # Single emoji can be up to 4 bytes
            return content
        return None
    except Exception:
        return None


def select_emoji(title: str, about: str | None, settings: Settings) -> str:
    """Select an appropriate emoji for a chat based on its title and description.

    Args:
        title: Chat title
        about: Chat description (optional)
        settings: App settings

    Returns:
        Selected emoji character
    """
    # Check if title already has emoji
    if _starts_with_emoji(title):
        return ""  # Return empty to signal no emoji needed

    # Stub mode: use keyword matching
    if settings.llm_mode == "stub":
        return _stub_select_emoji(title, about)

    # LLM mode: try OpenAI, fallback to stub
    llm_emoji = _llm_select_emoji(title, about, settings)
    if llm_emoji:
        return llm_emoji

    # Fallback to stub selection
    return _stub_select_emoji(title, about)
