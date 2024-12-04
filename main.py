from compiler import Lexer, Parser

if __name__ == "__main__":
    with open("input.txt", "r") as file:
        text = file.read()
    
    lexer = Lexer(text)
    lexer.tokenize()

    print(lexer.get_tokens())
