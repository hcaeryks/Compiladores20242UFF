from .types import Token, Node
from typing import List

class Parser():
    def __init__(self, tokens: List[Token]) -> None:
        self.tokens = [token for token in tokens if token.token_type != "whitespace" and token.token_type != "comment"]
        self.index = 0

    def get_token(self) -> Token:
        return self.tokens[self.index] if self.index < len(self.tokens) else None

    def consume(self, expected_type: str, expected_value: str = None) -> Token:
        token = self.get_token()
        if token and token.token_type == expected_type and (expected_value is None or token.value == expected_value):
            self.index += 1
            return token
        else:
            expected_desc = f"{expected_type} ('{expected_value}')" if expected_value else f"{expected_type}"
            raise Exception(f"Expected {expected_desc}, got {repr(token)} @ {self.index}")
        
    def parse(self):
        return self.parse_PROG()
        
    def parse_PROG(self):
        main = self.parse_MAIN()
        classes = []
        while self.get_token():
            classes.append(self.parse_CLASSE())
        return Node("PROG", [main] + classes)

    def parse_MAIN(self):
        self.consume("reserved", "class")
        class_name = self.consume("identifier")
        self.consume("punctuation", "{")
        self.consume("reserved", "public")
        self.consume("reserved", "static")
        self.consume("reserved", "void")
        self.consume("reserved", "main")
        self.consume("punctuation", "(")
        self.consume("reserved", "String")
        self.consume("punctuation", "[")
        self.consume("punctuation", "]")
        parameter = self.consume("identifier")
        self.consume("punctuation", ")")
        self.consume("punctuation", "{")
        commands = []
        while self.get_token().value != "}":
            commands.append(self.parse_CMD())
        self.consume("punctuation", "}")
        self.consume("punctuation", "}")
        return Node("MAIN", [class_name] + [parameter] + commands)

    def parse_CLASSE(self):
        pass

    def parse_VAR(self):
        pass

    def parse_METODO(self):
        pass

    def parse_PARAMS(self):
        pass

    def parse_TIPO(self):
        pass

    def parse_CMD(self):
        pass

    def parse_EXP(self):
        pass

    def parse_REXP(self):
        pass

    def parse_AEXP(self):
        pass

    def parse_MEXP(self):
        pass

    def parse_SEXP(self):
        pass

    def parse_PEXP(self):
        pass

    def parse_EXPS(self):
        pass