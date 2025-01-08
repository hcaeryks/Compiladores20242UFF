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
        return f".data\n{data}\n.text\n{text}"

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
        self.text_section.append("\tjr $ra")

    def assemble_CLASSE(self, tree: Node) -> None:
        for child in tree.children[2:]:
            self._cgen(child)

    def assemble_METODO(self, tree: Node) -> None:
        method_name = tree.children[1].value
        self.text_section.append(f"{method_name}:")
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
        left_code = self._cgen(tree.children[0])
        right_code = self._cgen(tree.children[1])
        operator = tree.value
        if operator == "+":
            self.text_section.append(f"\tadd $t0, {left_code}, {right_code}")
        elif operator == "-":
            self.text_section.append(f"\tsub $t0, {left_code}, {right_code}")
        elif operator == "*":
            self.text_section.append(f"\tmul $t0, {left_code}, {right_code}")
        elif operator == "==":
            self.text_section.append(f"\tseq $t0, {left_code}, {right_code}")
        elif operator == "!=":
            self.text_section.append(f"\tsne $t0, {left_code}, {right_code}")
        elif operator == "<":
            self.text_section.append(f"\tslt $t0, {left_code}, {right_code}")
        self.text_section.append("\tmove $v0, $t0")

    def assemble_NUM(self, tree: Node) -> None:
        self.text_section.append(f"\tli $t0, {tree.value}")
        self.text_section.append("\tmove $v0, $t0")

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
        self.data_section.append(f'{label}: .asciiz "{tree.value}"')
        self.text_section.append(f"\tla $a0, {label}")
        self.text_section.append("\tli $v0, 4")
        self.text_section.append("\tsyscall")

    def assemble_identifier(self, tree: Node) -> None:
        var_name = tree.value
        if var_name in self.variables:
            self.text_section.append(f"\tlw $t0, {self.variables[var_name]}")
            self.text_section.append("\tmove $v0, $t0")
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
        else:
            self.text_section.append(f"# ERROR @ {tree}")