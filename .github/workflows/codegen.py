# codegen.py
import os
from llvmlite import ir
import ast_nodes as ast

class MyoCompiler:
    def __init__(self):
        self.module = ir.Module(name="myo_engine_core")
        self.float_t = ir.FloatType()
        self.int_t = ir.IntType(32)
        self.void_t = ir.VoidType()
        
        self.vec_mode = os.environ.get("MYO_GRAPHIC_VECTOR_DEFAULT", "vec3")
        self.builder = None
        self.symbols = {}
        self._declare_external_functions()

    def _declare_external_functions(self):
        self.myo_clear = ir.Function(
            self.module, 
            ir.FunctionType(self.void_t, [self.float_t, self.float_t, self.float_t]), 
            name="myo_clear"
        )
        self.myo_draw_rect = ir.Function(
            self.module, 
            ir.FunctionType(self.void_t, [self.float_t, self.float_t, self.float_t, self.float_t, self.float_t, self.float_t, self.float_t]), 
            name="myo_draw_rect"
        )
        self.myo_draw_circle = ir.Function(
            self.module, 
            ir.FunctionType(self.void_t, [self.float_t, self.float_t, self.float_t, self.float_t, self.float_t, self.float_t]), 
            name="myo_draw_circle"
        )
        self.myo_draw_score = ir.Function(
            self.module, 
            ir.FunctionType(self.void_t, [self.float_t, self.float_t, self.float_t]), 
            name="myo_draw_score"
        )
        self.myo_is_key_down = ir.Function(
            self.module, 
            ir.FunctionType(self.float_t, [self.float_t]), 
            name="myo_is_key_down"
        )
        self.myo_rand = ir.Function(
            self.module, 
            ir.FunctionType(self.float_t, [self.float_t, self.float_t]), 
            name="myo_rand"
        )

    def _resolve_name(self, node):
        if isinstance(node, ast.Identifier):
            return node.name
        elif isinstance(node, ast.AttributeAccess):
            obj_name = self._resolve_name(node.obj)
            return f"{obj_name}_{node.attr}"
        return "unknown"

    def compile(self, node):
        for hook in ["main_game_init", "main_game_loop"]:
            if hook not in self.module.globals:
                fnty = ir.FunctionType(self.void_t, [])
                func = ir.Function(self.module, fnty, name=hook)
                block = func.append_basic_block(name="entry")
                builder = ir.IRBuilder(block)
                builder.ret_void()

        self._visit(node)
        return str(self.module)

    def _visit(self, node):
        if isinstance(node, ast.Program):
            for stmt in node.statements:
                self._visit(stmt)
                
        elif isinstance(node, ast.ClassDef):
            for method in node.methods:
                self._visit(method)
                
        elif isinstance(node, ast.FuncDef):
            if node.name == "create":
                func_name = "main_game_init"
            elif node.name == "update":
                func_name = "main_game_loop"
            else:
                func_name = node.name
            
            func_type = ir.FunctionType(self.void_t, [])
            if func_name in self.module.globals:
                func = self.module.globals[func_name]
                func.blocks.clear()
            else:
                func = ir.Function(self.module, func_type, name=func_name)
                
            block = func.append_basic_block(name="entry")
            self.builder = ir.IRBuilder(block)
            self.symbols = {}
            
            if hasattr(node, 'params') and node.params:
                for i, param_name in enumerate(node.params):
                    ptr = self.builder.alloca(self.float_t, name=param_name)
                    if func_name == "main_game_loop":
                        default_val = 100.0 if param_name in ('x', 'y') else 0.0
                        self.builder.store(ir.Constant(self.float_t, default_val), ptr)
                    else:
                        param_val = func.args[i]
                        param_val.name = param_name
                        self.builder.store(param_val, ptr)
                    self.symbols[param_name] = ptr
            
            for stmt in node.body:
                self._visit(stmt)
                
            self.builder.ret_void()

        elif isinstance(node, ast.AssignStmt):
            value = self._visit(node.value)
            if value is None:
                value = ir.Constant(self.float_t, 0.0)
            
            if isinstance(node.target, ast.AttributeAccess) and isinstance(node.target.obj, ast.Identifier) and node.target.obj.name == "object":
                var_name = f"object_{node.target.attr}"
                if var_name not in self.module.globals:
                    g_var = ir.GlobalVariable(self.module, self.float_t, name=var_name)
                    g_var.initializer = ir.Constant(self.float_t, 0.0)
                    g_var.linkage = 'internal'
                else:
                    g_var = self.module.globals[var_name]
                self.builder.store(value, g_var)
                return value

            target_name = self._resolve_name(node.target)
            if target_name not in self.symbols:
                ptr = self.builder.alloca(self.float_t, name=target_name)
                self.symbols[target_name] = ptr
            
            self.builder.store(value, self.symbols[target_name])
            return value

        elif isinstance(node, ast.BinOp):
            left = self._visit(node.left)
            right = self._visit(node.right)
            if left is None: left = ir.Constant(self.float_t, 0.0)
            if right is None: right = ir.Constant(self.float_t, 0.0)
            
            if node.op == '+': return self.builder.fadd(left, right)
            if node.op == '-': return self.builder.fsub(left, right)
            if node.op == '*': return self.builder.fmul(left, right)
            if node.op == '/': return self.builder.fdiv(left, right)
            
            # Map math operations or native comparisons directly to float casts
            if node.op in ('<', '>', '<=', '>=', '==', '!='):
                cmp_res = self.builder.fcmp_ordered(node.op, left, right)
                return self.builder.uitofp(cmp_res, self.float_t)

        elif isinstance(node, ast.IfStmt):
            cond_val = self._visit(node.condition)
            if cond_val is None:
                cond_val = ir.Constant(self.float_t, 0.0)
            
            cmp_cond = self.builder.fcmp_ordered('!=', cond_val, ir.Constant(self.float_t, 0.0))
            then_block = self.builder.append_basic_block('then')
            merge_block = self.builder.append_basic_block('merge')
            
            self.builder.cbranch(cmp_cond, then_block, merge_block)
            
            self.builder.position_at_end(then_block)
            for stmt in node.body:
                self._visit(stmt)
            self.builder.branch(merge_block)
            
            self.builder.position_at_end(merge_block)

        elif isinstance(node, ast.Number):
            return ir.Constant(self.float_t, float(node.value))

        elif isinstance(node, ast.String):
            return ir.Constant(self.float_t, 0.0)

        elif isinstance(node, ast.AttributeAccess):
            if isinstance(node.obj, ast.Identifier) and node.obj.name == "object":
                var_name = f"object_{node.attr}"
                if var_name not in self.module.globals:
                    g_var = ir.GlobalVariable(self.module, self.float_t, name=var_name)
                    g_var.initializer = ir.Constant(self.float_t, 0.0)
                    g_var.linkage = 'internal'
                else:
                    g_var = self.module.globals[var_name]
                return self.builder.load(g_var)
            
            var_name = self._resolve_name(node)
            if var_name in self.symbols:
                return self.builder.load(self.symbols[var_name])
            return ir.Constant(self.float_t, 0.0)

        elif isinstance(node, ast.Identifier):
            var_name = node.name
            if var_name in self.symbols:
                return self.builder.load(self.symbols[var_name])
            return ir.Constant(self.float_t, 0.0)

        elif isinstance(node, ast.MethodCall):
            if node.method == "clear":
                r = self._visit(node.args[0]) if len(node.args) > 0 else ir.Constant(self.float_t, 0.0)
                g = self._visit(node.args[1]) if len(node.args) > 1 else ir.Constant(self.float_t, 0.0)
                b = self._visit(node.args[2]) if len(node.args) > 2 else ir.Constant(self.float_t, 0.0)
                return self.builder.call(self.myo_clear, [r, g, b])
                
            elif node.method == "draw_rect":
                x = self._visit(node.args[0])
                y = self._visit(node.args[1])
                w = self._visit(node.args[2])
                h = self._visit(node.args[3])
                r = self._visit(node.args[4])
                g = self._visit(node.args[5])
                b = self._visit(node.args[6])
                return self.builder.call(self.myo_draw_rect, [x, y, w, h, r, g, b])
                
            elif node.method == "draw_circle":
                cx = self._visit(node.args[0])
                cy = self._visit(node.args[1])
                rad = self._visit(node.args[2])
                r = self._visit(node.args[3])
                g = self._visit(node.args[4])
                b = self._visit(node.args[5])
                return self.builder.call(self.myo_draw_circle, [cx, cy, rad, r, g, b])
                
            elif node.method == "draw_score":
                score = self._visit(node.args[0])
                x = self._visit(node.args[1])
                y = self._visit(node.args[2])
                return self.builder.call(self.myo_draw_score, [score, x, y])
                
            elif node.method == "is_key_down":
                vk_code = self._visit(node.args[0])
                return self.builder.call(self.myo_is_key_down, [vk_code])
                
            elif node.method == "rand":
                low = self._visit(node.args[0])
                high = self._visit(node.args[1])
                return self.builder.call(self.myo_rand, [low, high])

        return None
