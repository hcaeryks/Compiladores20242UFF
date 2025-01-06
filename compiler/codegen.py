from .types import Node
import re

class CodeGen():
    def __init__(self, tree: Node) -> None:
        self.tree = tree

    def generate_code(self) -> str:
        return self.cgen(self.tree)

    def _cgen(self, tree: Node) -> str:
        if hasattr(self, f"assemble_{tree.label}"):
            func = getattr(self, f"assemble_{tree.label}")
            if callable(func):
                return func(tree)
        else:
            return f"ERROR @ {tree}"
        
    def assemble_PROG(self, tree: Node) -> str:
        return "yea!"
    
    def assemble_MAIN(self, tree: Node) -> str:
        return self._cgen(tree.children[0])