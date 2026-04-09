"""
Unit tests for the NLP preprocessing pipeline.
Run with: pytest backend/tests/test_preprocessor.py -v
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.nlp.preprocessor import preprocess


class TestAdversarialNormalization:
    def test_zero_to_o(self):
        result = preprocess("Fr.ee M0ney", stem=False, remove_stops=False)
        assert "money" in result

    def test_at_sign_to_a(self):
        result = preprocess("s@le now", stem=False, remove_stops=False)
        assert "sale" in result

    def test_dollar_sign_to_s(self):
        result = preprocess("free ca$h", stem=False, remove_stops=False)
        assert "cash" in result

    def test_exclamation_to_i(self):
        # "w!n" → "win"
        result = preprocess("w!n a prize", stem=False, remove_stops=False)
        assert "win" in result


class TestCleaning:
    def test_lowercase(self):
        result = preprocess("HELLO WORLD", stem=False, remove_stops=False)
        assert result == result.lower()

    def test_url_removed(self):
        result = preprocess("Click here http://spam.com to win", stem=False, remove_stops=False)
        assert "http" not in result
        assert "spam" not in result or "com" not in result

    def test_phone_number_removed(self):
        result = preprocess("Call us at +1-800-555-1234 now", stem=False, remove_stops=False)
        assert "1234" not in result
        assert "800" not in result

    def test_special_chars_removed(self):
        result = preprocess("Hello!!! How are you???", stem=False, remove_stops=False)
        assert "!" not in result
        assert "?" not in result

    def test_empty_string(self):
        assert preprocess("") == ""

    def test_whitespace_only(self):
        assert preprocess("   ") == ""

    def test_non_string(self):
        assert preprocess(None) == ""


class TestStopWordRemoval:
    def test_removes_common_stopwords(self):
        result = preprocess("this is a very good message", stem=False, remove_stops=True)
        for stop in ["this", "is", "a", "very"]:
            assert stop not in result.split()

    def test_keeps_meaningful_words(self):
        result = preprocess("win free prize money", stem=False, remove_stops=True)
        assert "win" in result
        assert "free" in result
        assert "prize" in result
        assert "money" in result


class TestStemming:
    def test_stemming_applied(self):
        result = preprocess("running wins prizes", stem=True, remove_stops=False)
        # PorterStemmer: running→run, wins→win, prizes→prize
        assert "run" in result
        assert "win" in result

    def test_no_stemming(self):
        result = preprocess("running", stem=False, remove_stops=False)
        assert "running" in result


class TestBatch:
    def test_batch_processing(self):
        from backend.nlp.preprocessor import preprocess_batch
        messages = ["Free money now!", "Meeting at 5pm", ""]
        results = preprocess_batch(messages)
        assert len(results) == 3
        assert results[2] == ""
