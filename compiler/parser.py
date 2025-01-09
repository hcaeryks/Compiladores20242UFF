from .types import Token, Node
from typing import List, Dict, Set

class Parser():
    def __init__(self, tokens: List[Token]) -> None:
        self.tokens = [token for token in tokens if token.token_type != "whitespace" and token.token_type != "comment"]
        self.index = 0

        self.first: Dict[str, Set[str]] = {
            "PROG": {"class"},
            "MAIN": {"class"},
            "CLASSE": {"class"},
            "VAR": {"int", "boolean", "id"},
            "METODO": {"public"},
            "TIPO": {"int", "boolean", "id"},
            "CMD": {"{", "if", "while", "System.out.println", "id"},
            "EXP": {"!", "-", "true", "false", "num", "null", "new", "(", "this", "id"},
            "REXP": {"<", "==", "!="},
            "AEXP": {"+", "-"},
            "MEXP": {"*"},
            "SEXP": {"!", "-", "true", "false", "num", "null", "new", "(", "this", "id"},
            "PEXP": {"id", "this", "new", "("},
            "EXPS": {"!", "-", "true", "false", "num", "null", "new", "(", "this", "id"},
        }

        self.follow: Dict[str, Set[str]] = {
            "PROG": {"$"},
            "MAIN": {"class", "$"},
            "CLASSE": {"class", "$"},
            "VAR": {"public", "}", "$"},
            "METODO": {"public", "}", "$"},
            "TIPO": {"id"},
            "CMD": {"}", "else", "return"},
            "EXP": {")", ";", "]", "&&"},
            "REXP": {"&&"},
            "AEXP": {"&&", "<", "==", "!="},
            "MEXP": {"+", "-", "&&", "<", "==", "!="},
            "SEXP": {"*", "+", "-", "&&", "<", "==", "!="},
            "PEXP": {".", "(", "[", "*", "+", "-", "&&", "<", "==", "!="},
            "EXPS": {")"},
        }

    def get_token(self) -> Token:
        return self.tokens[self.index] if self.index < len(self.tokens) else None

    def consume(self, expected_type: str, expected_value: str = None) -> Token:
        token = self.get_token()
        print(f"Consuming token: {token}")
        if token and token.token_type == expected_type and (expected_value is None or token.value == expected_value):
            self.index += 1
            return token
        else:
            expected_desc = f"{expected_type} ('{expected_value}')" if expected_value else f"{expected_type}"
            raise Exception(f"Expected {expected_desc}, got {repr(token)} @ {self.index}")
        
    def parse(self):
        return self.parse_PROG()

    def parse_PROG(self):
        print("Parsing PROG")
        if self.get_token() and self.get_token().value in self.first["PROG"]:
            main = self.parse_MAIN()
            classes = []
            while self.get_token() and self.get_token().value in self.first["CLASSE"]:
                classes.append(self.parse_CLASSE())
            return Node("PROG", [main] + classes)
        else:
            raise Exception("Invalid start of program")

    def parse_MAIN(self):
        print("Parsing MAIN")
        self.consume("reserved", "class")
        class_name = Node("identifier", [self.consume("identifier").value])
        self.consume("punctuation", "{")
        self.consume("reserved", "public")
        self.consume("reserved", "static")
        self.consume("reserved", "void")
        self.consume("reserved", "main")
        self.consume("punctuation", "(")
        self.consume("reserved", "String")
        self.consume("punctuation", "[")
        self.consume("punctuation", "]")
        parameter = Node("identifier", [self.consume("identifier").value])
        self.consume("punctuation", ")")
        self.consume("punctuation", "{")
        commands = []
        while self.get_token() and self.get_token().value not in self.follow["CMD"]:
            commands.append(self.parse_CMD())
        self.consume("punctuation", "}")
        self.consume("punctuation", "}")
        return Node("MAIN", [class_name, parameter] + commands)

    def parse_CLASSE(self):
        print("Parsing CLASSE")
        self.consume("reserved", "class")
        class_name = Node("identifier", [self.consume("identifier").value])
        parent = None
        if self.get_token() and self.get_token().value == "extends":
            self.consume("reserved", "extends")
            parent = Node("identifier", [self.consume("identifier").value])
        self.consume("punctuation", "{")
        variables = []
        while self.get_token() and self.get_token().value in self.first["VAR"]:
            variables.append(self.parse_VAR())
        methods = []
        while self.get_token() and self.get_token().value in self.first["METODO"]:
            methods.append(self.parse_METODO())
        self.consume("punctuation", "}")
        return Node("CLASSE", [class_name, parent] + variables + methods)

    def parse_METODO(self):
        print("Parsing METODO")
        self.consume("reserved", "public")
        tipo = self.parse_TIPO()
        method_name = Node("identifier", [self.consume("identifier").value])
        self.consume("punctuation", "(")
        params = self.parse_PARAMS() if self.get_token().value != ")" else Node("PARAMS", [])
        self.consume("punctuation", ")")
        self.consume("punctuation", "{")
        variables = []
        while self.get_token() and self.get_token().value in self.first["VAR"]:
            variables.append(self.parse_VAR())
        commands = []
        while self.get_token() and self.get_token().value != "return":
            commands.append(self.parse_CMD())
        self.consume("reserved", "return")
        exp = self.parse_EXP()
        self.consume("punctuation", ";")
        self.consume("punctuation", "}")
        return Node("METODO", [tipo, method_name, params] + variables + commands + [exp])

    def parse_PARAMS(self):
        print("Parsing PARAMS")
        params = []
        if self.get_token() and self.get_token().value in self.first["TIPO"]:
            params.append(self.parse_TIPO())
            params.append(Node("identifier", [self.consume("identifier").value]))
            while self.get_token() and self.get_token().value == ",":
                self.consume("punctuation", ",")
                params.append(self.parse_TIPO())
                params.append(Node("identifier", [self.consume("identifier").value]))
        return Node("PARAMS", params)

    def parse_VAR(self):
        print("Parsing VAR")
        tipo = self.parse_TIPO()
        var_name = Node("identifier", [self.consume("identifier").value])
        self.consume("punctuation", ";")
        return Node("VAR", [tipo, var_name])

    def parse_TIPO(self):
        print("Parsing TIPO")
        token = self.get_token()
        if token.value == "int":
            self.consume("reserved", "int")
            if self.get_token() and self.get_token().value == "[":
                self.consume("punctuation", "[")
                self.consume("punctuation", "]")
                return Node("TIPO", [Node("reserved", ["int[]"])])
            return Node("TIPO", [Node("reserved", ["int"])])
        elif token.value == "boolean":
            self.consume("reserved", "boolean") 
            return Node("TIPO", [Node("reserved", ["boolean"])])
        elif token.token_type == "identifier":
            identifier = Node("identifier", [self.consume("identifier").value])
            return Node("TIPO", [identifier])
        else:
            raise Exception(f"Expected type, got {repr(token)} @ {self.index}")
        

    def parse_CMD(self):
        print("Parsing CMD")
        token = self.get_token()
        if not token:
            return None

        if token.value == "{" and token.token_type == "punctuation":
            self.consume("punctuation", "{")
            commands = []
            while self.get_token() and self.get_token().value not in self.follow["CMD"]:
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
        elif token.token_type == "reserved" and token.value in {"int", "boolean"}:
            var_decl = self.parse_VAR()
            return Node("CMD", [var_decl])
        elif token.token_type == "identifier":
            identifier = Node("identifier", [self.consume("identifier").value])
            if self.get_token() and self.get_token().value == "=":
                self.consume("operator", "=")
                exp = self.parse_EXP()
                self.consume("punctuation", ";")
                return Node("CMD", [identifier, Node("operator", ["="]), exp])
            elif self.get_token() and self.get_token().value == "[":
                self.consume("punctuation", "[")
                index_exp = self.parse_EXP()
                self.consume("punctuation", "]")
                self.consume("operator", "=")
                value_exp = self.parse_EXP()
                self.consume("punctuation", ";")
                return Node("CMD", [identifier, index_exp, Node("operator", ["="]), value_exp])
            else:
                raise Exception("Invalid CMD structure")
        else:
            raise Exception(f"Unexpected token {repr(token)}")
        
    def parse_EXP(self):
        print("Parsing EXP")
        left = self.parse_REXP()
        while self.get_token() and self.get_token().value == "&&":
            and_op = self.consume("operator", "&&")
            right = self.parse_REXP()
            left = Node("EXP", [left, Node("operator", [and_op.value]), right])
        return left

    def parse_REXP(self):
        print("Parsing REXP")
        left = self.parse_AEXP()
        while self.get_token() and self.get_token().value in ["<", "==", "!="]:
            operator = Node("operator", [self.consume("operator").value])
            right = self.parse_AEXP()
            left = Node("REXP", [left, operator, right])
        return left

    def parse_AEXP(self):
        print("Parsing AEXP")
        left = self.parse_MEXP()
        while self.get_token() and self.get_token().value in ["+", "-"]:
            operator = Node("operator", [self.consume("operator").value])
            right = self.parse_MEXP()
            left = Node("AEXP", [left, operator, right])
        return left

    def parse_MEXP(self):
        print("Parsing MEXP")
        left = self.parse_SEXP()
        while self.get_token() and self.get_token().value == "*":
            operator = Node("operator", [self.consume("operator").value])
            right = self.parse_SEXP()
            left = Node("MEXP", [left, operator, right])
        return left

    def parse_SEXP(self):
        print("Parsing SEXP")
        token = self.get_token()
        if token.value == "!":
            not_op = self.consume("operator", "!") # making our life easier
            sexp = self.parse_SEXP()
            op = sexp.children[0].children[0]
            op = "false" if op == "true" else "true"
            return Node("SEXP", [Node("boolean", [op])])
        elif token.value == "-":
            min_op = self.consume("operator", "-") # making our life easier
            sexp = self.parse_SEXP()
            num = sexp.children[0].children[0]
            num = int(num) * -1
            return Node("SEXP", [Node("number", [str(num)])])
        elif token.value == "true":
            return Node("SEXP", [Node("reserved", [self.consume("reserved", "true").value])])
        elif token.value == "false":
            return Node("SEXP", [Node("reserved", [self.consume("reserved", "false").value])])
        elif token.token_type == "number":
            num = Node("number", [self.consume("number").value])
            return Node("SEXP", [num])
        elif token.value == "null":
            self.consume("reserved", "null")
            return Node("SEXP", [Node("reserved", ["null"])])
        elif token.value == "new" and self.tokens[self.index + 1].value == "int":
            self.consume("reserved", "new")
            self.consume("reserved", "int")
            self.consume("punctuation", "[")
            exp = self.parse_EXP()
            self.consume("punctuation", "]")
            return Node("SEXP", [Node("reserved", ["new"]), Node("reserved", ["int"]), exp])
        else:
            pexp = self.parse_PEXP()
            while self.get_token() and self.get_token().value == ".":
                self.consume("punctuation", ".")
                identifier = Node("identifier", [self.consume("identifier").value])
                if self.get_token() and self.get_token().value == "(":
                    self.consume("punctuation", "(")
                    exps = self.parse_EXPS() if self.get_token().value != ")" else Node("EXPS", [])
                    self.consume("punctuation", ")")
                    pexp = Node("PEXP", [pexp, identifier, exps], "method_call")
                else:
                    pexp = Node("PEXP", [pexp, identifier])
            return pexp

    def parse_PEXP(self):
        print("Parsing PEXP")
        token = self.get_token()
        if token.token_type == "identifier":
            identifier = Node("identifier", [self.consume("identifier").value])
            if self.get_token() and self.get_token().value == "(":
                self.consume("punctuation", "(")
                exps = self.parse_EXPS() if self.get_token().value != ")" else Node("EXPS", [])
                self.consume("punctuation", ")")
                return Node("PEXP", [identifier, exps], "method_call")
            return identifier
        elif token.token_type == "number":
            self.index += 1
            return Node("NUM", [token.value])
        elif token.token_type == "reserved" and token.value == "new":
            self.consume("reserved", "new")
            class_name = Node("identifier", [self.consume("identifier").value])
            self.consume("punctuation", "(")
            self.consume("punctuation", ")")
            return Node("PEXP", [Node("reserved", ["new"]), class_name])
        elif token.token_type == "reserved" and token.value == "this":
            self.consume("reserved", "this")
            return Node("PEXP", [Node("reserved", ["this"])])
        elif token.token_type == "punctuation" and token.value == "(":
            self.consume("punctuation", "(")
            exp = self.parse_EXP()
            self.consume("punctuation", ")")
            return Node("PEXP", [exp])
        else:
            raise Exception(f"Expected PEXP, got {repr(token)} @ {self.index}")

    def parse_EXPS(self):
        print("Parsing EXPS")
        exps = [self.parse_EXP()]
        while self.get_token() and self.get_token().value == ",":
            self.consume("punctuation", ",")
            exps.append(self.parse_EXP())
        return Node("EXPS", exps)
