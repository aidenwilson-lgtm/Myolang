# lexer.py
import ply.lex as lex

reserved = {
    'class': 'CLASS',
    'def': 'DEF',
    'create': 'CREATE',
    'object': 'OBJECT',
    'import': 'IMPORT',
    'if': 'IF'
}

tokens = (
    'IDENTIFIER', 'NUMBER', 'STRING',
    'LBRACE', 'RBRACE', 'LPAREN', 'RPAREN', 'DOT',
    'EQUALS', 'PLUS', 'MINUS', 'STAR', 'SLASH', 'COMMA',
    'LT', 'GT', 'LE', 'GE', 'EE', 'NE'
) + tuple(reserved.values())

# Operators
t_LBRACE = r'\{'
t_RBRACE = r'\}'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_DOT    = r'\.'
t_EQUALS = r'='
t_PLUS   = r'\+'
t_MINUS  = r'-'
t_STAR   = r'\*'
t_SLASH  = r'/'
t_COMMA  = r','

# Comparison Operators (Check longer patterns first)
t_LE     = r'<='
t_GE     = r'>='
t_EE     = r'=='
t_NE     = r'!='
t_LT     = r'<'
t_GT     = r'>'

def t_IDENTIFIER(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = reserved.get(t.value, 'IDENTIFIER')
    return t

def t_NUMBER(t):
    r'\d+(\.\d+)?'
    t.value = float(t.value)
    return t

def t_STRING(t):
    r'\"([^\\\n]|(\\.))*?\"'
    t.value = t.value[1:-1]
    return t

t_ignore = ' \t\r'

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_comment(t):
    r'\#.*'
    pass

def t_error(t):
    print(f"Lexical error: Illegal character '{t.value[0]}' at line {t.lexer.lineno}")
    t.lexer.skip(1)

lexer = lex.lex()