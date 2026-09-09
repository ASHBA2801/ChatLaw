from conversation.speech_cleaner import clean_speech_text, number_to_indian_words


def test_number_to_indian_words():
    assert number_to_indian_words(18000) == "eighteen thousand"
    assert number_to_indian_words(250000) == "two lakh fifty thousand"


def test_clean_speech_text_citations_and_urls():
    raw = "Under Section 303(2) BNS [1], theft carries punishment [SOURCE 2]. Visit https://example.com for details."
    cleaned = clean_speech_text(raw)
    assert "[1]" not in cleaned
    assert "[SOURCE 2]" not in cleaned
    assert "https://" not in cleaned
    assert "Section 303, sub-section 2 of the Bharatiya Nyaya Sanhita" in cleaned


def test_clean_speech_currency():
    raw = "The monthly rent is ₹18,000 and deposit is ₹50,000."
    cleaned = clean_speech_text(raw)
    assert "eighteen thousand rupees" in cleaned
    assert "fifty thousand rupees" in cleaned
