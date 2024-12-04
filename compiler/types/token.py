class Token():
    def __init__(self, token_type: str, value: str) -> None:
        self.token_type: str = token_type
        self.value: str = value

    def __repr__(self) -> str:
        return f"<{self.token_type}, '{self.value}'>"