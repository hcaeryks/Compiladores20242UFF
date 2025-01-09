# Mapeamento das instruções R-type
R_TYPE_INSTRUCTIONS = {
    'add': '100000',
    'sub': '100010',
    'and': '100100',
    'or': '100101',
    'slt': '101010',
    'jr': '001000'
}

# Mapeamento das instruções I-type
I_TYPE_INSTRUCTIONS = {
    'addi': '001000',
    'lw': '100011',
    'sw': '101011',
    'beq': '000100',
    'bne': '000101',
    'andi': '001100',
    'ori': '001101',
    'slti': '001010'
}

# Mapeamento das instruções J-type
J_TYPE_INSTRUCTIONS = {
    'j': '000010',
    'jal': '000011'
}

def register_to_bin(register: str) -> str:
    registers = {
        '$zero': '00000', '$at': '00001', '$v0': '00010', '$v1': '00011',
        '$a0': '00100', '$a1': '00101', '$a2': '00110', '$a3': '00111',
        '$t0': '01000', '$t1': '01001', '$t2': '01010', '$t3': '01011',
        '$t4': '01100', '$t5': '01101', '$t6': '01110', '$t7': '01111',
        '$s0': '10000', '$s1': '10001', '$s2': '10010', '$s3': '10011',
        '$s4': '10100', '$s5': '10101', '$s6': '10110', '$s7': '10111',
        '$t8': '11000', '$t9': '11001', '$k0': '11010', '$k1': '11011',
        '$gp': '11100', '$sp': '11101', '$fp': '11110', '$ra': '11111'
    }
    return registers.get(register, '00000')

def to_binary(instruction: str, labels: dict) -> str:
    parts = instruction.split()
    opcode = parts[0]

    if opcode in R_TYPE_INSTRUCTIONS:
        if len(parts) != 4:
            raise ValueError(f"Invalid R-type instruction format: {instruction}")
        funct = R_TYPE_INSTRUCTIONS[opcode]
        rs = register_to_bin(parts[2])
        rt = register_to_bin(parts[3])
        rd = register_to_bin(parts[1])
        shamt = '00000'
        return f"000000{rs}{rt}{rd}{shamt}{funct}"

    elif opcode in I_TYPE_INSTRUCTIONS:
        if opcode in ['lw', 'sw']:
            if len(parts) != 3:
                raise ValueError(f"Invalid I-type instruction format: {instruction}")
            rt = register_to_bin(parts[1])
            offset_base = parts[2].split('(')
            offset = format(int(labels.get(offset_base[0], offset_base[0])), '016b')
            base = register_to_bin(offset_base[1][:-1])
            opcode_bin = I_TYPE_INSTRUCTIONS[opcode]
            return f"{opcode_bin}{base}{rt}{offset}"
        else:
            if len(parts) != 4:
                raise ValueError(f"Invalid I-type instruction format: {instruction}")
            opcode_bin = I_TYPE_INSTRUCTIONS[opcode]
            rt = register_to_bin(parts[1])
            rs = register_to_bin(parts[2])
            immediate = format(int(labels.get(parts[3], parts[3])), '016b')
            return f"{opcode_bin}{rs}{rt}{immediate}"

    elif opcode in J_TYPE_INSTRUCTIONS:
        if len(parts) != 2:
            raise ValueError(f"Invalid J-type instruction format: {instruction}")
        opcode_bin = J_TYPE_INSTRUCTIONS[opcode]
        address = format(int(labels.get(parts[1], parts[1])), '026b')
        return f"{opcode_bin}{address}"

    elif opcode == 'li':
        if len(parts) != 3:
            raise ValueError(f"Invalid li instruction format: {instruction}")
        rt = register_to_bin(parts[1])
        immediate = format(int(parts[2]), '016b')
        return f"00110100000{rt}{immediate}"  # ori rt, $zero, immediate

    elif opcode == 'move':
        if len(parts) != 3:
            raise ValueError(f"Invalid move instruction format: {instruction}")
        rd = register_to_bin(parts[1])
        rs = register_to_bin(parts[2])
        return f"000000{rs}00000{rd}00000{R_TYPE_INSTRUCTIONS['add']}"  # add rd, rs, $zero

    elif opcode == 'syscall':
        return '00000000000000000000000000001100'  # syscall

    elif opcode == 'jr':
        if len(parts) != 2:
            raise ValueError(f"Invalid jr instruction format: {instruction}")
        rs = register_to_bin(parts[1])
        return f"000000{rs}00000000000000000100000"  # jr rs

    else:
        raise ValueError(f"Unsupported instruction: {instruction}")

def convert_to_binary(assembly_code: str) -> str:
    binary_code = []
    labels = {}
    address = 0

    # First pass: collect labels
    for line in assembly_code.split('\n'):
        line = line.strip()
        if line.endswith(':'):
            labels[line[:-1]] = address
        else:
            address += 4

    # Second pass: convert instructions to binary
    for line in assembly_code.split('\n'):
        line = line.strip()
        if line and not line.startswith('#') and not line.startswith('.') and not line.endswith(':') and not '.word' in line:
            try:
                binary_code.append(to_binary(line, labels))
            except ValueError as e:
                print(f"Error converting instruction to binary: {e}")
    return '\n'.join(binary_code)