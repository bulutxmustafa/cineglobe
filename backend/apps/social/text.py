"""User text hygiene for the social layer (plan §3.11): URL stripping, word filter,
username rules. Everything is stored and rendered as plain text.
"""

from __future__ import annotations

import re
import unicodedata

USERNAME = re.compile(r"^[a-z0-9_]{3,20}$")

# Routes, brand and staff-like names nobody may take.
RESERVED_USERNAMES = {
    "admin",
    "administrator",
    "api",
    "app",
    "auth",
    "cineglobe",
    "destek",
    "help",
    "login",
    "logout",
    "me",
    "moderator",
    "mod",
    "official",
    "resmi",
    "root",
    "s",
    "settings",
    "shared",
    "signup",
    "staff",
    "support",
    "system",
    "tmdb",
    "u",
    "user",
    "users",
    "www",
    "yonetici",
}

# Small, generic TR+EN list (policy v1.7: insults/hate). Matching is on folded
# word boundaries so ordinary words containing these letters are not caught.
BANNED_WORDS = {
    # Ambiguous short words ("got", "pic") are left out: they block innocent English.
    "amk",
    "aq",
    "orospu",
    "piç",
    "siktir",
    "sik",
    "yarrak",
    "göt",
    "ibne",
    "kahpe",
    "pezevenk",
    "fuck",
    "fucking",
    "shit",
    "bitch",
    "cunt",
    "nigger",
    "faggot",
    "whore",
    "slut",
}

URL_PATTERN = re.compile(
    r"(https?://\S+|www\.\S+|\b[\w-]+(?:\.[\w-]+)*\.(?:com|net|org|io|tr|co|app|dev|ly|me|tv|gg|xyz|info|biz)\b\S*)",
    re.IGNORECASE,
)


def fold(text: str) -> str:
    """Lower-case, Turkish-aware, accent-free form for comparisons."""
    text = (
        unicodedata.normalize("NFKC", text).replace("İ", "i").replace("I", "ı").lower()
    )
    return text


def strip_urls(text: str) -> str:
    return " ".join(URL_PATTERN.sub("", text).split())


def contains_banned_word(text: str) -> bool:
    # Both foldings: Turkish ("I" -> "ı") and plain ("SHIT" must still match "shit").
    words = set(re.findall(r"\w+", fold(text))) | set(
        re.findall(r"\w+", text.casefold())
    )
    return not words.isdisjoint(BANNED_WORDS)


def clean_text(text: str) -> str:
    """Normalise whitespace and drop links (bios, list text, comments)."""
    return strip_urls(unicodedata.normalize("NFKC", text or "")).strip()


def username_problem(username: str) -> str | None:
    """None when acceptable, else an error code."""
    if not USERNAME.match(username):
        return "invalid_username"
    if username in RESERVED_USERNAMES:
        return "reserved_username"
    if contains_banned_word(username.replace("_", " ")) or any(
        word in username for word in BANNED_WORDS if len(word) >= 4
    ):
        return "banned_word"
    return None
