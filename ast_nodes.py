# ast_nodes.py
# Abstract Syntax Tree Definitions for Myo

class Node:
    pass

class Program(Node):
    def __init__(self, statements):
        self.statements = statements

class ImportStmt(Node):
    def __init__(self, module_name):
        self.module_name = module_name

class ClassDef(Node):
    def __init__(self, name, methods):
        self.name = name
        self.methods = methods

class FuncDef(Node):
    def __init__(self, name, params, body):
        self.name = name
        self.params = params
        self.body = body

class IfStmt(Node):
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body

class AssignStmt(Node):
    def __init__(self, target, value):
        self.target = target
        self.value = value

class MethodCall(Node):
    def __init__(self, obj, method, args):
        self.obj = obj
        self.method = method
        self.args = args

class BinOp(Node):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

class AttributeAccess(Node):
    def __init__(self, obj, attr):
        self.obj = obj
        self.attr = attr

class Identifier(Node):
    def __init__(self, name):
        self.name = name

class Number(Node):
    def __init__(self, value):
        self.value = value

class String(Node):
    def __init__(self, value):
        self.value = value