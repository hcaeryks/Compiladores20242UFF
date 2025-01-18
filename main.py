from compiler import Lexer, Parser, Semantic, CodeGen
from compiler.MIPSAssembler import MIPSAssembler
from compiler.OtimizadorMIPS import OtimizadorMIPS
from compiler.types import Node
#from graphviz import Digraph
import os

OUT_FOLDER = "./out/"
if not os.path.exists(OUT_FOLDER):
    os.makedirs(OUT_FOLDER)

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
    with open("./inputs/exemplo_1.txt", "r") as file:
        text = file.read()
    
    lexer = Lexer(text)
    lexer.tokenize()

    with open(os.path.join(OUT_FOLDER, "tokenized.txt"), "w") as token_file:
        for token in lexer.get_tokens():
            token_file.write(f"{token}\n")
    
    parser = Parser(lexer.get_tokens())
    tree = parser.parse()

    #graph = visualize_tree(tree)
    #graph.render(os.path.join(OUT_FOLDER, "aas"), format="png", cleanup=True)

    semantic = Semantic(tree)
    semantic.validate_all()

    codegen = CodeGen(tree)
    generated_code = codegen.generate_code()
    
    # Saida original MIPS
    with open(os.path.join(OUT_FOLDER, "output_code.txt"), "w") as code_file:
        code_file.write(generated_code)
    
    # Codigo MIPS otimizado
    otimizador = OtimizadorMIPS()
    codigo_otimizado = otimizador.otimizar(generated_code)
    
    with open(os.path.join(OUT_FOLDER, 'optimized_code.txt'), 'w') as f:
        f.write(codigo_otimizado)

    # Codigo de maquina
    assembler = MIPSAssembler()
    machine_code = assembler.assemble_file('optimized_code.txt')

    with open(os.path.join(OUT_FOLDER, 'output.bin'), 'wb') as f:
        for code in machine_code:
            f.write(code.to_bytes(4, byteorder='big'))
