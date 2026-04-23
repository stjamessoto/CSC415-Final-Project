from __future__ import annotations
from enum       import Enum, auto
from retaillang.errors   import LexError
from retaillang.synonyms import resolve_keyword, suggest_keyword


class TokenType(Enum):
    KEYWORD    = auto()
    IDENTIFIER = auto()
    FILENAME   = auto()
    STRING     = auto()
    NUMBER     = auto()
    COMPARATOR = auto()
    PUNCT      = auto()
    ARTICLE    = auto()
    EOF        = auto()


class Token:
    def __init__(self, type_: TokenType, value: str, position: int = 0):
        self.type     = type_
        self.value    = value
        self.position = position

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, pos={self.position})"


# ------------------------------------------------------------------
# Keyword sets
# ------------------------------------------------------------------

KEYWORDS = {
    "load", "import", "read", "open",
    "compute", "calculate", "find", "get",
    "filter", "where", "only", "select",
    "generate", "create", "make", "plot",
    "draw", "build", "show",
    "sort", "order", "rank",
    "pivot", "table",
    "bar", "line", "pie", "scatter", "histogram",
    "chart", "graph",
    "by", "per", "as", "of", "with",
    "and", "or", "then", "also",
    "total", "sum", "average", "avg", "mean",
    "count", "max", "maximum", "min", "minimum",
    "ascending", "asc", "descending", "desc",
    "between", "in", "not",
    "grouped", "for", "each",
    "comparing", "comparing",
    "titled", "title",
    "rows", "columns", "values",
    "highest", "lowest", "first",
    "number",
    "is",
    "at", "least", "most",
    "greater", "less", "than",
}

ARTICLES = {"a", "an", "the", "some"}

COMPARATORS = {"=", "==", "!=", ">", "<", ">=", "<="}

FILE_EXTENSIONS = {".csv", ".xlsx", ".json", ".parquet", ".xls"}

MULTI_WORD_COMPARATORS = {
    "greater than": ">",
    "less than":    "<",
    "at least":     ">=",
    "at most":      "<=",
    "is not":       "!=",
    "not equal":    "!=",
}

MULTI_WORD_KEYWORDS = {
    "grouped by",
    "for each",
    "highest first",
    "lowest first",
}


class Lexer:
    def __init__(self, source: str):
        self._source  = source
        self._pos     = 0
        self._tokens: list[Token] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def tokenize(self) -> list[Token]:
        self._tokens = []
        self._pos    = 0
        words        = self._split_source()

        i = 0
        while i < len(words):
            word, pos = words[i]

            # Skip empty
            if not word:
                i += 1
                continue

            # Try multi-word comparator (2 words)
            if i + 1 < len(words):
                two = f"{word} {words[i+1][0]}".lower()
                if two in MULTI_WORD_COMPARATORS:
                    self._tokens.append(Token(
                        TokenType.COMPARATOR,
                        MULTI_WORD_COMPARATORS[two],
                        pos,
                    ))
                    i += 2
                    continue

            # Try multi-word keyword (2 words)
            if i + 1 < len(words):
                two = f"{word} {words[i+1][0]}".lower()
                if two in MULTI_WORD_KEYWORDS:
                    canonical = resolve_keyword(two)
                    self._tokens.append(Token(TokenType.KEYWORD, canonical, pos))
                    i += 2
                    continue

            token = self._classify(word, pos)
            if token.type != TokenType.ARTICLE:
                self._tokens.append(token)
            i += 1

        self._tokens.append(Token(TokenType.EOF, "", self._pos))
        return self._tokens

    def format_token_stream(self) -> str:
        if not self._tokens:
            return "No tokens — call tokenize() first."
        lines = []
        for tok in self._tokens:
            lines.append(
                f"{tok.type.name:<12} {tok.value!r:<30} pos={tok.position}"
            )
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Source splitter
    # ------------------------------------------------------------------

    def _split_source(self) -> list[tuple[str, int]]:
        """
        Split source into (word, position) pairs, preserving
        quoted strings, filenames, comparators, and punctuation.
        """
        words = []
        i     = 0
        src   = self._source

        while i < len(src):
            c = src[i]

            # Whitespace
            if c.isspace():
                i += 1
                continue

            # Quoted string
            if c in ('"', "'"):
                j     = i + 1
                quote = c
                while j < len(src) and src[j] != quote:
                    j += 1
                words.append((src[i+1:j], i))
                i = j + 1
                continue

            # Two-char comparators
            if c in (">", "<", "!", "=") and i + 1 < len(src) and src[i+1] == "=":
                words.append((src[i:i+2], i))
                i += 2
                continue

            # Single-char comparator or punctuation
            if c in ("=", ">", "<", ",", "(", ")"):
                words.append((c, i))
                i += 1
                continue

            # Word or filename
            j = i
            while j < len(src) and not src[j].isspace() and src[j] not in (
                "=", ">", "<", ",", "(", ")", '"', "'"
            ):
                j += 1
            token_str = src[i:j]
            words.append((token_str, i))
            i = j

        return words

    # ------------------------------------------------------------------
    # Token classifier
    # ------------------------------------------------------------------

    def _classify(self, word: str, pos: int) -> Token:
        # Punctuation must be checked before rstrip so "," → "" doesn't fall through
        if word in (",", "(", ")"):
            return Token(TokenType.PUNCT, word, pos)

        lower = word.lower().rstrip(",")

        # Article — discard
        if lower in ARTICLES:
            return Token(TokenType.ARTICLE, lower, pos)

        # Comparator
        if lower in COMPARATORS:
            return Token(TokenType.COMPARATOR, lower, pos)

        # Filename (contains dot + known extension)
        if self._is_filename(word):
            return Token(TokenType.FILENAME, word, pos)

        # Quoted string value (already stripped of quotes by splitter)
        if self._is_numeric(word):
            return Token(TokenType.NUMBER, word, pos)

        # Known keyword or synonym
        if lower in KEYWORDS:
            canonical = resolve_keyword(lower)
            return Token(TokenType.KEYWORD, canonical, pos)

        # Identifier — column name or value
        if self._is_identifier(word):
            return Token(TokenType.IDENTIFIER, lower, pos)

        # String literal used as a value (e.g. West, Electronics)
        if word.replace("-", "").replace("_", "").isalnum():
            return Token(TokenType.STRING, word, pos)

        # Unknown — suggest and raise
        suggestion = suggest_keyword(lower)
        raise LexError(
            f"Unknown token '{word}'",
            position=pos,
            suggestion=suggestion,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _is_filename(self, word: str) -> bool:
        lower = word.lower()
        return any(lower.endswith(ext) for ext in FILE_EXTENSIONS)

    def _is_numeric(self, word: str) -> bool:
        try:
            float(word)
            return True
        except ValueError:
            return False

    def _is_identifier(self, word: str) -> bool:
        return (
            word.replace("_", "").replace("-", "").isalnum()
            and not word[0].isdigit()
        )