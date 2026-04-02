from agents.tools.generator_quality import apply_quality_filters
from agents.tools.generator_quality import is_plausible_headline
from agents.tools.generator_quality import normalize_headline


def test_normalize_headline_compacts_whitespace():
    assert (
        normalize_headline("  Florida Man   does   a thing  ")
        == "Florida Man does a thing"
    )


def test_is_plausible_headline_requires_phrase_and_length():
    assert is_plausible_headline("Florida man does a believable thing")
    assert not is_plausible_headline("Too short")
    assert not is_plausible_headline("A normal headline without phrase")


def test_apply_quality_filters_drops_invalid_and_duplicates():
    headlines = [
        "Florida Man does one thing",
        "  florida man does one thing  ",
        "No keyword headline",
        "Florida Man does two things",
    ]

    kept, stats = apply_quality_filters(headlines)

    assert kept == [
        "Florida Man does one thing",
        "Florida Man does two things",
    ]
    assert stats["input_count"] == 4
    assert stats["kept_count"] == 2
    assert stats["invalid_dropped"] == 1
    assert stats["duplicates_dropped"] == 1
