class RetailLangError(Exception):
    """Base class for all RetailLang errors."""

    def __init__(self, message: str, position: int = None, suggestion: str = None):
        super().__init__(message)
        self.message    = message
        self.position   = position
        self.suggestion = suggestion

    def __str__(self):
        parts = [self.message]
        if self.position is not None:
            parts.append(f"(position {self.position})")
        if self.suggestion:
            parts.append(f"— did you mean '{self.suggestion}'?")
        return " ".join(parts)


class LexError(RetailLangError):
    """Raised when the lexer encounters an unrecognised token."""
    pass


class ParseError(RetailLangError):
    """Raised when the parser encounters a structural grammar violation."""
    pass


class ExecutionError(RetailLangError):
    """Raised when the executor fails to process a valid AST."""
    pass


class FileLoadError(RetailLangError):
    """Raised when a referenced data file cannot be loaded."""
    pass


class ColumnNotFoundError(RetailLangError):
    """Raised when a referenced column does not exist in the loaded dataset."""

    def __init__(self, column: str, available: list[str]):
        available_str = ", ".join(available[:10])
        message = (
            f"Column '{column}' not found. "
            f"Available columns: {available_str}"
        )
        super().__init__(message)
        self.column    = column
        self.available = available