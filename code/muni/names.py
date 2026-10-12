"""Name normalization and government-class inference.

Plain-language header: the three sources spell the same government differently
("Town of Colonie", "COLONIE", "Colonie (T)"). This file turns every spelling
into one comparable key plus a class (city, town, village, county, school
district). Technical file; you do not need to open it.
"""
import re

CLASSES = ("city", "town", "village", "county", "school district", "fire district")

_ABBREV = [
    (r"\bst\.?\b", "saint"), (r"\bmt\.?\b", "mount"), (r"\bft\.?\b", "fort"),
    (r"\bpt\.?\b", "point"), (r"\bhts\b", "heights"), (r"\be\.?\b", "east"),
    (r"\bw\.?\b", "west"), (r"\bn\.?\b", "north"), (r"\bs\.?\b", "south"),
]
_SCHOOL = [r"\bcentral high school district\b", r"\bcentral school district\b", r"\bunion free school district\b",
           r"\bcity school district\b", r"\bschool district\b", r"\bc\.?s\.?d\.?\b",
           r"\bu\.?f\.?s\.?d\.?\b", r"\bsd\b", r"\bcsd\b", r"\bufsd\b",
           r"\bpublic schools?\b", r"\bschools?\b", r"\bboard of education\b"]
_CLASS_WORDS = [r"\btown of\b", r"\bcity of\b", r"\bvillage of\b", r"\bcounty of\b",
                r"\bcounty\b", r"\b\((t|c|v)\)", r"\btown\b", r"\bcity\b", r"\bvillage\b",
                r"\binc\.?\b"]


def infer_class(name: str) -> str | None:
    """Guess the class of government from a free-text name."""
    s = (name or "").lower()
    if re.search(r"school|\bcsd\b|\bufsd\b|\bsd\b|board of education|boces", s):
        return "school district"
    if re.search(r"fire district|\bfd\b", s):
        return "fire district"
    if re.search(r"\bvillage\b|\(v\)", s):
        return "village"
    if re.search(r"\btown\b|\(t\)", s):
        return "town"
    if re.search(r"\bcounty\b", s):
        return "county"
    if re.search(r"\bcity\b|\(c\)", s):
        return "city"
    return None


def normalize_class(label: str) -> str | None:
    """Map a source's class label (e.g. 'Village', 'SCHOOL DISTRICT') to CLASSES."""
    s = (label or "").strip().lower()
    for c in CLASSES:
        if s.startswith(c.split()[0]):
            return c
    if s.startswith("school"):
        return "school district"
    return None


def name_key(name: str) -> str:
    """Comparable key: lowercase, class words and punctuation removed."""
    s = (name or "").lower().replace("&", " and ")
    for pat in _SCHOOL + _CLASS_WORDS:
        s = re.sub(pat, " ", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    for pat, rep in _ABBREV:
        s = re.sub(pat, rep, s)
    return re.sub(r"\s+", " ", s).strip()


def county_key(name: str) -> str:
    s = (name or "").lower().replace("county", "")
    s = re.sub(r"[^a-z ]", " ", s)
    s = s.replace("saint ", "st ").replace("st. ", "st ")
    return re.sub(r"\s+", " ", s).strip()
