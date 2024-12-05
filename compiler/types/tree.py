from typing import List

class Node():
    def __init__(self, value: str, children: List['Node']) -> None:
        self.value = value
        self.children = children

    def add_child(self, child: 'Node') -> None:
        self.children.append(child)

    def __repr__(self) -> str:
        return f"{self.value}({', '.join(repr(child) for child in self.children)})"