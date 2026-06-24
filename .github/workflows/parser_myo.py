# parser_myo.py
import ply.yacc as yacc
from lexer import tokens
import ast_nodes as ast

# Precedence rules defining correct operator order
precedence = (
    ('left', 'EE', 'NE', 'LT', 'GT', 'LE', 'GE'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'STAR', 'SLASH'),
    ('left', 'DOT'),
    ('left', 'LPAREN'),
)

def p_program(p):
    '''program : statements'''
    p[0] = ast.Program(p[1])

def p_statements_list(p):
    '''statements : statements statement
                  | statement'''
    if len(p) == 3:
        p[0] = p[1] + [p[2]]
    else:
        p[0] = [p[1]]

def p_statement(p):
    '''statement : import_stmt
                 | class_def
                 | func_def
                 | if_stmt
                 | assign_stmt
                 | expr_stmt'''
    p[0] = p[1]

def p_import_stmt(p):
    '''import_stmt : IMPORT IDENTIFIER'''
    p[0] = ast.ImportStmt(p[2])

def p_class_def(p):
    '''class_def : CLASS IDENTIFIER LBRACE statements RBRACE'''
    p[0] = ast.ClassDef(p[2], p[4])

def p_func_def(p):
    '''func_def : DEF IDENTIFIER LPAREN param_list RPAREN LBRACE statements RBRACE
                | DEF CREATE LPAREN param_list RPAREN LBRACE statements RBRACE'''
    p[0] = ast.FuncDef(p[2], p[4], p[7])

def p_param_list(p):
    '''param_list : param_list COMMA IDENTIFIER
                  | IDENTIFIER
                  | empty'''
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    elif p[1] is None:
        p[0] = []
    else:
        p[0] = [p[1]]

def p_if_stmt(p):
    '''if_stmt : IF expression LBRACE statements RBRACE'''
    p[0] = ast.IfStmt(p[2], p[4])

def p_assign_stmt(p):
    '''assign_stmt : expression EQUALS expression'''
    p[0] = ast.AssignStmt(p[1], p[3])

def p_expr_stmt(p):
    '''expr_stmt : expression'''
    p[0] = p[1]

def p_expression_binop(p):
    '''expression : expression PLUS expression
                  | expression MINUS expression
                  | expression STAR expression
                  | expression SLASH expression
                  | expression LT expression
                  | expression GT expression
                  | expression LE expression
                  | expression GE expression
                  | expression EE expression
                  | expression NE expression'''
    p[0] = ast.BinOp(p[1], p[2], p[3])

def p_expression_call(p):
    '''expression : expression LPAREN arg_list RPAREN'''
    if isinstance(p[1], ast.AttributeAccess):
        p[0] = ast.MethodCall(p[1].obj, p[1].attr, p[3])
    else:
        p[0] = ast.MethodCall(None, p[1], p[3])

def p_expression_attr_access(p):
    '''expression : expression DOT IDENTIFIER'''
    p[0] = ast.AttributeAccess(p[1], p[3])

def p_expression_terminal(p):
    '''expression : IDENTIFIER
                  | NUMBER
                  | STRING
                  | OBJECT'''
    token_type = p.slice[1].type
    if token_type == 'NUMBER':
        p[0] = ast.Number(p[1])
    elif token_type == 'STRING':
        p[0] = ast.String(p[1])
    elif token_type == 'OBJECT':
        p[0] = ast.Identifier('object')
    else:
        p[0] = ast.Identifier(p[1])

def p_arg_list(p):
    '''arg_list : arg_list COMMA expression
                | expression
                | empty'''
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    elif p[1] is None:
        p[0] = []
    else:
        p[0] = [p[1]]

def p_expression_group(p):
    '''expression : LPAREN expression RPAREN'''
    p[0] = p[2]

def p_empty(p):
    '''empty :'''
    pass

def p_error(p):
    if p:
        print(f"Syntax error at '{p.value}', line {p.lineno}")
    else:
        print("Syntax error at EOF")

parser = yacc.yacc()
