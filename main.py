from compiler import Lexer, Parser, Semantic, CodeGen
from compiler.MIPSAssembler import MIPSAssembler
from compiler.OtimizadorMIPS import OtimizadorMIPS
from compiler.types import Node
from graphviz import Digraph

def visualize_tree(node: Node, graph=None, parent=None):
    if graph is None:
        graph = Digraph()

    graph.node(node.value, label=node.label)

    if parent:
        graph.edge(parent, node.value)

    if type(node) is not Node:
        return graph
    for child in node.children:
        if type(child) is Node: visualize_tree(child, graph, node.value)

    return graph

if __name__ == "__main__":
    with open("./inputs/exemplo_3.txt", "r") as file:
        text = file.read()
    
    lexer = Lexer(text)
    lexer.tokenize()

    with open("tokenized.txt", "w") as token_file:
        for token in lexer.get_tokens():
            token_file.write(f"{token}\n")
    
    parser = Parser(lexer.get_tokens())
    tree = parser.parse()

    #graph = visualize_tree(tree)
    #graph.render("aas", format="png", cleanup=True)

    semantic = Semantic(tree)
    semantic.validate_all()

    codegen = CodeGen(tree)
    generated_code = codegen.generate_code()
    
    # Saida original MIPS
    with open("output_code.txt", "w") as code_file:
        code_file.write(generated_code)
    
    # Codigo MIPS otimizado
    otimizador = OtimizadorMIPS()
    codigo_otimizado = otimizador.otimizar(generated_code)
    
    with open('optimized_code.txt', 'w') as f:
        f.write(codigo_otimizado)

    # Codigo de maquina
    assembler = MIPSAssembler()
    machine_code = assembler.assemble_file('optimized_code.txt')

    with open('output.bin', 'wb') as f:
        for code in machine_code:
            f.write(code.to_bytes(4, byteorder='big'))
