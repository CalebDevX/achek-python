class AchekConnectError(Exception):
    """Raised when the Achek Connect API returns an error response."""

    def __init__(self, message: str, status_code: int = 0, code: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.code = code

    def __repr__(self) -> str:
        return f"AchekConnectError(message={str(self)!r}, status_code={self.status_code}, code={self.code!r})"
