TAG_MAX_LENGTH = 30
MAX_TAGS_PER_ENTITY = 20


class TagValidationError(Exception):
    pass


def normalize_tags(raw: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for candidate in raw:
        tag = candidate.strip().lower()
        if not tag:
            continue
        if len(tag) > TAG_MAX_LENGTH:
            raise TagValidationError(f"Tag exceeds {TAG_MAX_LENGTH} characters: {tag!r}")
        if tag not in seen:
            seen.add(tag)
            normalized.append(tag)
    if len(normalized) > MAX_TAGS_PER_ENTITY:
        raise TagValidationError(f"At most {MAX_TAGS_PER_ENTITY} tags are allowed")
    return sorted(normalized)
