from compiler import Lexer, Parser, Semantic, CodeGen
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
    with open("./inputs/exemplo_4.txt", "r") as file:
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
    
    with open("output_code.txt", "w") as code_file:
        code_file.write(generated_code)