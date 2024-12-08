from typing import List, Tuple, Iterator

from .types import Token, TokenType
import re

class Lexer():
    TOKEN_SPECS: List[Tuple[str, str]] = [
        ("reserved", r'\b(boolean|class|extends|public|static|void|main|String|return|int|if|else|while|System\.out\.println|length|true|false|this|new|null)\b'),
        ("identifier", r'[a-zA-Z_][a-zA-Z0-9_]*'),
        ("number", r'\d+'),
        ("operator", r'==|!=|<=|>=|<|>|\+|-|\*|&&|!|='),
        ("punctuation", r'[(){}\[\];.,]'),
        ("whitespace", r'[ \t\r\f\n]+'),
        ("comment", r'//.*?$|/\*.*?\*/'),
        ("mistake", r'.'),
    ]

    FULL_REGEX: str = '|'.join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_SPECS)

    def __init__(self, text: str) -> None:
        self.text: str = text
        self.tokens: List[Token] = []
        self.current_position: int = 0
        self.regex = re.compile(self.FULL_REGEX)

    def tokenize(self) -> None:
        for match in re.finditer(self.FULL_REGEX, self.text, re.DOTALL | re.MULTILINE):
            token_type = match.lastgroup
            token_value = match.group()

            if token_type == "branco" or token_type == "comentario":
                continue
            elif token_type == "erro":
                raise SyntaxError(f"Token desconhecido: {token_value}")
            
            self.tokens.append(Token(TokenType(token_type), token_value))

    def get_tokens(self) -> List[Token]:
        if not self.tokens:
            self.tokens = list(self._generate_tokens())
        return self.tokens
    
    def __iter__(self) -> Iterator[Token]:
        return