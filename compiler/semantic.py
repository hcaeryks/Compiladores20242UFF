from .types import Node
from .types import Token

class Semantic():
    def __init__(self, tree: Node) -> None:
        self.tree = tree

    def validate_all(self) -> None:
        self.variables = {} 
        self.methods = {}
        self.extends = {}
        self.dfs(self.tree, True, True, True)

    def replace_node(self, root: Node, id: str, replacement: Node) -> bool:
        if not root:
            return False

        for i, child in enumerate(root.children):
            if type(child) == Node:
                if child.value == id:
                    root.children[i] = replacement
                    return True
                
                if self.replace_node(child, id, replacement):
                    return True

        return False
    
    def find_extends(self, prog_node: Node) -> None:
        for child in prog_node.children:
            if child.label == "CLASSE":
                if child.children[1] != None:
                    self.extends[child.children[0].children[0]] = [child.children[1].children[0], child.children[0].children[0]]

    def dfs(self, node: Node, validate_variables: bool, validate_functions: bool, replace_constants: bool, owned_by: str = "") -> None:
        if not isinstance(node, Node):
            return
        
        if node.label == "VAR" or node.label == "MAIN" or node.label == "CLASSE" or node.label == "METODO":
            for id in node.get_identifiers():
                self.variables[id['name']] = id
                self.variables[id['name']]['owned_by'] = owned_by
            
        if validate_variables: self.validate_variable_declaration(node, owned_by)
        if validate_functions: self.validate_function_calls(node)

        if node.label == "PROG":
            node.children.reverse()
        elif node.label == "CLASSE":
            owned_by = node.children[0].children[0]
        for child in node.children:
            self.dfs(child, validate_variables, validate_functions, replace_constants, owned_by)

        if replace_constants: self.replace_constants(node)

    def validate_variable_declaration(self, node: Node, owned_by: str = "") -> None:
        for id in node.get_identifiers():
            if id['name'] not in self.variables:
                raise Exception(f"Tried using variable {id['name']} before declaration")
            #elif self.variables[id['name']]['owned_by'] not in self.extends[owned_by]:
            #    raise Exception(f"Variable {id['name']} is not declared in the current scope")

    def validate_function_calls(self, node: Node) -> None:
        if node.label == "PEXP" and node.type == "method_call":
            method = node.children[-2].children[0]
            params = node.children[-1].children
            filtered_dict = list({k: v for k, v in self.variables.items() if v.get("method") == method}.values())

            if len(filtered_dict) != len(params):
                raise Exception(f"Invalid number of parameters for method {method} @ {node}")
            
            for i, param in enumerate(params):
                type = "int" if param.are_there_numbers_involved() else "number"
                if type != filtered_dict[i]['dtype']:
                    raise Exception(f"Invalid type for parameter {i} in method {method} @ {node}")

    def replace_constants(self, node: Node) -> None:
        if (node.label == "MEXP" or node.label == "AEXP") and not node.are_there_variables_involved():
            self.replace_node(self.tree, node.value, Node("SEXP", [Node("number", [str(node.evaluate_bottom_expression())])]))
        elif (node.label == "REXP" or node.label == "EXP") and not node.are_there_variables_involved():
            self.replace_node(self.tree, node.value, Node("SEXP", [Node("boolean", [str(node.evaluate_bottom_expression())])]))
