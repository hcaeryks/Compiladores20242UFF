from .types import Node

class CodeGen():
    def __init__(self, tree: Node) -> None:
        self.tree = tree

    def cgen(self, tree: Node) -> str:
        pass