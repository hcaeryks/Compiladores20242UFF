from dataclasses import dataclass
from enum import Enum

@dataclass
class TokenType(Enum):
    WHITESPACE = "whitespace"
    COMMENT = "comment"
    ID = "identifier"

    NEW = "new"
    CLASS = "class"
    EXTENDS = "extends"
    STATIC = "static"
    PUBLIC = "public"
    THIS = "this"
    NULL = "null"

    WHILE = "while"
    IF = "if"
    ELSE = "else"

    PRINT = "System.out.println"

    BOOL = "boolean"
    VOID = "void"
    STRING = "String"
    LENGHT = "length"
    INT = "int"

    RETURN = "return"
    MAIN = "main"

    TRUE = "true"
    FALSE = "false"

    OPEN_BRACKET = "["
    OPEN_PARENTHESES = "("
    OPEN_BRACES = "{"

    CLOSE_BRACKET = "]"
    CLOSE_PARENTHESES = ")"
    CLOSE_BRACES = "}"

    SEMICOLON = ";"
    DOT = "."
    COMMA = ","
    
    EQUALS = "="

    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_OR_EQUALS = ">="
    LESS_OR_EQUALS = "<="
    EQUALS_EQUALS = "=="
    DIFFERENT_THAN = "!="
    AND = "&&"
    NOT = "!"

    PLUS = "+"
    MINUS = "-"
    MULTIPLY = "*"

    RESERVED ="reserved"
    NUMBER = "number"
    OP = "operator"
    PUNCTUATION = "punctuation"
    MISTAKE = "mistake"