import re

class MIPSAssembler:
    def __init__(self):
        # R-type
        self.r_type = {
            'add': {'funct': 0x20, 'opcode': 0x0},
            'sub': {'funct': 0x22, 'opcode': 0x0},
            'mul': {'funct': 0x18, 'opcode': 0x0},
            'slt': {'funct': 0x2a, 'opcode': 0x0},
            'jr':  {'funct': 0x08, 'opcode': 0x0}
        }
        
        # I-type
        self.i_type = {
            'addi':  0x8,
            'addiu': 0x9,
            'beqz':  0x4,
            'beq':   0x4,
            'li':    0x8,
            'lw':    0x23,
            'sw':    0x2b
        }

        # J-type
        self.j_type = {
            'j':   0x2,
            'jal': 0x3
        }
        
        self.pseudo_instructions = {
            'move': 'add {}, $zero, {}',  # move rd, rs -> add rd, $zero, rs
            'b': 'beq $zero, $zero, {}',  # b label -> beq $zero, $zero, label
        }
        
        # Mapa de registers
        self.registers = {
            '$zero': 0,  '$0': 0,
            '$at': 1,    '$1': 1,
            '$v0': 2,    '$2': 2,    '$v1': 3,    '$3': 3,
            '$a0': 4,    '$4': 4,    '$a1': 5,    '$5': 5,
            '$a2': 6,    '$6': 6,    '$a3': 7,    '$7': 7,
            '$t0': 8,    '$8': 8,    '$t1': 9,    '$9': 9,
            '$t2': 10,   '$10': 10,  '$t3': 11,   '$11': 11,
            '$t4': 12,   '$12': 12,  '$t5': 13,   '$13': 13,
            '$t6': 14,   '$14': 14,  '$t7': 15,   '$15': 15,
            '$s0': 16,   '$16': 16,  '$s1': 17,   '$17': 17,
            '$s2': 18,   '$18': 18,  '$s3': 19,   '$19': 19,
            '$s4': 20,   '$20': 20,  '$s5': 21,   '$21': 21,
            '$s6': 22,   '$22': 22,  '$s7': 23,   '$23': 23,
            '$t8': 24,   '$24': 24,  '$t9': 25,   '$25': 25,
            '$k0': 26,   '$26': 26,  '$k1': 27,   '$27': 27,
            '$gp': 28,   '$28': 28,  '$sp': 29,   '$29': 29,
            '$fp': 30,   '$30': 30,  '$ra': 31,   '$31': 31
        }
        
        self.labels = {}
        self.current_address = 0
        self.instructions = []  # Instruções pra segunda passada

    def parse_register(self, reg):
        if reg in self.registers:
            return self.registers[reg]
        raise ValueError(f"Registrador invalido: {reg}")

    def parse_immediate(self, imm):
        try:
            if imm.startswith('0x'):
                return int(imm, 16)
            return int(imm)
        except ValueError:
            if imm in self.labels:
                # Offset relativo pra instruções de branch
                offset = (self.labels[imm] - self.current_address - 4) // 4
                return offset
            raise ValueError(f"Valor imediato invalido: {imm}")

    def expand_pseudo_instruction(self, line):
        """Expandir pseudo-instrucoes para instrucoes reais"""
        parts = re.split(r'[\s,]+', line.strip())
        op = parts[0].lower()
        
        if op in self.pseudo_instructions:
            if op == 'move':
                return self.pseudo_instructions[op].format(parts[1], parts[2])
            elif op == 'b':
                return self.pseudo_instructions[op].format(parts[1])
        return line

    def first_pass(self, lines):
        """Primeira passada para coletar enderecos dos labels"""
        address = 0
        for line in lines:
            line = line.strip()
            if not line or line.startswith('.'):
                continue
                
            if ':' in line:
                label = line.split(':')[0].strip()
                self.labels[label] = address
            else:
                # Instruções pra segunda passada
                self.instructions.append((address, line))
                address += 4
        return address

    def assemble_instruction(self, line, address):
        """Converter uma instrucao unica para codigo de maquina"""
        self.current_address = address
        line = line.strip()
        if not line or line.startswith('.') or ':' in line:
            return None
            
        # Remover comentarios
        line = line.split('#')[0].strip()
        
        line = self.expand_pseudo_instruction(line)
        
        # Fazer parse na instrucao
        parts = re.split(r'[\s,]+', line)
        op = parts[0].lower()
        
        try:
            # R-type
            if op in self.r_type:
                if op == 'jr':
                    rs = self.parse_register(parts[1])
                    return (self.r_type[op]['opcode'] << 26) | (rs << 21) | self.r_type[op]['funct']
                else:
                    rd = self.parse_register(parts[1])
                    rs = self.parse_register(parts[2])
                    rt = self.parse_register(parts[3]) if len(parts) > 3 else 0
                    return (self.r_type[op]['opcode'] << 26) | (rs << 21) | (rt << 16) | (rd << 11) | self.r_type[op]['funct']

            # I-type
            elif op in self.i_type:
                if op in ['lw', 'sw']:
                    # Operacoes na memoria tipo lw $t0, offset($sp)
                    rt = self.parse_register(parts[1])
                    offset_base = parts[2].replace(')', '').split('(')
                    imm = self.parse_immediate(offset_base[0])
                    rs = self.parse_register(offset_base[1])
                    return (self.i_type[op] << 26) | (rs << 21) | (rt << 16) | (imm & 0xFFFF)
                elif op == 'beqz':
                    rs = self.parse_register(parts[1])
                    imm = self.parse_immediate(parts[2])
                    rt = 0  # $zero
                    return (self.i_type[op] << 26) | (rs << 21) | (rt << 16) | (imm & 0xFFFF)
                else:
                    rt = self.parse_register(parts[1])
                    if op == 'li':
                        rs = 0  # $zero
                        imm = self.parse_immediate(parts[2])
                    else:
                        rs = self.parse_register(parts[2])
                        imm = self.parse_immediate(parts[3]) if len(parts) > 2 else 0
                    return (self.i_type[op] << 26) | (rs << 21) | (rt << 16) | (imm & 0xFFFF)

            # J-type
            elif op in self.j_type:
                target = parts[1]
                if target in self.labels:
                    target_address = self.labels[target] >> 2  # Converter para endereco word
                    return (self.j_type[op] << 26) | (target_address & 0x3FFFFFF)
                raise ValueError(f"Label desconhecido: {target}")

            # Syscall
            elif op == 'syscall':
                return 0x0000000c

            else:
                raise ValueError(f"Instrucao desconhecida: {op}")

        except Exception as e:
            print(f"Erro ao fazer o assemble da instrucao '{line}': {str(e)}")
            return None

    def assemble_file(self, filename):
        """Arquivo Assembly MIPS para codigo de maquina"""
        with open(filename, 'r') as f:
            lines = f.readlines()
            
        # Primeira passada para coletar labels
        self.first_pass(lines)
        
        # Segunda passada para gerar codigo de maquina
        machine_code = []
        for address, line in self.instructions:
            instruction = self.assemble_instruction(line, address)
            if instruction is not None:
                machine_code.append(instruction)
                
        return machine_code

def main():
    assembler = MIPSAssembler()
    machine_code = assembler.assemble_file('output_code.txt')
    
    # Printar codigo de maquina em formato hexadecimal
    print("Codigo de maquina:")
    for i, code in enumerate(machine_code):
        print(f"0x{code:08x}")
        
    # Salvando para arquivo binario
    with open('output.bin', 'wb') as f:
        for code in machine_code:
            f.write(code.to_bytes(4, byteorder='big'))

if __name__ == "__main__":
    main()