from typing import TypedDict


DEFAULT_MIN_HEADLINE_CHARS = 20
DEFAULT_MAX_HEADLINE_CHARS = 180
DEFAULT_REQUIRED_PHRASE = "florida man"


class GeneratorQualityStats(TypedDict):
    input_count: int
    kept_count: int
    invalid_dropped: int
    duplicates_dropped: int


def normalize_headline(text: str) -> str:
    return " ".join(text.split()).strip()


def is_plausible_headline(
    text: str,
    min_chars: int = DEFAULT_MIN_HEADLINE_CHARS,
    max_chars: int = DEFAULT_MAX_HEADLINE_CHARS,
    required_phrase: str = DEFAULT_REQUIRED_PHRASE,
) -> bool:
    if not isinstance(text, str):
        return False

    clean = normalize_headline(text)
    if len(clean) < min_chars or len(clean) > max_chars:
        return False

    if required_phrase and required_phrase.lower() not in clean.lower():
        return False

    return True


def apply_quality_filters(
    headlines: list[str],
    min_chars: int = DEFAULT_MIN_HEADLINE_CHARS,
    max_chars: int = DEFAULT_MAX_HEADLINE_CHARS,
    required_phrase: str = DEFAULT_REQUIRED_PHRASE,
) -> tuple[list[str], GeneratorQualityStats]:
    seen: set[str] = set()
    kept: list[str] = []

    stats: GeneratorQualityStats = {
        "input_count": len(headlines),
        "kept_count": 0,
        "invalid_dropped": 0,
        "duplicates_dropped": 0,
    }

    for raw in headlines:
        if not is_plausible_headline(
            raw,
            min_chars=min_chars,
            max_chars=max_chars,
            required_phrase=required_phrase,
        ):
            stats["invalid_dropped"] += 1
            continue

        clean = normalize_headline(raw)
        key = clean.lower()

        if key in seen:
            stats["duplicates_dropped"] += 1
            continue

        seen.add(key)
        kept.append(clean)

    stats["kept_count"] = len(kept)
    return kept, stats
