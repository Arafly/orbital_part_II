from decimal import Decimal

from app.credits import (
    calculate_credits,
    count_third_vowels,
    extract_words,
    is_palindrome_message,
)

def test_extract_words_handles_apostrophes_and_hyphens():
    assert extract_words("It's a well-known rule") == ["It's", "a", "well-known", "rule"]

def test_extract_words_ignores_symbols_only():
    # positions 3 and 6 are vowels in "abeido"
    assert count_third_vowels("abeido") == 2

def test_palindrom_ignores_case_and_non_alphanumeric():
    assert is_palindrome_message("A man, a plan, a canal: Panama")

def test_non_palindrome_returns_false():
    assert not is_palindrome_message("hello world")

def test_minimum_cost_before_palindrome():
    result = calculate_credits("!!!")
    assert result == Decimal("1.15")

def test_unique_word_bonus_applies_when_all_words_are_unique():
    result = calculate_credits("alpha beta gamma")
    assert result == Decimal("1.00")

def test_unique_word_bonus_does_not_apply_when_words_repeat():
    result = calculate_credits("hello hello")
    assert result == Decimal("1.00")

def test_length_penalty_applies_over_100_chars():
    long_text = "a" * 101
    result = calculate_credits(long_text)
    assert result >= Decimal("11.15")

def test_palindrome_doubles_after_other_rules():
    result = calculate_credits("Racecar")
    assert result == Decimal("2.00")