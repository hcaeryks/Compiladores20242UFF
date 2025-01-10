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

    def generate_code(self) -> str:
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
        # Add frame setup
        self.text_section.append("\tsw $fp, 0($sp)")
        self.text_section.append("\tmove $fp, $sp")
        self.text_section.append("\tsw $ra, -4($sp)")
        self.text_section.append("\taddiu $sp, $sp, -8")
        
        for child in tree.children[2:]:
            self._cgen(child)
        
        # Add frame cleanup before exit
        self.text_section.append("\tlw $ra, -4($fp)")
        self.text_section.append("\tmove $sp, $fp")
        self.text_section.append("\tlw $fp, 0($fp)")
        self.text_section.append("\tli $v0, 10")
        self.text_section.append("\tsyscall")

    def assemble_CLASSE(self, tree: Node) -> None:
        self.current_scope = f"{tree.children[0].children[0]}"
        self.variables[self.current_scope] = {}
        self.text_section.append(f"\n{self.current_scope}:")
        for child in tree.children[2:]:
            self._cgen(child)

    def assemble_VAR(self, tree: Node) -> None:
        for child in tree.children[1::2]:
            name = child.children[0]
            if len(self.current_scope.split('.')) > 1:
                # Local variables start at -8($fp) after $ra and saved $fp
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
            offset = 4 + (i * 4)  # Parameters start at 4($fp)
            self.variables[self.current_scope.split('.')[0]][self.current_scope.split('.')[1]][name] = offset
            self.text_section.append(f"\tlw $a0, {offset}($fp)")
            i += 1

    def assemble_METODO(self, tree: Node) -> None:
        metodo_name = tree.children[1].children[0]
        self.variables[self.current_scope][metodo_name] = {}
        self.current_scope = f"{self.current_scope}.{metodo_name}"
        self.current_scope_max_offset_params[self.current_scope] = 0
        self.current_scope_max_offset[self.current_scope] = -8  # Start after $ra and $fp
        
        self.text_section.append(f"{self.current_scope}:")
        self.text_section.append("\tsw $fp, 0($sp)")
        self.text_section.append("\tmove $fp, $sp")
        self.text_section.append("\tsw $ra, -4($sp)")
        self.text_section.append("\taddiu $sp, $sp, -12")  # Space for $ra, $fp, and locals

        for child in tree.children[2:]:
            self._cgen(child)

        # Before returning, move result from $a0 to $v0
        self.text_section.append("\tmove $v0, $a0")
        self.text_section.append("\tlw $ra, -4($fp)")
        self.text_section.append("\tmove $sp, $fp")
        self.text_section.append("\tlw $fp, 0($fp)")
        self.text_section.append("\tjr $ra")

    def assemble_CMD(self, tree: Node) -> None:
        if tree.children[0].label == "System.out.println":
            self._cgen(tree.children[0].children[0])
            self.text_section.append("\tmove $a0, $v0")  # Only one move needed
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
        elif tree.children[0].label == "identifier" and len(tree.children) == 3:
            # Handle assignment
            self._cgen(tree.children[2])
            name = tree.children[0].children[0]
            scope = self.current_scope.split('.')
            if len(scope) > 1:
                offset = self.variables[scope[0]][scope[1]][name]
                self.text_section.append(f"\tsw $a0, {offset}($fp)")
            else:
                # Global variable case remains the same
                self.text_section.append(f"\tsw $a0, {self.variables[self.current_scope][name]}")
        else:
            # CASO ARRAY
            pass
        

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
        # First operand (num)
        self._cgen(tree.children[0])
        self.text_section.append("\tsw $a0, 0($sp)")
        self.text_section.append("\taddiu $sp, $sp, -4")
        
        # Second operand (recursive call result)
        self._cgen(tree.children[2])
        
        # Multiply
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
        if len(tree.children) == 1 and tree.children[0].label == "PEXP":
            self._cgen(tree.children[0])
            return
        
        if tree.type == "method_call":
            whereweat = None
            if len(tree.children[0].children) == 1:  # caso this
                whereweat = self.current_scope.split('.')[0]
            else:  # caso new
                whereweat = tree.children[0].children[1].children[0]
            funcname = tree.children[1].children[0]
            path = f"{whereweat}.{funcname}"
            
            # Save current $a0 if needed
            self.text_section.append("\tsw $a0, 0($sp)")
            self.text_section.append("\taddiu $sp, $sp, -4")
            
            # Process and push arguments
            for child in tree.children[-1].children[::-1]:
                self._cgen(child)
                self.text_section.append("\tsw $a0, 0($sp)")
                self.text_section.append("\taddiu $sp, $sp, -4")
            
            # Make the call
            self.text_section.append("\tjal " + path)
            
            # Clean up arguments
            if tree.children[-1].children:
                self.text_section.append(f"\taddiu $sp, $sp, {4 * len(tree.children[-1].children)}")
            
            # Restore result to $a0
            self.text_section.append("\tmove $a0, $v0")
            
            # Restore saved $a0 if needed
            self.text_section.append("\tlw $t1, 4($sp)")
            self.text_section.append("\taddiu $sp, $sp, 4")
            self.text_section.append("\tsw $t1, 0($sp)")
            self.text_section.append("\taddiu $sp, $sp, -4")

    def assemble_REXP(self, tree: Node) -> None:
        # First operand
        self._cgen(tree.children[0])
        self.text_section.append("\tsw $a0, 0($sp)")
        self.text_section.append("\taddiu $sp, $sp, -4")
        
        # Second operand
        self._cgen(tree.children[2])
        
        # Compare
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
        self.text_section.append("\tmove $v0, $a0")  # Move result to return value register