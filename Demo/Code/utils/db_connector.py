class DatabaseConnector:
    """Placeholder database connector for future persistence work."""

    def __init__(self, dsn: str = "") -> None:
        self.dsn = dsn
        self.connected = False

    def connect(self) -> "DatabaseConnector":
        """Mark the placeholder connector as connected."""
        self.connected = True
        return self

    def close(self) -> None:
        """Close the placeholder connector."""
        self.connected = False
