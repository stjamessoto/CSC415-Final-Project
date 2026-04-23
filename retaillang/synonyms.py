from __future__ import annotations


# ------------------------------------------------------------------
# Canonical keyword synonyms
# Each key is the canonical form; values are accepted alternatives.
# ------------------------------------------------------------------

KEYWORD_SYNONYMS: dict[str, list[str]] = {
    "load":        ["import", "read", "open"],
    "compute":     ["calculate", "find", "get"],
    "filter":      ["where", "only", "select"],
    "generate":    ["create", "make", "plot", "draw", "build", "show"],
    "sort":        ["order", "rank"],
    "ascending":   ["asc", "lowest first"],
    "descending":  ["desc", "highest first"],
    "average":     ["avg", "mean"],
    "total":       ["sum"],
    "maximum":     ["max"],
    "minimum":     ["min"],
    "by":          ["grouped by", "per", "for each"],
    "and":         ["then", "also"],
    "table":       ["tables"],
    "chart":       ["graph", "plot", "visualization", "viz"],
}

# ------------------------------------------------------------------
# Column / metric synonyms
# Maps common business terms to a canonical column name group.
# The executor uses this to fuzzy-match user column references
# against the actual DataFrame columns.
# ------------------------------------------------------------------

COLUMN_SYNONYMS: dict[str, list[str]] = {
    "revenue":  ["sales", "income", "turnover", "earnings", "receipts"],
    "profit":   ["margin", "net", "gain", "earnings"],
    "units":    ["quantity", "qty", "items", "pieces", "count"],
    "cost":     ["expense", "spend", "expenditure", "outlay"],
    "orders":   ["transactions", "purchases", "sales"],
    "customer": ["client", "buyer", "shopper"],
    "product":  ["item", "good", "sku"],
    "region":   ["area", "zone", "territory", "location"],
    "date":     ["day", "time", "period"],
    "total":    ["sum", "grand total", "subtotal"],
    "discount": ["reduction", "saving", "offer"],
    "category": ["type", "group", "class", "department"],
    "segment":  ["tier", "group", "division"],
}

# ------------------------------------------------------------------
# Reverse lookup: alias → canonical
# ------------------------------------------------------------------

_KEYWORD_REVERSE: dict[str, str] = {}
for canonical, aliases in KEYWORD_SYNONYMS.items():
    for alias in aliases:
        _KEYWORD_REVERSE[alias.lower()] = canonical

_COLUMN_REVERSE: dict[str, str] = {}
for canonical, aliases in COLUMN_SYNONYMS.items():
    for alias in aliases:
        _COLUMN_REVERSE[alias.lower()] = canonical


def resolve_keyword(word: str) -> str:
    """
    Return the canonical keyword for a given word, or
    return the word unchanged if no synonym mapping exists.
    """
    return _KEYWORD_REVERSE.get(word.lower(), word.lower())


def resolve_column(word: str) -> str:
    """
    Return the canonical column name for a given word, or
    return the word unchanged if no synonym mapping exists.
    """
    return _COLUMN_REVERSE.get(word.lower(), word.lower())


def suggest_keyword(word: str, threshold: int = 2) -> str | None:
    """
    Return the closest known keyword to the given word using
    Levenshtein edit distance. Returns None if no close match found.
    """
    all_keywords = (
        list(KEYWORD_SYNONYMS.keys()) +
        list(_KEYWORD_REVERSE.keys())
    )
    word_lower = word.lower()
    best       = None
    best_dist  = threshold + 1

    for kw in all_keywords:
        dist = _levenshtein(word_lower, kw)
        if dist < best_dist:
            best_dist = dist
            best      = _KEYWORD_REVERSE.get(kw, kw)

    return best


def suggest_column(word: str, known_columns: list[str], threshold: int = 2) -> str | None:
    """
    Return the closest known column name to the given word using
    Levenshtein edit distance against the actual DataFrame columns.
    Returns None if no close match found.
    """
    word_lower = word.lower()
    best       = None
    best_dist  = threshold + 1

    candidates = known_columns + list(_COLUMN_REVERSE.keys())

    for col in candidates:
        dist = _levenshtein(word_lower, col.lower())
        if dist < best_dist:
            best_dist = dist
            best      = col

    return best


def _levenshtein(a: str, b: str) -> int:
    """Compute the Levenshtein edit distance between two strings."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)

    prev = list(range(len(b) + 1))

    for i, ca in enumerate(a, 1):
        curr = [i]
        for j, cb in enumerate(b, 1):
            curr.append(min(
                prev[j] + 1,
                curr[j - 1] + 1,
                prev[j - 1] + (0 if ca == cb else 1),
            ))
        prev = curr

    return prev[len(b)]