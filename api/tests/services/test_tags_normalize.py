import pytest

from api.services.common.tags import (
    MAX_TAGS_PER_ENTITY,
    TAG_MAX_LENGTH,
    TagValidationError,
    normalize_tags,
)


def test_normalize_lowercases_trims_and_sorts() -> None:
    assert normalize_tags(["  Relic ", "Magic", "weapon"]) == ["magic", "relic", "weapon"]


def test_normalize_deduplicates_case_insensitively() -> None:
    assert normalize_tags(["Magic", "magic", "MAGIC"]) == ["magic"]


def test_normalize_drops_empty_and_whitespace_only() -> None:
    assert normalize_tags(["", "   ", "magic"]) == ["magic"]


def test_normalize_empty_list_returns_empty() -> None:
    assert normalize_tags([]) == []


def test_normalize_rejects_tag_over_max_length() -> None:
    too_long = "a" * (TAG_MAX_LENGTH + 1)
    with pytest.raises(TagValidationError):
        normalize_tags([too_long])


def test_normalize_accepts_tag_at_max_length() -> None:
    exactly_max = "a" * TAG_MAX_LENGTH
    assert normalize_tags([exactly_max]) == [exactly_max]


def test_normalize_rejects_too_many_tags() -> None:
    tags = [f"tag{index}" for index in range(MAX_TAGS_PER_ENTITY + 1)]
    with pytest.raises(TagValidationError):
        normalize_tags(tags)


def test_normalize_count_checked_after_dedup() -> None:
    # 25 raw entries that dedup to 1 must pass, not trip the count cap.
    assert normalize_tags(["magic"] * 25) == ["magic"]
