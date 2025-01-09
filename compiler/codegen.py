from .types import Node
import re

class CodeGen():
    def __init__(self, tree: Node) -> None:
        self.tree = tree
        self.data_section = []
        self.text_section = []
        self.variables = {}

    def generate_code(self) -> str:
        self._cgen(self.tree)
        data = "\n".join(self.data_section)
        text = "\n".join(self.text_section)
        return f".data\n{data}\n.text\n.globl main\n{text}"

    def yield_error(self, message: str, tree: Node) -> None:
        self.text_section.append(f"# ERROR: {message} @ {tree}")

    def _cgen(self, tree: Node) -> None:
        if hasattr(self, f"assemble_{tree.label}"):
            func = getattr(self, f"assemble_{tree.label}")
            if callable(func):
                func(tree)
        else:
            self.yield_error(f"assemble_{tree.label} function not found", tree)

    def assemble_PROG(self, tree: Node) -> None:
        for child in tree.children:
            self._cgen(child)
    
    def assemble_MAIN(self, tree: Node) -> None:
        self.text_section.append("main:")
        for child in tree.children[2:]:
            self._cgen(child)
        self.text_section.append("\tli $v0, 10")
        self.text_section.append("\tsyscall")

    def assemble_CLASSE(self, tree: Node) -> None:
        for child in tree.children[2:]:
            self._cgen(child)

    def assemble_METODO(self, tree: Node) -> None:
        method_name = tree.children[1].children[0]
        self.text_section.append(f"{method_name}:")
        
        # Handle method parameters
        params = tree.children[2].children
        for i in range(0, len(params), 2):
            param_type = params[i].children[0].children[0]
            param_name = params[i + 1].children[0]
            self.variables[param_name] = f"{param_name}_addr"
            self.data_section.append(f"{param_name}_addr: .word 0")
        
        for child in tree.children[3:]:
            self._cgen(child)
        self.text_section.append("\tjr $ra")

    def assemble_CALL(self, tree: Node) -> None:
        callee = tree.children[0].value
        self.text_section.append(f"\tjal {callee}")

    def assemble_RETURN(self, tree: Node) -> None:
        self._cgen(tree.children[0])
        self.text_section.append("\tjr $ra")

    def assemble_ASSIGN(self, tree: Node) -> None:
        var_name = tree.children[0].children[0]
        self._cgen(tree.children[2])
        self.text_section.append(f"\tsw $v0, {self.variables[var_name]}")

    def assemble_BINOP(self, tree: Node) -> None:
        self._cgen(tree.children[0])
        self.text_section.append("\tmove $t0, $v0")
        self._cgen(tree.children[2])
        operator = tree.children[1].children[0]
        if operator == "+":
            self.text_section.append(f"\tadd $v0, $t0, $v0")
        elif operator == "-":
            self.text_section.append(f"\tsub $v0, $t0, $v0")
        elif operator == "*":
            self.text_section.append(f"\tmul $v0, $t0, $v0")
        elif operator == "==":
            self.text_section.append(f"\tseq $v0, $t0, $v0")
        elif operator == "!=":
            self.text_section.append(f"\tsne $v0, $t0, $v0")
        elif operator == "<":
            self.text_section.append(f"\tslt $v0, $t0, $v0")

    def assemble_NUM(self, tree: Node) -> None:
        self.text_section.append(f"\tli $v0, {tree.children[0]}")

    def assemble_VAR(self, tree: Node) -> None:
        var_name = tree.children[1].children[0]
        self.variables[var_name] = f"{var_name}_addr"
        self.data_section.append(f"{var_name}_addr: .word 0")

    def assemble_PRINT(self, tree: Node) -> None:
        self._cgen(tree.children[0])
        self.text_section.append("\tmove $a0, $v0")
        self.text_section.append("\tli $v0, 1")
        self.text_section.append("\tsyscall")

    def assemble_STRING(self, tree: Node) -> None:
        label = f"str_{len(self.data_section)}"
        self.data_section.append(f'{label}: .asciiz {tree.children[0]}')
        self.text_section.append(f"\tla $a0, {label}")
        self.text_section.append("\tli $v0, 4")
        self.text_section.append("\tsyscall")

    def assemble_EXP(self, tree: Node) -> None:
        self._cgen(tree.children[0])
        for i in range(1, len(tree.children), 2):
            operator = tree.children[i].children[0]
            self._cgen(tree.children[i + 1])
            if operator == "&&":
                self.text_section.append("\tand $t0, $t0, $v0")
                self.text_section.append("\tmove $v0, $t0")

    def assemble_REXP(self, tree: Node) -> None:
        self._cgen(tree.children[0])
        for i in range(1, len(tree.children), 2):
            operator = tree.children[i].children[0]
            self._cgen(tree.children[i + 1])
            if operator == "<":
                self.text_section.append("\tslt $t0, $t0, $v0")
            elif operator == "==":
                self.text_section.append("\tseq $t0, $t0, $v0")
            elif operator == "!=":
                self.text_section.append("\tsne $t0, $t0, $v0")
            self.text_section.append("\tmove $v0, $t0")

    def assemble_AEXP(self, tree: Node) -> None:
        self._cgen(tree.children[0])
        for i in range(1, len(tree.children), 2):
            operator = tree.children[i].children[0]
            self._cgen(tree.children[i + 1])
            if operator == "+":
                self.text_section.append(f"\tadd $t0, $t0, $v0")
            elif operator == "-":
                self.text_section.append(f"\tsub $t0, $t0, $v0")
            self.text_section.append("\tmove $v0, $t0")

    def assemble_MEXP(self, tree: Node) -> None:
        self._cgen(tree.children[0])
        for i in range(1, len(tree.children), 2):
            operator = tree.children[i].children[0]
            self._cgen(tree.children[i + 1])
            if operator == "*":
                self.text_section.append(f"\tmul $t0, $t0, $v0")
            self.text_section.append("\tmove $v0, $t0")

    def assemble_SEXP(self, tree: Node) -> None:
        if tree.children[0].label == "number":
            self.assemble_NUM(tree.children[0])
        elif tree.children[0].label == "identifier":
            self.assemble_identifier(tree.children[0])
        else:
            self.yield_error(f"Unsupported SEXP type: {tree.children[0].label}", tree)

    def assemble_PEXP(self, tree: Node) -> None:
        if tree.children[0].label == "reserved" and tree.children[0].children[0] == "new":
            class_name = tree.children[1].children[0]
            self.text_section.append(f"\t# Create new object of class {class_name}")
            # Assuming object creation logic here
        elif tree.children[0].label == "identifier":
            identifier = tree.children[0].children[0]
            if len(tree.children) > 1 and tree.children[1].label == "EXPS":
                self.text_section.append(f"\t# Call method {identifier}")
                self.assemble_EXPS(tree.children[1])
                self.text_section.append(f"\tjal {identifier}")
            else:
                self.assemble_identifier(tree.children[0])
        elif tree.children[0].label == "reserved" and tree.children[0].children[0] == "this":
            self.text_section.append("\t# Handle 'this' keyword")
            # Assuming 'this' keyword handling logic here
        elif tree.children[0].label == "PEXP":
            self._cgen(tree.children[0])
            if len(tree.children) > 1 and tree.children[1].label == "identifier":
                method_name = tree.children[1].children[0]
                self.text_section.append(f"\t# Call method {method_name}")
                if len(tree.children) > 2 and tree.children[2].label == "EXPS":
                    self.assemble_EXPS(tree.children[2])
                self.text_section.append(f"\tjal {method_name}")
        elif tree.children[0].label == "SEXP":
            self.assemble_SEXP(tree.children[0])
        elif tree.children[0].label == "LPAREN":
            self._cgen(tree.children[1])  # Assuming the expression is the second child
        else:
            self.yield_error(f"Unsupported PEXP type: {tree.children[0].label}", tree)

    def assemble_EXPS(self, tree: Node) -> None:
        for child in tree.children:
            self._cgen(child)
            self.text_section.append("\taddi $sp, $sp, -4")
            self.text_section.append("\tsw $v0, 0($sp)")

    def assemble_identifier(self, tree: Node) -> None:
        var_name = tree.children[0]
        if var_name in self.variables:
            self.text_section.append(f"\tlw $v0, {self.variables[var_name]}")
        else:
            self.text_section.append(f"# ERROR: Undefined variable {var_name}")

    def assemble_CMD(self, tree: Node) -> None:
        if tree.children[0].label == "System.out.println":
            expr = tree.children[0].children[0]
            if expr.label == "STRING":
                self.assemble_STRING(expr)
            else:
                self._cgen(expr)
                self.text_section.append("\tmove $a0, $v0")
                self.text_section.append("\tli $v0, 1")
                self.text_section.append("\tsyscall")
        elif tree.children[0].label == "VAR":
            self.assemble_VAR(tree.children[0])
        elif tree.children[0].label == "identifier" and tree.children[1].label == "operator" and tree.children[1].children[0] == "=":
            self.assemble_ASSIGN(tree)
        elif tree.children[0].label == "if":
            self.assemble_IF(tree)
        else:
            self.text_section.append(f"# ERROR @ {tree}")

    def assemble_IF(self, tree: Node) -> None:
        condition = tree.children[0].children[0]
        if_block = tree.children[0].children[1]
        else_block = tree.children[1].children[0] if len(tree.children) > 1 and tree.children[1].label == "else" else None

        self._cgen(condition)
        self.text_section.append("\tbeqz $v0, else_label")
        self._cgen(if_block)
        if else_block:
            self.text_section.append("\tj end_if_label")
            self.text_section.append("else_label:")
            self._cgen(else_block)
            self.text_section.append("end_if_label:")
        else:
            self.text_section.append("else_label:")