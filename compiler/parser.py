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
        class_name = Node("identifier", [self.consume("identifier")])
        self.consume("punctuation", "{")
        self.consume("reserved", "public")
        self.consume("reserved", "static")
        self.consume("reserved", "void")
        self.consume("reserved", "main")
        self.consume("punctuation", "(")
        self.consume("reserved", "String")
        self.consume("punctuation", "[")
        self.consume("punctuation", "]")
        parameter = Node("identifier", [self.consume("identifier")])
        self.consume("punctuation", ")")
        self.consume("punctuation", "{")
        commands = []
        while self.get_token().value != "}":
            commands.append(self.parse_CMD())
        self.consume("punctuation", "}")
        self.consume("punctuation", "}")
        return Node("MAIN", [class_name, parameter] + commands)

    def parse_CLASSE(self):
        self.consume("reserved", "class")
        class_name = Node("identifier", [self.consume("identifier")])
        parent_class = None
        if self.get_token().value == "extends":
            self.consume("reserved", "extends")
            parent_class = Node("identifier", [self.consume("identifier")])
        self.consume("punctuation", "{")
        variables = []
        while self.get_token().value not in ["public", "}"]:
            variables.append(self.parse_VAR())
        methods = []
        while self.get_token().value != "}":
            methods.append(self.parse_METODO())
        self.consume("punctuation", "}")
        return Node("CLASSE", [class_name, parent_class] + variables + methods)

    def parse_VAR(self):
        tipo = self.parse_TIPO()
        identifier = Node("identifier", [self.consume("identifier")])
        self.consume("punctuation", ";")
        return Node("VAR", [tipo, identifier])

    def parse_METODO(self):
        self.consume("reserved", "public")
        tipo = self.parse_TIPO()
        identifier = Node("identifier", [self.consume("identifier")])
        self.consume("punctuation", "(")
        params = self.parse_PARAMS() if self.get_token().value != ")" else Node("PARAMS", [])
        self.consume("punctuation", ")")
        self.consume("punctuation", "{")
        variables = []
        while self.get_token().token_type == "reserved" and self.get_token().value in ["int", "boolean"]:
            variables.append(self.parse_VAR())
        commands = []
        while self.get_token().value != "return":
            commands.append(self.parse_CMD())
        self.consume("reserved", "return")
        exp = self.parse_EXP()
        self.consume("punctuation", ";")
        self.consume("punctuation", "}")
        return Node("METODO", [tipo, identifier, params] + variables + commands + [exp])

    def parse_PARAMS(self):
        params = []
        if self.get_token().token_type != "punctuation" or self.get_token().value != ")":
            params.append(self.parse_TIPO())
            params.append(Node("identifier", [self.consume("identifier")]))
            while self.get_token().value == ",":
                self.consume("punctuation", ",")
                params.append(self.parse_TIPO())
                params.append(Node("identifier", [self.consume("identifier")]))
        return Node("PARAMS", params)

    def parse_TIPO(self):
        token = self.get_token()
        if token.token_type == "reserved" and token.value in ["int", "boolean"]:
            tipo = Node("reserved", [self.consume("reserved")])
            if tipo.children[0].value == "int" and self.get_token().value == "[":
                self.consume("punctuation", "[")
                self.consume("punctuation", "]")
                return Node("TIPO", [tipo, Node("ARRAY")])
            return Node("TIPO", [tipo])
        elif token.token_type == "identifier":
            identifier = Node("identifier", [self.consume("identifier")])
            return Node("TIPO", [identifier])
        else:
            raise Exception(f"Expected type, got {repr(token)} @ {self.index}")

    def parse_CMD(self):
        token = self.get_token()
        if token.value == "{":
            self.consume("punctuation", "{")
            commands = []
            while self.get_token().value != "}":
                commands.append(self.parse_CMD())
            self.consume("punctuation", "}")
            return Node("CMD", commands)
        elif token.value == "if":
            self.consume("reserved", "if")
            self.consume("punctuation", "(")
            exp = self.parse_EXP()
            self.consume("punctuation", ")")
            cmd = self.parse_CMD()
            if self.get_token() and self.get_token().value == "else":
                self.consume("reserved", "else")
                else_cmd = self.parse_CMD()
                return Node("CMD", [Node("if", [exp, cmd]), Node("else", [else_cmd])])
            return Node("CMD", [Node("if", [exp, cmd])])
        elif token.value == "while":
            self.consume("reserved", "while")
            self.consume("punctuation", "(")
            exp = self.parse_EXP()
            self.consume("punctuation", ")")
            cmd = self.parse_CMD()
            return Node("CMD", [Node("while", [exp, cmd])])
        elif token.value == "System.out.println":
            self.consume("reserved", "System.out.println")
            self.consume("punctuation", "(")
            exp = self.parse_EXP()
            self.consume("punctuation", ")")
            self.consume("punctuation", ";")
            return Node("CMD", [Node("System.out.println", [exp])])
        elif token.token_type == "identifier":
            identifier = Node("identifier", [self.consume("identifier")])
            if self.get_token().value == "=":
                self.consume("operator", "=")
                exp = self.parse_EXP()
                self.consume("punctuation", ";")
                return Node("CMD", [identifier, Node("operator", "="), exp])
            elif self.get_token().value == "[":
                self.consume("punctuation", "[")
                index_exp = self.parse_EXP()
                self.consume("punctuation", "]")
                self.consume("operator", "=")
                value_exp = self.parse_EXP()
                self.consume("punctuation", ";")
                return Node("CMD", [identifier, index_exp, Node("operator", "="), value_exp])
        else:
            raise Exception(f"Expected command, got {repr(token)} @ {self.index}")

    def parse_EXP(self):
        left = self.parse_REXP()
        while self.get_token() and self.get_token().value == "&&":
            self.consume("operator", "&&")
            right = self.parse_REXP()
            left = Node("EXP", [left, Node("operator", "&&"), right])
        return left

    def parse_REXP(self):
        left = self.parse_AEXP()
        while self.get_token() and self.get_token().value in ["<", "==", "!="]:
            operator = Node("operator", [self.consume("operator")])
            right = self.parse_AEXP()
            left = Node("REXP", [left, operator, right])
        return left

    def parse_AEXP(self):
        left = self.parse_MEXP()
        while self.get_token() and self.get_token().value in ["+", "-"]:
            operator = Node("operator", [self.consume("operator")])
            right = self.parse_MEXP()
            left = Node("AEXP", [left, operator, right])
        return left
    
    def parse_MEXP(self):
        left = self.parse_SEXP()
        while self.get_token() and self.get_token().value == "*":
            operator = Node("operator", [self.consume("operator")])
            right = self.parse_SEXP()
            left = Node("MEXP", [left, operator, right])
        return left

    def parse_SEXP(self):
        token = self.get_token()
        if token.value == "!":
            self.consume("operator", "!")
            sexp = self.parse_SEXP()
            return Node("SEXP", [Node("operator", "!"), sexp])
        elif token.value == "-":
            self.consume("operator", "-")
            sexp = self.parse_SEXP()
            return Node("SEXP", [Node("operator", "-"), sexp])
        elif token.value == "true":
            self.consume("reserved", "true")
            return Node("SEXP", [Node("reserved", "true")])
        elif token.value == "false":
            self.consume("reserved", "false")
            return Node("SEXP", [Node("reserved", "false")])
        elif token.token_type == "num":
            num = Node("num", [self.consume("num")])
            return Node("SEXP", [num])
        elif token.value == "null":
            self.consume("reserved", "null")
            return Node("SEXP", [Node("reserved", "null")])
        elif token.value == "new" and self.tokens[self.index + 1].value == "int":
            self.consume("reserved", "new")
            self.consume("reserved", "int")
            self.consume("punctuation", "[")
            exp = self.parse_EXP()
            self.consume("punctuation", "]")
            return Node("SEXP", [Node("reserved", "new"), Node("reserved", "int"), exp])
        else:
            pexp = self.parse_PEXP()
            if self.get_token() and self.get_token().value == "." and self.tokens[self.index + 1].value == "length":
                self.consume("punctuation", ".")
                self.consume("identifier", "length")
                return Node("SEXP", [pexp, Node("identifier", "length")])
            elif self.get_token() and self.get_token().value == "[":
                self.consume("punctuation", "[")
                exp = self.parse_EXP()
                self.consume("punctuation", "]")
                return Node("SEXP", [pexp, exp])
            return pexp

    def parse_PEXP(self):
        base = self.parse_BasePEXP()
        while self.get_token() and self.get_token().value == ".":
            self.consume("punctuation", ".")
            identifier = Node("identifier", [self.consume("identifier")])
            if self.get_token() and self.get_token().value == "(":
                self.consume("punctuation", "(")
                exps = self.parse_EXPS() if self.get_token().value != ")" else Node("EXPS", [])
                self.consume("punctuation", ")")
                base = Node("PEXP", [base, identifier, exps])
            else:
                base = Node("PEXP", [base, identifier])
        return base
    
    def parse_BasePEXP(self):
        token = self.get_token()
        if token.token_type == "identifier":
            identifier = Node("identifier", [self.consume("identifier")])
            return Node("BasePEXP", [identifier])
        elif token.token_type == "number":  # Add handling for numeric literals
            number = Node("number", [self.consume("number")])
            return Node("BasePEXP", [number])
        elif token.token_type == "reserved" and token.value == "this":
            self.consume("reserved", "this")
            return Node("BasePEXP", [Node("reserved", "this")])
        elif token.token_type == "reserved" and token.value == "new":
            self.consume("reserved", "new")
            identifier = Node("identifier", [self.consume("identifier")])
            self.consume("punctuation", "(")
            self.consume("punctuation", ")")
            return Node("BasePEXP", [Node("reserved", "new"), identifier])
        elif token.token_type == "punctuation" and token.value == "(":
            self.consume("punctuation", "(")
            exp = self.parse_EXP()
            self.consume("punctuation", ")")
            return Node("BasePEXP", [exp])
        else:
            raise Exception(f"Expected BasePEXP, got {repr(token)} @ {self.index}")

    def parse_EXPS(self):
        exps = [self.parse_EXP()]
        while self.get_token() and self.get_token().value == ",":
            self.consume("punctuation", ",")
            exps.append(self.parse_EXP())
        return Node("EXPS", exps)
