import re
from pathlib import Path

_NUMBER_SUFFIX = re.compile(r"[\s_\-]*(\d+)$")


def parse_story_name(filename: str) -> tuple[str, int]:
    """Split a filename into (story name, number).

    "Space_Mage_2.docx" -> ("space_mage", 2). An unnumbered file is number 0,
    so it sorts ahead of numbered ones in the same story.
    """
    stem = Path(filename).stem
    match = _NUMBER_SUFFIX.search(stem)
    base = stem[: match.start()].strip(" _-") if match else stem
    if not base:
        return stem.lower(), 0
    return base.lower(), int(match.group(1)) if match else 0
