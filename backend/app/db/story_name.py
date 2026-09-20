import re
from pathlib import Path

_NUMBER_SUFFIX = re.compile(r"[\s_\-]*(\d+)$")
_SEPARATORS = re.compile(r"[\s_\-]+")


def parse_story_name(filename: str) -> tuple[str, int]:
    """Split a filename into (story name, number).

    "Space_Mage_2.docx" -> ("space_mage", 2). Spaces, underscores and hyphens
    all count as the same separator, so "Space Mage 2", "space-mage-2" and
    "Space_Mage_2" name the same story. An unnumbered file is number 0, so it
    sorts ahead of numbered ones in the same story.
    """
    stem = Path(filename).stem
    match = _NUMBER_SUFFIX.search(stem)
    base = stem[: match.start()] if match else stem
    name = _SEPARATORS.sub("_", base).strip("_").lower()
    if not name:
        return _SEPARATORS.sub("_", stem).strip("_").lower(), 0
    return name, int(match.group(1)) if match else 0
