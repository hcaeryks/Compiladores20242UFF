from .types import Token, Node, TokenType
from typing import List

class Parser():
    def __init__(self, tokens: List[Token]) -> None:
        self.tokens = [token for token in tokens if token.token_type is not TokenType.WHITESPACE and token.token_type is not TokenType.COMMENT]
        self.index = 0

    def get_token(self) -> Token:
        return self.tokens[self.index] if self.index < len(self.tokens) else None

    def consume(self, expected_type: TokenType, expected_value: str = None) -> Token:
        token = self.get_token()
        if token and token.token_type is expected_type and (expected_value is None or token.value == expected_value.value):
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
        self.consume(TokenType.RESERVED, TokenType.CLASS)
        class_name = Node(TokenType.ID, [self.consume(TokenType.ID)])
        self.consume(TokenType.PUNCTUATION, TokenType.OPEN_BRACES)
        self.consume(TokenType.RESERVED, TokenType.PUBLIC)
        self.consume(TokenType.RESERVED, TokenType.STATIC)
        self.consume(TokenType.RESERVED, TokenType.VOID)
        self.consume(TokenType.RESERVED, TokenType.MAIN)
        self.consume(TokenType.PUNCTUATION, TokenType.OPEN_PARENTHESES)
        self.consume(TokenType.RESERVED, TokenType.STRING)
        self.consume(TokenType.PUNCTUATION, TokenType.OPEN_BRACKET)
        self.consume(TokenType.PUNCTUATION, TokenType.CLOSE_BRACKET)
        parameter = Node(TokenType.ID, [self.consume(TokenType.ID)])
        self.consume(TokenType.PUNCTUATION, TokenType.CLOSE_PARENTHESES)
        self.consume(TokenType.PUNCTUATION, TokenType.OPEN_BRACES)
        commands = []
        while self.get_token().value != TokenType.CLOSE_BRACES.value:
            commands.append(self.parse_CMD())
        self.consume(TokenType.PUNCTUATION, TokenType.CLOSE_BRACES)
        self.consume(TokenType.PUNCTUATION, TokenType.CLOSE_BRACES)
        return Node("MAIN", [class_name, parameter] + commands)

    def parse_CLASSE(self):
        self.consume(TokenType.RESERVED, TokenType.CLASS)
        class_name = Node(TokenType.ID, [self.consume(TokenType.ID)])
        parent_class = None
        if self.get_token().value == TokenType.EXTENDS.value:
            self.consume(TokenType.RESERVED, TokenType.EXTENDS)
            parent_class = Node(TokenType.ID, [self.consume(TokenType.ID)])
        self.consume(TokenType.PUNCTUATION, TokenType.OPEN_BRACES)
        variables = []
        while self.get_token().value not in [TokenType.PUBLIC.value, TokenType.CLOSE_BRACES.value]:
            variables.append(self.parse_VAR())
        methods = []
        while self.get_token().value != TokenType.CLOSE_BRACES.value:
            methods.append(self.parse_METODO())
        self.consume(TokenType.PUNCTUATION, TokenType.CLOSE_BRACES)
        return Node("CLASSE", [class_name, parent_class] + variables + methods)

    def parse_VAR(self):
        tipo = self.parse_TIPO()
        identifier = Node(TokenType.ID, [self.consume(TokenType.ID)])
        self.consume(TokenType.PUNCTUATION, TokenType.SEMICOLON)
        return Node("VAR", [tipo, identifier])

    def parse_METODO(self):
        self.consume(TokenType.RESERVED, TokenType.PUBLIC)
        tipo = self.parse_TIPO()
        identifier = Node(TokenType.ID, [self.consume(TokenType.ID)])
        self.consume(TokenType.PUNCTUATION, TokenType.OPEN_PARENTHESES)
        params = self.parse_PARAMS() if self.get_token().value != TokenType.CLOSE_PARENTHESES.value else Node("PARAMS", [])
        self.consume(TokenType.PUNCTUATION, TokenType.CLOSE_PARENTHESES)
        self.consume(TokenType.PUNCTUATION, TokenType.OPEN_BRACES)
        variables = []
        while self.get_token().token_type is TokenType.RESERVED and self.get_token().value in [TokenType.INT.value, TokenType.BOOL.value]:
            variables.append(self.parse_VAR())
        commands = []
        while self.get_token().value != TokenType.RETURN.value:
            commands.append(self.parse_CMD())
        self.consume(TokenType.RESERVED, TokenType.RETURN)
        exp = self.parse_EXP()
        self.consume(TokenType.PUNCTUATION, TokenType.SEMICOLON)
        self.consume(TokenType.PUNCTUATION, TokenType.CLOSE_BRACES)
        return Node("METODO", [tipo, identifier, params] + variables + commands + [exp])

    def parse_PARAMS(self):
        params = []
        if self.get_token().token_type is not TokenType.PUNCTUATION or self.get_token().value != TokenType.CLOSE_PARENTHESES.value:
            params.append(self.parse_TIPO())
            params.append(Node(TokenType.ID, [self.consume(TokenType.ID)]))
            while self.get_token().value == TokenType.COMMA.value:
                self.consume(TokenType.PUNCTUATION, TokenType.COMMA)
                params.append(self.parse_TIPO())
                params.append(Node(TokenType.ID, [self.consume(TokenType.ID)]))
        return Node("PARAMS", params)

    def parse_TIPO(self):
        token = self.get_token()
        if token.token_type is TokenType.RESERVED and token.value in [TokenType.INT.value, TokenType.BOOL.value]:
            tipo = Node(TokenType.RESERVED, [self.consume(TokenType.RESERVED)])
            if tipo.children[0].value == TokenType.INT.value and self.get_token().value == TokenType.OPEN_BRACKET.value:
                self.consume(TokenType.PUNCTUATION, TokenType.OPEN_BRACKET)
                self.consume(TokenType.PUNCTUATION, TokenType.CLOSE_BRACKET)
                return Node("TIPO", [tipo, Node("ARRAY")])
            return Node("TIPO", [tipo])
        elif token.token_type is TokenType.ID:
            identifier = Node(TokenType.ID, [self.consume(TokenType.ID)])
            return Node("TIPO", [identifier])
        else:
            raise Exception(f"Expected type, got {repr(token)} @ {self.index}")

    def parse_CMD(self):
        token = self.get_token()
        if token.value == TokenType.OPEN_BRACES.value:
            self.consume(TokenType.PUNCTUATION, TokenType.OPEN_BRACES)
            commands = []
            while self.get_token().value != TokenType.CLOSE_BRACES.value:
                commands.append(self.parse_CMD())
            self.consume(TokenType.PUNCTUATION, TokenType.CLOSE_BRACES)
            return Node("CMD", commands)
        elif token.value == TokenType.IF.value:
            self.consume(TokenType.RESERVED, TokenType.IF)
            self.consume(TokenType.PUNCTUATION, TokenType.OPEN_PARENTHESES)
            exp = self.parse_EXP()
            self.consume(TokenType.PUNCTUATION, TokenType.CLOSE_PARENTHESES)
            cmd = self.parse_CMD()
            if self.get_token() and self.get_token().value == TokenType.ELSE.value:
                self.consume(TokenType.RESERVED, TokenType.ELSE)
                else_cmd = self.parse_CMD()
                return Node("CMD", [Node(TokenType.IF, [exp, cmd]), Node(TokenType.ELSE, [else_cmd])])
            return Node("CMD", [Node(TokenType.IF, [exp, cmd])])
        elif token.value == TokenType.WHILE.value:
            self.consume(TokenType.RESERVED, TokenType.WHILE)
            self.consume(TokenType.PUNCTUATION, TokenType.OPEN_PARENTHESES)
            exp = self.parse_EXP()
            self.consume(TokenType.PUNCTUATION, TokenType.CLOSE_PARENTHESES)
            cmd = self.parse_CMD()
            return Node("CMD", [Node(TokenType.WHILE, [exp, cmd])])
        elif token.value == TokenType.PRINT.value:
            self.consume(TokenType.RESERVED, TokenType.PRINT)
            self.consume(TokenType.PUNCTUATION, TokenType.OPEN_PARENTHESES)
            exp = self.parse_EXP()
            self.consume(TokenType.PUNCTUATION, TokenType.CLOSE_PARENTHESES)
            self.consume(TokenType.PUNCTUATION, TokenType.SEMICOLON)
            return Node("CMD", [Node(TokenType.PRINT, [exp])])
        elif token.token_type is TokenType.ID:
            identifier = Node(TokenType.ID, [self.consume(TokenType.ID)])
            if self.get_token().value == TokenType.EQUALS.value:
                self.consume(TokenType.OP, TokenType.EQUALS)
                exp = self.parse_EXP()
                self.consume(TokenType.PUNCTUATION, TokenType.SEMICOLON)
                return Node("CMD", [identifier, Node(TokenType.OP, TokenType.EQUALS), exp])
            elif self.get_token().value == TokenType.OPEN_BRACKET.value:
                self.consume(TokenType.PUNCTUATION, TokenType.OPEN_BRACKET)
                index_exp = self.parse_EXP()
                self.consume(TokenType.PUNCTUATION, TokenType.CLOSE_BRACKET)
                self.consume(TokenType.OP, TokenType.EQUALS)
                value_exp = self.parse_EXP()
                self.consume(TokenType.PUNCTUATION, TokenType.SEMICOLON)
                return Node("CMD", [identifier, index_exp, Node(TokenType.OP, TokenType.EQUALS), value_exp])
        else:
            raise Exception(f"Expected command, got {repr(token)} @ {self.index}")

    def parse_EXP(self):
        left = self.parse_REXP()
        while self.get_token() and self.get_token().value == TokenType.AND.value:
            self.consume(TokenType.OP, TokenType.AND)
            right = self.parse_REXP()
            left = Node("EXP", [left, Node(TokenType.OP, TokenType.AND), right])
        return left

    def parse_REXP(self):
        left = self.parse_AEXP()
        while self.get_token() and self.get_token().value in [TokenType.LESS_THAN.value, TokenType.EQUALS_EQUALS.value, TokenType.DIFFERENT_THAN.value]:
            operator = Node(TokenType.OP, [self.consume(TokenType.OP)])
            right = self.parse_AEXP()
            left = Node("REXP", [left, operator, right])
        return left

    def parse_AEXP(self):
        left = self.parse_MEXP()
        while self.get_token() and self.get_token().value in [TokenType.PLUS.value, TokenType.MINUS.value]:
            operator = Node(TokenType.OP, [self.consume(TokenType.OP)])
            right = self.parse_MEXP()
            left = Node("AEXP", [left, operator, right])
        return left
    
    def parse_MEXP(self):
        left = self.parse_SEXP()
        while self.get_token() and self.get_token().value == TokenType.MULTIPLY.value:
            operator = Node(TokenType.OP, [self.consume(TokenType.OP)])
            right = self.parse_SEXP()
            left = Node("MEXP", [left, operator, right])
        return left

    def parse_SEXP(self):
        token = self.get_token()
        if token.value == TokenType.NOT.value:
            self.consume(TokenType.OP, TokenType.NOT)
            sexp = self.parse_SEXP()
            return Node("SEXP", [Node(TokenType.OP, TokenType.NOT), sexp])
        elif token.value == TokenType.MINUS.value:
            self.consume(TokenType.OP, TokenType.MINUS)
            sexp = self.parse_SEXP()
            return Node("SEXP", [Node(TokenType.OP, TokenType.MINUS), sexp])
        elif token.value == TokenType.TRUE.value:
            self.consume(TokenType.RESERVED, TokenType.TRUE)
            return Node("SEXP", [Node(TokenType.RESERVED, TokenType.TRUE)])
        elif token.value == TokenType.FALSE.value:
            self.consume(TokenType.RESERVED, TokenType.FALSE)
            return Node("SEXP", [Node(TokenType.RESERVED, TokenType.FALSE)])
        elif token.token_type.value == "num":
            num = Node("num", [self.consume("num")])
            return Node("SEXP", [num])
        elif token.value == TokenType.NULL.value:
            self.consume(TokenType.RESERVED, TokenType.NULL)
            return Node("SEXP", [Node(TokenType.RESERVED, TokenType.NULL)])
        elif token.value == TokenType.NEW.value and self.tokens[self.index + 1].value == TokenType.INT.value:
            self.consume(TokenType.RESERVED, TokenType.NEW)
            self.consume(TokenType.RESERVED, TokenType.INT)
            self.consume(TokenType.PUNCTUATION, TokenType.OPEN_BRACKET)
            exp = self.parse_EXP()
            self.consume(TokenType.PUNCTUATION, TokenType.CLOSE_BRACKET)
            return Node("SEXP", [Node(TokenType.RESERVED, TokenType.NEW), Node(TokenType.RESERVED, TokenType.INT), exp])
        else:
            pexp = self.parse_PEXP()
            if self.get_token() and self.get_token().value == TokenType.DOT.value and self.tokens[self.index + 1].value == TokenType.LENGHT.value:
                self.consume(TokenType.PUNCTUATION, TokenType.DOT)
                self.consume(TokenType.ID, TokenType.LENGHT)
                return Node("SEXP", [pexp, Node(TokenType.ID, TokenType.LENGHT)])
            elif self.get_token() and self.get_token().value == TokenType.OPEN_BRACKET.value:
                self.consume(TokenType.PUNCTUATION, TokenType.OPEN_BRACKET)
                exp = self.parse_EXP()
                self.consume(TokenType.PUNCTUATION, TokenType.CLOSE_BRACKET)
                return Node("SEXP", [pexp, exp])
            return pexp

    def parse_PEXP(self):
        base = self.parse_BasePEXP()
        while self.get_token() and self.get_token().value == TokenType.DOT.value:
            self.consume(TokenType.PUNCTUATION, TokenType.DOT)
            identifier = Node(TokenType.ID, [self.consume(TokenType.ID)])
            if self.get_token() and self.get_token().value == TokenType.OPEN_PARENTHESES.value:
                self.consume(TokenType.PUNCTUATION, TokenType.OPEN_PARENTHESES)
                exps = self.parse_EXPS() if self.get_token().value != TokenType.CLOSE_PARENTHESES.value else Node("EXPS", [])
                self.consume(TokenType.PUNCTUATION, TokenType.CLOSE_PARENTHESES)
                base = Node("PEXP", [base, identifier, exps])
            else:
                base = Node("PEXP", [base, identifier])
        return base
    
    # Tive que adicionar essa parada pra facilitar a vida
    def parse_BasePEXP(self):
        token = self.get_token()
        if token.token_type is TokenType.ID:
            identifier = Node(TokenType.ID, [self.consume(TokenType.ID)])
            return Node("BasePEXP", [identifier])
        elif token.token_type is TokenType.NUMBER:
            number = Node(TokenType.NUMBER, [self.consume(TokenType.NUMBER)])
            return Node("BasePEXP", [number])
        elif token.token_type is TokenType.RESERVED and token.value == TokenType.THIS.value:
            self.consume(TokenType.RESERVED, TokenType.THIS)
            return Node("BasePEXP", [Node(TokenType.RESERVED, TokenType.THIS)])
        elif token.token_type is TokenType.RESERVED and token.value == TokenType.NEW.value:
            self.consume(TokenType.RESERVED, TokenType.NEW)
            identifier = Node(TokenType.ID, [self.consume(TokenType.ID)])
            self.consume(TokenType.PUNCTUATION, TokenType.OPEN_PARENTHESES)
            self.consume(TokenType.PUNCTUATION, TokenType.CLOSE_PARENTHESES)
            return Node("BasePEXP", [Node(TokenType.RESERVED, TokenType.NEW), identifier])
        elif token.token_type is TokenType.PUNCTUATION and token.value == TokenType.OPEN_PARENTHESES.value:
            self.consume(TokenType.PUNCTUATION, TokenType.OPEN_PARENTHESES)
            exp = self.parse_EXP()
            self.consume(TokenType.PUNCTUATION, TokenType.CLOSE_PARENTHESES)
            return Node("BasePEXP", [exp])
        else:
            raise Exception(f"Expected BasePEXP, got {repr(token)} @ {self.index}")

    def parse_EXPS(self):
        exps = [self.parse_EXP()]
        while self.get_token() and self.get_token().value == TokenType.COMMA.value:
            self.consume(TokenType.PUNCTUATION, TokenType.COMMA)
            exps.append(self.parse_EXP())
        return Node("EXPS", exps)
