class Token:
    def __init__(self, token_type: str, value: str) -> None:
        self.token_type = token_type
        self.value = value

    def __repr__(self) -> str:
        return f"Token(type={self.token_type}, value={self.value})"

class Node:
    def __init__(self, label: str, children: list = None, value: str = None) -> None:
        self.label = label
        self.children = children if children is not None else []
        self.value = value

    def __repr__(self) -> str:
        return f"Node(label={self.label}, value={self.value}, children={self.children})"
