from __future__ import annotations

import re
from decimal import Decimal, ROUND_HALF_UP

WORD_RE = re.compile(r"[A-Za-z]+(?:['-][A-Za-z]+)*")
VOWELS = set("AEIOUaeiou")

BASE_COST = Decimal("1")
CHAR_COST = Decimal("0.05")
SHORT_WORD_COST = Decimal("0.1")
MEDIUM_WORD_COST = Decimal("0.2")
LONG_WORD_COST = Decimal("0.3")
THIRD_VOWEL_COST = Decimal("0.3")
LENGTH_PENALTY = Decimal("5")
UNIQUE_WORD_BONUS = Decimal("2")
TWO_DP = Decimal("0.01")

def extract_words(text: str) -> list[str]:
    return WORD_RE.findall(text)

def count_third_vowels(text: str) -> int:
    # 3rd, 6th, 9th... characters => indexes 2, 5, 8...
    return sum(1 for i in range(2, len(text), 3) if text[i] in VOWELS)

def is_palindrome_message(text: str) -> bool:
    normalized = "".join(ch.lower() for ch in text if ch.isalnum())
    return bool(normalized) and normalized == normalized[::-1]

def quantize_2dp(value: Decimal) -> Decimal:
    return value.quantize(TWO_DP, rounding=ROUND_HALF_UP)

def calculate_credits(text: str) -> Decimal:
    total = BASE_COST
    words = extract_words(text)

    # Word length multipliers
    for word in words:
        word_len = len(word)
        if 1 <= word_len <= 3:
            total += SHORT_WORD_COST
        elif 4 <= word_len <= 7:
            total += MEDIUM_WORD_COST
        else:
            total += LONG_WORD_COST

    # Per-character cost
    total += Decimal(len(text)) * CHAR_COST

    # Third vowel
    total += Decimal(count_third_vowels(text)) * THIRD_VOWEL_COST

    # Length penalty
    if len(text) > 100:
        total += LENGTH_PENALTY

    # Unique word bonus
    if words:
        total -= UNIQUE_WORD_BONUS

    # Minimum cost before palindrome rule
    if total < BASE_COST:
        total = BASE_COST

    # Palindrome doubles after all other rules
    if is_palindrome_message(text):
        total *= Decimal("2")
    return quantize_2dp(total)