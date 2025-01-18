from .types import Node
import re

class CodeGen():
    def __init__(self, tree: Node) -> None:
        self.tree = tree
        self.data_section = []
        self.text_section = []
        self.additional_section = []
        self.variables = {}
        self.instancescope = None
        self.current_scope = "" # formato ClassName.MethodName
        self.current_scope_max_offset_params = {}
        self.current_scope_max_offset = {}
        self.global_label_counter = 0
        self.arrays = {}
        self.arrays_size = {}
        self.next_array_register = 3
        self.class_hierarchy = {}  # class names -> parent class names
        self.inherited_methods = {}  # class names -> inherited methods
        self.inherited_variables = {} # class names -> inherited variables

    def build_inheritance_tree(self):
        """Build the inheritance tree from the AST"""
        for child in self.tree.children:
            if child.label == "CLASSE":
                class_name = child.children[0].children[0]
                parent_node = child.children[1]
                parent_name = parent_node.children[0] if parent_node else None
                
                self.class_hierarchy[class_name] = parent_name
                self.inherited_methods[class_name] = {}
                self.inherited_variables[class_name] = {}
                
                if parent_name:
                    # Copiar metodos e variaveis da parent class
                    self._copy_inherited_members(class_name, parent_name)
    
    def _copy_inherited_members(self, child_class: str, parent_class: str):
        """Copy inherited methods and variables from parent to child class"""
        # Copy parent's methods
        if parent_class in self.variables:
            for method_name, method_info in self.variables[parent_class].items():
                if isinstance(method_info, dict):  # It's a method
                    self.inherited_methods[child_class][method_name] = {
                        'parent': parent_class,
                        'offset': method_info
                    }

            # Copy parent's variables
            for var_name, var_offset in self.variables[parent_class].items():
                if not isinstance(var_offset, dict):  # It's a variable
                    self.inherited_variables[child_class][var_name] = {
                        'parent': parent_class,
                        'offset': var_offset
                    }

        # Recursively copy from grandparent if exists
        if parent_class in self.class_hierarchy and self.class_hierarchy[parent_class]:
            self._copy_inherited_members(child_class, self.class_hierarchy[parent_class])
    
    def _resolve_method(self, class_name: str, method_name: str) -> str:
        """Resolve method to the correct class in the inheritance chain"""
        current_class = class_name
        while current_class:
            # Check if method exists in current class
            if (current_class in self.variables and 
                method_name in self.variables[current_class]):
                return f"{current_class}.{method_name}"
            
            # Check inherited methods
            if (current_class in self.inherited_methods and 
                method_name in self.inherited_methods[current_class]):
                parent_class = self.inherited_methods[current_class][method_name]['parent']
                return f"{parent_class}.{method_name}"
            
            # Move up the inheritance chain
            current_class = self.class_hierarchy.get(current_class)
            
        return f"{class_name}.{method_name}"  # Fallback to original class

    def generate_code(self) -> str:
        self.build_inheritance_tree()
        self._cgen(self.tree)
        main_index = next((i for i, line in enumerate(self.text_section) if line.strip() == "main:"), None)
        if main_index is not None:
            main_and_after = self.text_section[main_index:]
            self.text_section = main_and_after + self.text_section[:main_index]
        data = "\n".join(self.data_section)
        text = "\n".join(self.text_section)
        additional = "\n".join(self.additional_section)
        return f".data\n{data}\n.text\n.globl main\n{text}\n\n{additional}"

    def yield_error(self, message: str, tree: Node) -> None:
        self.text_section.append(f"# ERROR: {message} @ {tree}")

    def _cgen(self, tree: Node) -> None:
        if hasattr(self, f"assemble_{tree.label}"):
            func = getattr(self, f"assemble_{tree.label}")
            if callable(func):
                func(tree)
        else:
            self.yield_error(f"assemble_{tree.label} function not found", tree)

    def assemble_PROG(self, tree: Node) -> None:
        for child in tree.children:
            self._cgen(child)
    
    def assemble_MAIN(self, tree: Node) -> None:
        self.current_scope = "main.main"
        self.current_scope_max_offset_params[self.current_scope] = 4
        self.current_scope_max_offset[self.current_scope] = 0
        self.variables[self.current_scope] = {}
        self.text_section.append("\nmain:")
        self.text_section.append("\tsw $fp, 0($sp)")
        self.text_section.append("\tmove $fp, $sp")
        self.text_section.append("\tsw $ra, -4($sp)")
        self.text_section.append("\taddiu $sp, $sp, -8")
        
        for child in tree.children[2:]:
            self._cgen(child)
        
        self.text_section.append("\tlw $ra, -4($fp)")
        self.text_section.append("\tmove $sp, $fp")
        self.text_section.append("\tlw $fp, 0($fp)")
        self.text_section.append("\tli $v0, 10")
        self.text_section.append("\tsyscall")

    def assemble_CLASSE(self, tree: Node) -> None:
        """Modified CLASSE assembly to handle inheritance"""
        self.current_scope = f"{tree.children[0].children[0]}"
        self.variables[self.current_scope] = {}
        
        # Handle inheritance
        parent_node = tree.children[1]
        if parent_node:
            parent_name = parent_node.children[0]
            self.class_hierarchy[self.current_scope] = parent_name
            
            # Initialize inheritance tracking for this class
            if self.current_scope not in self.inherited_methods:
                self.inherited_methods[self.current_scope] = {}
            if self.current_scope not in self.inherited_variables:
                self.inherited_variables[self.current_scope] = {}
            
            # Copy inherited members
            self._copy_inherited_members(self.current_scope, parent_name)

        self.text_section.append(f"\n{self.current_scope}:")
        for child in tree.children[2:]:
            self._cgen(child)

    def assemble_VAR(self, tree: Node) -> None:
        for child in tree.children[1::2]:
            name = child.children[0]
            if len(self.current_scope.split('.')) > 1:
                self.current_scope_max_offset[self.current_scope] -= 4
                offset = self.current_scope_max_offset[self.current_scope]
                self.variables[self.current_scope.split('.')[0]][self.current_scope.split('.')[1]][name] = offset
                self.text_section.append(f"\taddiu $sp, $sp, -4")
            else:    
                self.variables[self.current_scope][name] = self.current_scope_max_offset[self.current_scope]
                self.data_section.append(f"{name}: .word 0")
                self.current_scope_max_offset[self.current_scope] += 4

    def assemble_PARAMS(self, tree: Node) -> None:
        i = 0
        for child in tree.children[1::2]:
            name = child.children[0]
            offset = 4 + (i * 4)
            self.variables[self.current_scope.split('.')[0]][self.current_scope.split('.')[1]][name] = offset
            self.text_section.append(f"\tlw $a0, {offset}($fp)")
            i += 1

    def assemble_METODO(self, tree: Node) -> None:
        metodo_name = tree.children[1].children[0]
        self.variables[self.current_scope][metodo_name] = {}
        self.current_scope = f"{self.current_scope}.{metodo_name}"
        self.current_scope_max_offset_params[self.current_scope] = 0
        self.current_scope_max_offset[self.current_scope] = -8
        
        self.text_section.append(f"{self.current_scope}:")
        self.text_section.append("\tsw $fp, 0($sp)")
        self.text_section.append("\tmove $fp, $sp")
        self.text_section.append("\tsw $ra, -4($sp)")
        self.text_section.append("\taddiu $sp, $sp, -12")

        for child in tree.children[2:]:
            self._cgen(child)

        self.text_section.append("\tmove $v0, $a0")
        self.text_section.append("\tlw $ra, -4($fp)")
        self.text_section.append("\tmove $sp, $fp")
        self.text_section.append("\tlw $fp, 0($fp)")
        self.text_section.append("\tjr $ra")

    def assemble_CMD(self, tree: Node) -> None:
        if tree.children[0].label == "System.out.println":
            self._cgen(tree.children[0].children[0])
            self.text_section.append("\tli $v0, 1")
            self.text_section.append("\tsyscall")
        elif tree.children[0].label == "CMD":
            for child in tree.children:
                self._cgen(child)
        elif tree.children[0].label == "if":
            if len(tree.children) == 2:
                cnt1 = self.global_label_counter
                cnt2 = self.global_label_counter + 1
                self.global_label_counter += 2

                self._cgen(tree.children[0].children[0])
                self.text_section.append(f"\tbeqz $a0, false_branch{cnt1}")
                self._cgen(tree.children[0].children[1])
                self.text_section.append(f"\tb end_if{cnt2}")
                self.text_section.append(f"false_branch{cnt1}:")
                self._cgen(tree.children[1].children[0])
                self.text_section.append(f"end_if{cnt2}:")
            else:
                self._cgen(tree.children[0].children[0])
                self.text_section.append(f"\tbeqz $a0, end_if{self.global_label_counter}")
                self._cgen(tree.children[0].children[1])
                self.text_section.append(f"end_if{self.global_label_counter}:")
        elif tree.children[0].label == "while":
            cnt1 = self.global_label_counter
            cnt2 = self.global_label_counter + 1
            self.global_label_counter += 2

            self.text_section.append(f"while{cnt1}:")
            self._cgen(tree.children[0].children[0])
            self.text_section.append(f"\tbeqz $a0, end_while{cnt2}")
            self._cgen(tree.children[0].children[1])
            self.text_section.append(f"\tb while{cnt1}")
            self.text_section.append(f"end_while{cnt2}:")
        elif len(tree.children) == 3 and tree.children[2].type == "array_init":
            self._cgen(tree.children[2].children[2])
            self.arrays[tree.children[0].children[0]] = self.next_array_register
            self.next_array_register += 1
            self.text_section.append(f"\tmove $t0, $a0")
            self.text_section.append("\tadd $a0, $a0, $a0")
            self.text_section.append("\tadd $a0, $a0, $a0")
            self.text_section.append("\tli $v0, 9")
            self.text_section.append("\tsyscall")
            self.text_section.append(f"\tmove $t{self.arrays[tree.children[0].children[0]]}, $v0")
            self.text_section.append("\tsw $t0, 0($v0)")
        elif len(tree.children) == 4 and tree.type == "array_assign":
            base = self.arrays[tree.children[0].children[0]]
            self._cgen(tree.children[1])
            self.text_section.append("\tadd $a0, $a0, $a0")
            self.text_section.append("\tadd $a0, $a0, $a0")
            self.text_section.append("\taddiu $a0, $a0, 4")
            self.text_section.append("\tsw $a0, 0($sp)")
            self.text_section.append("\taddiu $sp, $sp, -4")
            self._cgen(tree.children[3])
            self.text_section.append("\tlw $t0, 4($sp)")
            self.text_section.append("\taddiu $sp, $sp, 4")
            self.text_section.append(f"\tadd $t1, $t0, $t{base}")
            self.text_section.append("\tsw $a0, 0($t1)")
        elif tree.children[0].label == "identifier" and len(tree.children) == 3:
            self._cgen(tree.children[2])
            name = tree.children[0].children[0]
            scope = self.current_scope.split('.')
            if len(scope) > 1:
                offset = self.variables[scope[0]][scope[1]][name]
                self.text_section.append(f"\tsw $a0, {offset}($fp)")
            else:
                self.text_section.append(f"\tsw $a0, {self.variables[self.current_scope][name]}")
        
    def assemble_identifier(self, tree: Node) -> None:
        name = tree.children[0]
        scope_to_use = self.current_scope if self.instancescope == None else self.instancescope
        
        if len(scope_to_use.split('.')) > 1:
            if name in self.variables[scope_to_use.split('.')[0]][scope_to_use.split('.')[1]]:
                self.text_section.append(f"\tlw $a0, {self.variables[scope_to_use.split('.')[0]][scope_to_use.split('.')[1]][name]}($fp)")
            else:
                self.yield_error(f"Variable {name} not found in scope {scope_to_use}", tree)
        else:
            if name in self.variables[scope_to_use]:
                self.text_section.append(f"\tlw $a0, {self.variables[scope_to_use][name]}($fp)")
            else:
                self.yield_error(f"Variable {name} not found in scope {scope_to_use}", tree)

    def assemble_SEXP(self, tree: Node) -> None:
        # PRECISA FAZER CASOS ONDE É UM ARRAY, MAIS UM ELIF
        if tree.children[0].label == "boolean":
            val = 1 if tree.children[0].children[0].lower() == "true" else 0
            self.text_section.append(f"\tli $a0, {val}")
        elif tree.children[0].label == "number":
            val = tree.children[0].children[0]
            self.text_section.append(f"\tli $a0, {val}")
        elif tree.children[0].children[0] == "null":
            self.text_section.append("\tmove $a0, $zero")
        else:
            self._cgen(tree.children[0])

    def assemble_AEXP(self, tree: Node) -> None:
        self._cgen(tree.children[0])
        self.text_section.append("\tsw $a0, 0($sp)")
        self.text_section.append("\taddiu $sp, $sp, -4")
        self._cgen(tree.children[2])
        self.text_section.append("\tlw $t1, 4($sp)")
        if tree.children[1].children[0] == "+":
            self.text_section.append("\tadd $a0, $t1, $a0")
        elif tree.children[1].children[0] == "-":
            self.text_section.append("\tsub $a0, $t1, $a0")
        self.text_section.append("\taddiu $sp, $sp, 4")

    def assemble_MEXP(self, tree: Node) -> None:
        self._cgen(tree.children[0])
        self.text_section.append("\tsw $a0, 0($sp)")
        self.text_section.append("\taddiu $sp, $sp, -4")
        
        self._cgen(tree.children[2])
        
        self.text_section.append("\tlw $t1, 4($sp)")
        self.text_section.append("\tmul $a0, $t1, $a0")
        self.text_section.append("\taddiu $sp, $sp, 4")

    def assemble_EXPS(self, tree: Node) -> None:
        for child in tree.children:
            self._cgen(child)

    def assemble_EXP(self, tree: Node) -> None:
        self._cgen(tree.children[0])
        self.text_section.append("\tsw $a0, 0($sp)")
        self.text_section.append("\taddiu $sp, $sp, -4")
        self._cgen(tree.children[2])
        self.text_section.append("\tlw $t1, 4($sp)")
        self.text_section.append("\tand $a0, $t1, $a0")
        self.text_section.append("\taddiu $sp, $sp, 4")

    def assemble_PEXP(self, tree: Node) -> None:
        if tree.type == "array_length":
            base = self.arrays[tree.children[0].children[0]]
            self.text_section.append(f"\tlw $a0, 0($t{base})")
            return

        if tree.children[0].label == "identifier" and len(tree.children) == 2:
            base = self.arrays[tree.children[0].children[0]]
            self._cgen(tree.children[1])
            self.text_section.append("\tadd $a0, $a0, $a0")
            self.text_section.append("\tadd $a0, $a0, $a0")
            self.text_section.append("\taddiu $a0, $a0, 4")
            self.text_section.append(f"\tadd $t0, $a0, $t{base}")
            self.text_section.append("\tlw $a0, 0($t0)")
            return

        if tree.type == "method_call":
            whereweat = None
            if len(tree.children[0].children) == 1:  # caso this
                whereweat = self.current_scope.split('.')[0]
            else:  # caso new
                whereweat = tree.children[0].children[1].children[0]
            
            funcname = tree.children[1].children[0]
            # Use method resolution
            path = self._resolve_method(whereweat, funcname)
            
            self.text_section.append("\tsw $a0, 0($sp)")
            self.text_section.append("\taddiu $sp, $sp, -4")
            
            for child in tree.children[-1].children[::-1]:
                self._cgen(child)
                self.text_section.append("\tsw $a0, 0($sp)")
                self.text_section.append("\taddiu $sp, $sp, -4")
            
            self.text_section.append("\tjal " + path)
            
            if tree.children[-1].children:
                self.text_section.append(f"\taddiu $sp, $sp, {4 * len(tree.children[-1].children)}")
            
            self.text_section.append("\tmove $a0, $v0")
            
            self.text_section.append("\tlw $t1, 4($sp)")
            self.text_section.append("\taddiu $sp, $sp, 4")
            self.text_section.append("\tsw $t1, 0($sp)")
            self.text_section.append("\taddiu $sp, $sp, -4")

        if len(tree.children) == 1:
            self._cgen(tree.children[0])
            return

    def assemble_REXP(self, tree: Node) -> None:
        self._cgen(tree.children[0])
        self.text_section.append("\tsw $a0, 0($sp)")
        self.text_section.append("\taddiu $sp, $sp, -4")
        
        self._cgen(tree.children[2])
        
        self.text_section.append("\tlw $t1, 4($sp)")
        if tree.children[1].children[0] == "<":
            self.text_section.append("\tslt $a0, $t1, $a0")
        elif tree.children[1].children[0] == "==":
            self.text_section.append("\tseq $a0, $t1, $a0")
        elif tree.children[1].children[0] == "!=":
            self.text_section.append("\tsne $a0, $t1, $a0")
        self.text_section.append("\taddiu $sp, $sp, 4")

    def assemble_RETURN(self, tree: Node) -> None:
        self._cgen(tree.children[0])
        self.text_section.append("\tmove $v0, $a0")