from typing import List
import uuid

class Node():
    def __init__(self, label: str, children: List['Node']) -> None:
        self.value = str(uuid.uuid4())
        self.label = label
        self.children = children

    def add_child(self, child: 'Node') -> None:
        self.children.append(child)

    def __repr__(self) -> str:
        return f"{self.label}({', '.join(repr(child) for child in self.children)})"