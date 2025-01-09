from .types import Node

class Optimizer():
    def __init__(self, tree: Node):
        self.tree = tree

    def optimize(self) -> Node:
        self.constant_folding(self.tree)
        self.dead_code_elimination(self.tree)
        return self.tree

    def constant_folding(self, node: Node) -> None:
        if not isinstance(node, Node):
            return

        for i, child in enumerate(node.children):
            if isinstance(child, Node):
                self.constant_folding(child)

        if node.label in {"AEXP", "MEXP", "REXP", "EXP"} and not node.are_there_variables_involved():
            folded_value = node.evaluate_bottom_expression()
            if isinstance(folded_value, bool):
                folded_value = "true" if folded_value else "false"
                node.children = [Node("reserved", [folded_value])]
            else:
                node.children = [Node("number", [str(folded_value)])]
            node.label = "SEXP"

    def dead_code_elimination(self, node: Node) -> None:
        if not isinstance(node, Node):
            return

        for i, child in enumerate(node.children):
            if isinstance(child, Node):
                self.dead_code_elimination(child)

        if node.label == "CMD" and len(node.children) > 0 and node.children[0].label == "if":
            condition = node.children[0].children[0]
            if condition.label == "SEXP" and condition.children[0].label == "reserved":
                if condition.children[0].children[0] == "false":
                    node.children = [Node("CMD", [node.children[1].children[0]])] if len(node.children) > 1 else []
                elif condition.children[0].children[0] == "true":
                    node.children = [node.children[0].children[1]]