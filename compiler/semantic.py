from collections import defaultdict, deque
from .types import Node
from .types import Token

class Semantic():
    def __init__(self, tree: Node) -> None:
        self.tree = tree

    def validate_all(self) -> Node:
        self.variables = {}
        self.dependencies = []
        self.sort_ast()
        self.dfs(self.tree, True, True, True)
        for dep in self.dependencies:
            i1 = self.get_class_index_by_name(dep[0])
            i2 = self.get_class_index_by_name(dep[1])
            self.tree.children[i1].children = self.tree.children[i1].children[:2] + self.tree.children[i2].children[2:] + self.tree.children[i1].children[2:]
        return self.tree, self.dependencies

    def get_class_index_by_name(self, name: str) -> int:
        for i, child in enumerate(self.tree.children):
            if child.children[0].children[0] == name:
                return i

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

    def dfs(self, node: Node, validate_variables: bool, validate_functions: bool, replace_constants: bool, owned_by: str = "") -> None:
        if not isinstance(node, Node):
            return
        
        if node.label == "VAR" or node.label == "MAIN" or node.label == "CLASSE" or node.label == "METODO":
            for id in node.get_identifiers():
                self.variables[id['name']] = id
                self.variables[id['name']]['owned_by'] = owned_by
                #for dep in self.dependencies:
                #    if dep[1] == id['name']:
                #        self.variables[dep[0]] = id
                #        self.variables[dep[0]]['owned_by'] = owned_by
            
        if validate_variables: self.validate_variable_declaration(node, owned_by)
        if validate_functions: self.validate_function_calls(node)
        
        for child in node.children:
            if node.label == "CLASSE":
                owned_by = node.children[0].children[0]
                self.dfs(child, validate_variables, validate_functions, replace_constants, owned_by)
            else: 
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

    def extract_classes(self, root: Node) -> list:
        classes = []
        dependencies = []
        main_class = None

        for child in root.children:
            if child.label == 'MAIN':
                main_class = child
            elif child.label == 'CLASSE':
                class_name = child.children[0].children[0]
                extends = child.children[1].children[0] if len(child.children) > 1 and child.children[1] is not None else None
                classes.append((class_name, extends, child))
                if extends:
                    dependencies.append((class_name, extends))

        return classes, main_class, dependencies

    def topological_sort(self, classes, main_class) -> list:
        graph = defaultdict(list)
        in_degree = defaultdict(int)
        class_nodes = {}

        for class_name, extends, node in classes:
            class_nodes[class_name] = node
            if extends:
                graph[extends].append(class_name)
                in_degree[class_name] += 1
            if class_name not in in_degree:
                in_degree[class_name] = 0

        sorted_classes = []
        queue = deque([cls for cls in in_degree if in_degree[cls] == 0])

        while queue:
            current = queue.popleft()
            sorted_classes.append(class_nodes[current])
            for dependent in graph[current]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        if main_class:
            sorted_classes.append(main_class)

        return sorted_classes

    def sort_dependencies(self, classes, sorted_classes):
        class_order = {node.children[0].children[0]: i for i, node in enumerate(sorted_classes) if node.label != 'MAIN'}
        sorted_dependencies = sorted(
            [(class_name, extends) for class_name, extends, _ in classes if extends],
            key=lambda dep: (class_order[dep[0]], class_order[dep[1]])
        )
        return sorted_dependencies

    def sort_ast(self) -> None:
        classes, main_class, dependencies = self.extract_classes(self.tree)
        sorted_classes = self.topological_sort(classes, main_class)
        sorted_dependencies = self.sort_dependencies(classes, sorted_classes)
        self.tree.children = sorted_classes
        self.dependencies = sorted_dependencies