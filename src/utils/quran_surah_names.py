"""Standard English transliterations of the 114 Qur'an surah names, in canonical order.

This is the universally-agreed enumeration/ordering of surahs (not a matter of juristic
or scholarly disagreement -- unlike hadith authenticity grading, which this project
deliberately does not adjudicate, see DECISIONS.md DG-5). Used only to resolve a
surah-name citation (e.g. "Al-Baqarah") to its surah_id for lookup against
data/corpus/quran.jsonl, which itself only stores the Arabic surah_name.

Common alternate spellings are included as extra keys mapping to the same id, since
citation text in model output/benchmarks is not guaranteed to use one fixed spelling.
"""

from __future__ import annotations

from src.utils.text_normalize import normalize_name_key

SURAH_NAMES: dict[int, str] = {
    1: "Al-Fatihah", 2: "Al-Baqarah", 3: "Ali 'Imran", 4: "An-Nisa", 5: "Al-Ma'idah",
    6: "Al-An'am", 7: "Al-A'raf", 8: "Al-Anfal", 9: "At-Tawbah", 10: "Yunus",
    11: "Hud", 12: "Yusuf", 13: "Ar-Ra'd", 14: "Ibrahim", 15: "Al-Hijr",
    16: "An-Nahl", 17: "Al-Isra", 18: "Al-Kahf", 19: "Maryam", 20: "Taha",
    21: "Al-Anbiya", 22: "Al-Hajj", 23: "Al-Mu'minun", 24: "An-Nur", 25: "Al-Furqan",
    26: "Ash-Shu'ara", 27: "An-Naml", 28: "Al-Qasas", 29: "Al-Ankabut", 30: "Ar-Rum",
    31: "Luqman", 32: "As-Sajdah", 33: "Al-Ahzab", 34: "Saba", 35: "Fatir",
    36: "Ya-Sin", 37: "As-Saffat", 38: "Sad", 39: "Az-Zumar", 40: "Ghafir",
    41: "Fussilat", 42: "Ash-Shuraa", 43: "Az-Zukhruf", 44: "Ad-Dukhan", 45: "Al-Jathiyah",
    46: "Al-Ahqaf", 47: "Muhammad", 48: "Al-Fath", 49: "Al-Hujurat", 50: "Qaf",
    51: "Adh-Dhariyat", 52: "At-Tur", 53: "An-Najm", 54: "Al-Qamar", 55: "Ar-Rahman",
    56: "Al-Waqi'ah", 57: "Al-Hadid", 58: "Al-Mujadilah", 59: "Al-Hashr", 60: "Al-Mumtahanah",
    61: "As-Saff", 62: "Al-Jumu'ah", 63: "Al-Munafiqun", 64: "At-Taghabun", 65: "At-Talaq",
    66: "At-Tahrim", 67: "Al-Mulk", 68: "Al-Qalam", 69: "Al-Haqqah", 70: "Al-Ma'arij",
    71: "Nuh", 72: "Al-Jinn", 73: "Al-Muzzammil", 74: "Al-Muddaththir", 75: "Al-Qiyamah",
    76: "Al-Insan", 77: "Al-Mursalat", 78: "An-Naba", 79: "An-Nazi'at", 80: "Abasa",
    81: "At-Takwir", 82: "Al-Infitar", 83: "Al-Mutaffifin", 84: "Al-Inshiqaq", 85: "Al-Buruj",
    86: "At-Tariq", 87: "Al-A'la", 88: "Al-Ghashiyah", 89: "Al-Fajr", 90: "Al-Balad",
    91: "Ash-Shams", 92: "Al-Layl", 93: "Ad-Duhaa", 94: "Ash-Sharh", 95: "At-Tin",
    96: "Al-Alaq", 97: "Al-Qadr", 98: "Al-Bayyinah", 99: "Az-Zalzalah", 100: "Al-Adiyat",
    101: "Al-Qari'ah", 102: "At-Takathur", 103: "Al-Asr", 104: "Al-Humazah", 105: "Al-Fil",
    106: "Quraysh", 107: "Al-Ma'un", 108: "Al-Kawthar", 109: "Al-Kafirun", 110: "An-Nasr",
    111: "Al-Masad", 112: "Al-Ikhlas", 113: "Al-Falaq", 114: "An-Nas",
}

# A few common alternate spellings not close enough to the canonical form above for the
# normalize_name_key() collapse (hyphens/apostrophes/spaces/case) to bridge on its own.
_EXTRA_ALIASES: dict[str, int] = {
    "yasin": 36, "ya-seen": 36, "yaseen": 36,
    "fatiha": 1, "alfatiha": 1,
    "ikhlaas": 112,
    "nisaa": 4,
    "imran": 3, "aleimran": 3, "aal-e-imran": 3, "aaleimran": 3,
    "inshirah": 94, "alinshirah": 94,
    "dahr": 76, "insaan": 76,
    "lahab": 111, "allahab": 111,
}

_NAME_TO_ID: dict[str, int] = {normalize_name_key(v): k for k, v in SURAH_NAMES.items()}
_NAME_TO_ID.update({normalize_name_key(k): v for k, v in _EXTRA_ALIASES.items()})


def surah_id_from_name(name: str) -> int | None:
    """Resolve a surah-name citation (any of the spellings above) to its 1-114 id.

    Returns None if the name isn't recognized -- callers must treat that as
    "unparseable", not silently guess a surah.
    """
    return _NAME_TO_ID.get(normalize_name_key(name))
