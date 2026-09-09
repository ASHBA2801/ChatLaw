from conversation.language_detector import detect_language


def test_detect_pure_tamil():
    res = detect_language("என் நிலத்தை என் சகோதரர் ஆக்கிரமித்துள்ளார். நான் என்ன செய்யலாம்?")
    assert res["detected_language"] == "ta"
    assert res["confidence"] >= 0.95
    assert res["is_code_switched"] is False


def test_detect_pure_hindi():
    res = detect_language("मेरे किरायेदार ने तीन महीने से किराया नहीं दिया है। मैं क्या कर सकता हूँ?")
    assert res["detected_language"] == "hi"
    assert res["confidence"] >= 0.95
    assert res["is_code_switched"] is False


def test_detect_pure_telugu():
    res = detect_language("నా భూమిని నా సోదరుడు ఆక్రమించాడు. నేను ఏమి చేయగలను?")
    assert res["detected_language"] == "te"
    assert res["confidence"] >= 0.95
    assert res["is_code_switched"] is False


def test_detect_english():
    res = detect_language("What are my legal rights if my landlord refuses to return my deposit?")
    assert res["detected_language"] == "en"
    assert res["confidence"] >= 0.95
    assert res["is_code_switched"] is False


def test_code_switched_tamil():
    res = detect_language("என் tenant மூன்று months rent கொடுக்கவில்லை.")
    assert res["detected_language"] == "ta"
    assert res["is_code_switched"] is True
    assert res["confidence"] >= 0.95


def test_code_switched_hindi():
    res = detect_language("Mere tenant rent pay नहीं कर रहा.")
    assert res["detected_language"] == "hi"
    assert res["is_code_switched"] is True
    assert res["confidence"] >= 0.95


def test_directives():
    res_en = detect_language("இது பற்றி தமிழில் விளக்கம் கொடுத்தீர்கள், please answer in English now.")
    assert res_en["detected_language"] == "en"
    assert res_en["directive_applied"] is True

    res_ta = detect_language("Explain this situation in Tamil: தமிழில் பதில் சொல்லுங்கள்")
    assert res_ta["detected_language"] == "ta"
    assert res_ta["directive_applied"] is True

    res_hi = detect_language("हिंदी में समझाइए please")
    assert res_hi["detected_language"] == "hi"
    assert res_hi["directive_applied"] is True

    res_te = detect_language("తెలుగులో చెప్పండి")
    assert res_te["detected_language"] == "te"
    assert res_te["directive_applied"] is True


def test_conversation_memory():
    res1 = detect_language("Tamil Nadu", prior_language="ta")
    assert res1["detected_language"] == "ta"

    res2 = detect_language("₹18,000", prior_language="ta")
    assert res2["detected_language"] == "ta"

    res3 = detect_language("Yes", prior_language="hi")
    assert res3["detected_language"] == "hi"


def test_language_switch():
    res = detect_language("What are my rights?", prior_language="ta")
    assert res["detected_language"] == "en"

    res_ta = detect_language("இதை இன்னும் எளிமையாக விளக்குங்கள்", prior_language="en")
    assert res_ta["detected_language"] == "ta"
