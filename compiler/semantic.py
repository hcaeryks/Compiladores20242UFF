from .types import Node
from .types import Token

class Semantic():
    def __init__(self, tree: Node) -> None:
        self.tree = tree
        self.variables = {}
        self.methods = {}
        self.extends = {}
        self.class_methods = {}

    def validate_all(self) -> None:
        self.find_extends(self.tree)  # Make sure to build inheritance info first
        self.build_method_info(self.tree)  # New: Build method information
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
        """Build inheritance information for all classes"""
        # Initialize with all classes first
        for child in prog_node.children:
            if child.label == "CLASSE":
                class_name = child.children[0].children[0]
                self.extends[class_name] = []
                self.class_methods[class_name] = {}

        # Then build inheritance chains
        for child in prog_node.children:
            if child.label == "CLASSE":
                class_name = child.children[0].children[0]
                if child.children[1] is not None:  # Has parent
                    parent_name = child.children[1].children[0]
                    # Include parent and all its parents in extends list
                    self.extends[class_name] = [parent_name]
                    current_parent = parent_name
                    while current_parent in self.extends and self.extends[current_parent]:
                        parent_of_parent = self.extends[current_parent][0]
                        self.extends[class_name].append(parent_of_parent)
                        current_parent = parent_of_parent

    def build_method_info(self, prog_node: Node) -> None:
        """Build method information for all classes"""
        for child in prog_node.children:
            if child and child.label == "CLASSE":  # Add check for None
                class_name = child.children[0].children[0]
                # Find all methods in the class
                for node in child.children:
                    if node and node.label == "METODO":  # Add check for None
                        method_name = node.children[1].children[0]
                        # Get parameter information
                        params = []
                        if len(node.children) > 2 and node.children[2].label == "PARAMS":
                            params = node.children[2].children
                        self.class_methods[class_name][method_name] = {
                            'params': len(params) // 2,  # Each param has type and name
                            'node': node
                        }

    
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
            method_name = node.children[-2].children[0]
            params = node.children[-1].children

            # Find the class context
            class_context = None
            if len(node.children[0].children) == 1:  # this case
                current_scope = self.get_current_scope(node)
                if current_scope:
                    class_context = current_scope
            else:  # new Class() case or method call on variable
                if node.children[0].label == "PEXP":
                    if (node.children[0].children[0].label == "reserved" and 
                        node.children[0].children[0].children[0] == "new"):
                        # Handle case of new Class().method()
                        class_context = node.children[0].children[1].children[0]
                elif node.children[0].label == "identifier":
                    # Handle case of variable.method()
                    var_name = node.children[0].children[0]
                    if var_name in self.variables:
                        class_context = self.variables[var_name]['type']
                    else:
                        # If not found in variables, check if it's a class name
                        class_context = var_name

            if not class_context:
                class_context = node.children[0].children[0]  # Fallback to first child

            if not class_context:
                raise Exception(f"Cannot determine class context for method {method_name}")

            # Check method in current class and parent classes
            method_found = False
            classes_to_check = [class_context] + self.extends.get(class_context, [])
            
            for class_name in classes_to_check:
                if class_name in self.class_methods and method_name in self.class_methods[class_name]:
                    method_found = True
                    expected_params = self.class_methods[class_name][method_name]['params']
                    if len(params) != expected_params:
                        raise Exception(f"Invalid number of parameters for method {method_name}. Expected {expected_params}, got {len(params)}")
                    break

            if not method_found:
                raise Exception(f"Method {method_name} not found in class {class_context} or its parent classes")


    def get_current_scope(self, node: Node) -> str:
        """Helper method to find the current class scope"""
        current = node
        while current:
            if current.label == "CLASSE":
                return current.children[0].children[0]
            current = current.parent if hasattr(current, 'parent') else None
        return None

    def replace_constants(self, node: Node) -> None:
        if (node.label == "MEXP" or node.label == "AEXP") and not node.are_there_variables_involved():
            self.replace_node(self.tree, node.value, Node("SEXP", [Node("number", [str(node.evaluate_bottom_expression())])]))
        elif (node.label == "REXP" or node.label == "EXP") and not node.are_there_variables_involved():
            self.replace_node(self.tree, node.value, Node("SEXP", [Node("boolean", [str(node.evaluate_bottom_expression())])]))
