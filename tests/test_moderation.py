from moderation import analyze_message


def test_clean_message_is_not_flagged():
    result = analyze_message("Hey, how was your day today?")
    assert result["flagged"] is False
    assert result["crisis"] is False
    assert result["matched"] == []
    assert result["reason"] is None


def test_crisis_phrase_is_flagged_and_triggers_crisis_popup():
    result = analyze_message("I want to kill myself")
    assert result["flagged"] is True
    assert result["crisis"] is True
    assert "kill myself" in result["matched"]
    assert "Crisis keywords" in result["reason"]


def test_distress_phrase_is_flagged_but_not_crisis():
    result = analyze_message("I've been feeling really depressed lately")
    assert result["flagged"] is True
    assert result["crisis"] is False
    assert "depressed" in result["matched"]
    assert "Distress keywords" in result["reason"]


def test_matching_is_case_insensitive():
    result = analyze_message("I FEEL HOPELESS about everything")
    assert result["flagged"] is True
    assert "hopeless" in result["matched"]


def test_word_boundary_avoids_false_positive_substring():
    # "hopeless" is a distress keyword — make sure it doesn't fire just
    # because it's a substring of a longer, unrelated word.
    result = analyze_message("We studied hopelessness theory in psychology class")
    assert "hopeless" not in result["matched"]
    assert result["flagged"] is False
