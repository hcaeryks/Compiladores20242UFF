class PeepholeOptimizer:
    def __init__(self, code: str):
        self.code = code.split('\n')

    def optimize(self) -> str:
        self.remove_redundant_load_store()
        self.combine_adjacent_arithmetic()
        return '\n'.join(self.code)

    def remove_redundant_load_store(self) -> None:
        optimized_code = []
        i = 0
        while i < len(self.code):
            if i + 1 < len(self.code) and self.code[i].startswith('lw') and self.code[i + 1].startswith('sw'):
                lw_instr = self.code[i].split()
                sw_instr = self.code[i + 1].split()
                if lw_instr[1] == sw_instr[1] and lw_instr[2] == sw_instr[2]:
                    i += 2
                    continue
            optimized_code.append(self.code[i])
            i += 1
        self.code = optimized_code

    def combine_adjacent_arithmetic(self) -> None:
        optimized_code = []
        i = 0
        while i < len(self.code):
            if i + 1 < len(self.code) and self.code[i].startswith('add') and self.code[i + 1].startswith('add'):
                add_instr1 = self.code[i].split()
                add_instr2 = self.code[i + 1].split()
                if add_instr1[1] == add_instr2[2] and add_instr1[2] == add_instr2[1]:
                    combined_instr = f"add {add_instr1[1]}, {add_instr1[2]}, {add_instr2[2]}"
                    optimized_code.append(combined_instr)
                    i += 2
                    continue
            optimized_code.append(self.code[i])
            i += 1
        self.code = optimized_code