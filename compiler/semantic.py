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
        print("Starting build_method_info")  # Debug print
        
        # First, ensure class_methods is initialized for all classes
        for child in prog_node.children:
            if child and child.label == "CLASSE":
                class_name = child.children[0].children[0]
                if class_name not in self.class_methods:
                    self.class_methods[class_name] = {}
                print(f"Found class: {class_name}")  # Debug print
        
        # Then collect method information
        for child in prog_node.children:
            if child and child.label == "CLASSE":
                class_name = child.children[0].children[0]
                print(f"Processing methods for class: {class_name}")  # Debug print
                
                # Find all methods in the class body
                for node in child.children:
                    if node and node.label == "METODO":
                        method_name = node.children[1].children[0]
                        print(f"Found method: {method_name}")  # Debug print
                        
                        # Get parameter information
                        params = []
                        if len(node.children) > 2 and node.children[2].label == "PARAMS":
                            params = [p for p in node.children[2].children if p.label == "identifier"]
                        
                        self.class_methods[class_name][method_name] = {
                            'params': len(params),
                            'node': node
                        }
                        print(f"Method {method_name} in class {class_name} has {len(params)} parameters")  # Debug print
        
        print("class_methods contents:")  # Debug print
        for class_name, methods in self.class_methods.items():
            print(f"{class_name}: {methods.keys()}")

    
    def dfs(self, node: Node, validate_variables: bool, validate_functions: bool, replace_constants: bool, owned_by: str = "") -> None:
        if not isinstance(node, Node):
            return
        
        if node.label == "VAR" or node.label == "MAIN" or node.label == "CLASSE" or node.label == "METODO":
            for id in node.get_identifiers():
                self.variables[id['name']] = id
                self.variables[id['name']]['owned_by'] = owned_by
                # Ensure the variable has type information
                if 'type' not in self.variables[id['name']]:
                    self.variables[id['name']]['type'] = self.infer_type(id)
                
        if validate_variables: self.validate_variable_declaration(node, owned_by)
        if validate_functions: self.validate_function_calls(node)

        if node.label == "PROG":
            node.children.reverse()
        elif node.label == "CLASSE":
            owned_by = node.children[0].children[0]
        for child in node.children:
            self.dfs(child, validate_variables, validate_functions, replace_constants, owned_by)

        if replace_constants: self.replace_constants(node)

    def infer_type(self, id: dict) -> str:
        """
        Infer the type of a variable based on its context and usage.
        """
        # Placeholder logic for type inference
        # This should be replaced with actual logic based on your language's type system

        # Example: Infer type based on variable name or initial value
        if 'value' in id:
            value = id['value']
            if isinstance(value, int):
                return "int"
            elif isinstance(value, float):
                return "float"
            elif isinstance(value, bool):
                return "boolean"
            elif isinstance(value, str):
                return "string"
        
        # Default to int if no other information is available
        return "int"


    def validate_variable_declaration(self, node: Node, owned_by: str = "") -> None:
        for id in node.get_identifiers():
            if id['name'] not in self.variables:
                raise Exception(f"Tried using variable {id['name']} before declaration")
            else:
                # Ensure the variable has type information
                if 'type' not in self.variables[id['name']]:
                    raise Exception(f"Variable {id['name']} does not have a type information")

    def validate_function_calls(self, node: Node) -> None:
        if node.label == "PEXP" and node.type == "method_call":
            method_name = node.children[-2].children[0]
            params = node.children[-1].children
            
            print(f"\nValidating method call: {method_name}")
            print(f"Parameters: {len(params)}")

            # Find the class context
            class_context = None
            
            # Get first child node for analysis
            first_child = node.children[0]
            print(f"First child: {first_child.label}")  # Debug print

            # Case 1: Method call on new instance (new Calculator())
            if hasattr(first_child, 'children') and len(first_child.children) > 1:
                if (first_child.children[0].label == "reserved" and 
                    first_child.children[0].children[0] == "new"):
                    class_context = first_child.children[1].children[0]
                    print(f"Found new instance of class: {class_context}")  # Debug print
            
            # Case 2: Method call using 'this'
            elif (hasattr(first_child, 'children') and 
                len(first_child.children) == 1 and 
                isinstance(first_child.children[0], Node) and
                first_child.children[0].label == "reserved" and 
                first_child.children[0].children[0] == "this"):
                class_context = self.get_current_scope(node)
                print(f"Found this reference in class: {class_context}")  # Debug print
            
            # Case 3: Method call on variable
            elif first_child.label == "identifier":
                var_name = first_child.children[0]
                # Get class context from current scope if variable type not found
                class_context = self.get_current_scope(node)
                print(f"Found variable reference: {var_name} in class: {class_context}")  # Debug print

                # Check if the variable is an instance of a class
                if var_name in self.variables:
                    var_info = self.variables[var_name]
                    if 'type' in var_info:
                        class_context = var_info['type']
                        print(f"Variable {var_name} is of type: {class_context}")  # Debug print
                    else:
                        raise Exception(f"Variable {var_name} does not have a type information")

            if not class_context:
                raise Exception(f"Cannot determine class context for method {method_name}")

            print(f"Final class context: {class_context}")  # Debug print

            # Check method in current class and parent classes
            method_found = False
            classes_to_check = [class_context] + self.extends.get(class_context, [])
            
            for class_name in classes_to_check:
                if class_name in self.class_methods:
                    if method_name in self.class_methods[class_name]:
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
