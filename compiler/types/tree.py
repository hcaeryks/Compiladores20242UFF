from typing import List
import uuid

class Node():
    def __init__(self, label: str, children: List['Node'], type: str = "") -> None:
        self.value = str(uuid.uuid4())
        self.label = label
        self.children = children
        self.type = type

    def add_child(self, child: 'Node') -> None:
        self.children.append(child)

    def get_identifiers(self) -> List[str]:
        params = []
        if self.label == "METODO":
            for i in range(0, len(self.children[2].children), 2):
                params.append({"name": self.children[2].children[i+1].children[0], "dtype": self.children[2].children[i].children[0].children[0], "aas_type": "PARAM", "method": self.children[1].children[0], "pos": i//2})
        dtype = self.children[0].children[0].children[0] if type(self.children[0]) == Node and self.children[0].label == "TIPO" else None
        dtype = "String[]" if dtype == None and self.label == "MAIN" else dtype
        return [{"name": child.children[0], "dtype": dtype, "aas_type": self.label} for child in self.children if isinstance(child, Node) and child.label == 'identifier'] + params

    def are_there_numbers_involved(self) -> bool:
        if self.label == "number":
            return True
        for child in self.children:
            if isinstance(child, Node) and child.are_there_numbers_involved():
                return True
        return False
    
    def are_there_bools_involved(self) -> bool:
        if self.label == "reserved" and (self.children[0] == "true" or self.children[0] == "false"):
            return True
        for child in self.children:
            if isinstance(child, Node) and child.are_there_bools_involved():
                return True
        return False
    
    def are_there_variables_involved(self) -> bool:
        if self.label == "identifier":
            return True
        for child in self.children:
            if isinstance(child, Node) and child.are_there_variables_involved():
                return True
        return False
    
    def get_direct_val(self, node: 'Node') -> int | bool:
        if node.children[0].label == "reserved":
            return True if node.children[0].children[0].value == "true" else False
        return int(node.children[0].children[0].value)
    
    def evaluate_bottom_expression(self) -> int | bool:
        if self.label == "AEXP" or self.label == "MEXP":
            op = self.children[1].children[0].value
            if op == "+":
                return self.get_direct_val(self.children[0]) + self.get_direct_val(self.children[2])
            elif op == "-":
                return self.get_direct_val(self.children[0]) - self.get_direct_val(self.children[2])
            elif op == "*":
                return self.get_direct_val(self.children[0]) * self.get_direct_val(self.children[2])
        elif self.label == "REXP" or self.label == "EXP":
            op = self.children[1].children[0].value
            if op == "<":
                return self.get_direct_val(self.children[0]) < self.get_direct_val(self.children[2])
            elif op == "==":
                return self.get_direct_val(self.children[0]) == self.get_direct_val(self.children[2])
            elif op == "!=":
                return self.get_direct_val(self.children[0]) != self.get_direct_val(self.children[2])
            elif op == "&&":
                return self.get_direct_val(self.children[0]) and self.get_direct_val(self.children[2])

    def __repr__(self) -> str:
        return f"{self.label}({', '.join(repr(child) for child in self.children)})"