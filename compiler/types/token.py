from compiler.types.TokenType import TokenType

class Token():
    def __init__(self, token_type: TokenType, value: str) -> None:
        self.token_type: TokenType = token_type
        self.value: str = value

    def __repr__(self) -> str:
        return f"<{self.token_type.value}, '{self.value}'>"