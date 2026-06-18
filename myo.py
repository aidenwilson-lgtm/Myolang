# myo.py
import argparse
import os
import subprocess
import sys
import random
from parser_myo import parser
import ast_nodes as ast

try:
    import pygame
except ImportError:
    pygame = None

class MyoRuntimeError(Exception):
    pass

class MyoObject:
    def __init__(self, class_name):
        self.class_name = class_name
        self.fields = {}

    def get_field(self, name):
        return self.fields.get(name, 0.0)

    def set_field(self, name, value):
        self.fields[name] = value

class MyoInterpreter:
    def __init__(self):
        self.globals = {}
        self.classes = {}
        self.screen = None
        self.clock = None
        self.running = False
        self.objects = []
        
        self._setup_stdlib()

    def _setup_stdlib(self):
        self.globals['graphics'] = {
            'init': self._graphics_init,
            'clear': self._graphics_clear,
            'draw_rect': self._graphics_draw_rect,
            'draw_circle': self._graphics_draw_circle,
            'draw_score': self._graphics_draw_score,
            'present': self._graphics_present
        }
        self.globals['input'] = {
            'is_key_down': self._input_is_key_down
        }
        self.globals['math'] = {
            'rand': self._math_rand
        }

    def _graphics_init(self, args):
        if not pygame:
            print("[Interpreter Error] Pygame is required for interpreter mode.")
            sys.exit(1)
        width, height = int(args[0]), int(args[1])
        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Myo Engine Active Viewport")
        self.clock = pygame.time.Clock()
        self.running = True

    def _graphics_clear(self, args):
        if self.screen:
            r, g, b = int(args[0]), int(args[1]), int(args[2])
            self.screen.fill((r, g, b))

    def _graphics_draw_rect(self, args):
        if self.screen:
            x, y, w, h = int(args[0]), int(args[1]), int(args[2]), int(args[3])
            r, g, b = int(args[4]), int(args[5]), int(args[6])
            pygame.draw.rect(self.screen, (r, g, b), (x, y, w, h))

    def _graphics_draw_circle(self, args):
        if self.screen:
            cx, cy, rad = int(args[0]), int(args[1]), int(args[2])
            r, g, b = int(args[3]), int(args[4]), int(args[5])
            pygame.draw.circle(self.screen, (r, g, b), (cx, cy), rad)

    def _graphics_draw_score(self, args):
        if self.screen:
            score = int(args[0])
            x, y = int(args[1]), int(args[2])
            font = pygame.font.SysFont("Courier New", 32, bold=True)
            text_surf = font.render(f"MYO SCORE: {score}", True, (255, 255, 255))
            self.screen.blit(text_surf, (x, y))

    def _graphics_present(self, args):
        pass

    def _input_is_key_down(self, args):
        vk = int(args[0])
        if not pygame:
            return False
        
        # Virtual Key mapping to Pygame keys
        vk_map = {
            37: pygame.K_LEFT,
            39: pygame.K_RIGHT,
            38: pygame.K_UP,
            40: pygame.K_DOWN,
            32: pygame.K_SPACE
        }
        target = vk_map.get(vk)
        if target is None:
            return False
        return bool(pygame.key.get_pressed()[target])

    def _math_rand(self, args):
        low, high = float(args[0]), float(args[1])
        return random.uniform(low, high)

    def interpret(self, ast_node):
        self._visit(ast_node, env={})

    def _visit(self, node, env):
        if isinstance(node, ast.Program):
            for stmt in node.statements:
                if isinstance(stmt, ast.ClassDef):
                    self.classes[stmt.name] = stmt
            for stmt in node.statements:
                if not isinstance(stmt, ast.ClassDef):
                    self._visit(stmt, env)
            self._start_lifecycle_loop()

        elif isinstance(node, ast.ImportStmt):
            pass

        elif isinstance(node, ast.FuncDef):
            env[node.name] = node

        elif isinstance(node, ast.AssignStmt):
            val = self._visit(node.value, env)
            if isinstance(node.target, ast.AttributeAccess):
                obj_val = self._visit(node.target.obj, env)
                if isinstance(obj_val, MyoObject):
                    obj_val.set_field(node.target.attr, val)
                return val
            elif isinstance(node.target, ast.Identifier):
                var_name = node.target.name
                if var_name == "object":
                    raise MyoRuntimeError("Cannot reassign 'object' reference.")
                env[var_name] = val
                return val

        elif isinstance(node, ast.BinOp):
            l = self._visit(node.left, env)
            r = self._visit(node.right, env)
            if node.op == '+': return l + r
            if node.op == '-': return l - r
            if node.op == '*': return l * r
            if node.op == '/': return l / r
            if node.op == '<': return 1.0 if l < r else 0.0
            if node.op == '>': return 1.0 if l > r else 0.0
            if node.op == '<=': return 1.0 if l <= r else 0.0
            if node.op == '>=': return 1.0 if l >= r else 0.0
            if node.op == '==': return 1.0 if l == r else 0.0
            if node.op == '!=': return 1.0 if l != r else 0.0

        elif isinstance(node, ast.Number):
            return node.value

        elif isinstance(node, ast.String):
            return node.value

        elif isinstance(node, ast.Identifier):
            name = node.name
            if name == "object" and "object" in env:
                return env["object"]
            if name in env:
                return env[name]
            if name in self.globals:
                return self.globals[name]
            return 0.0

        elif isinstance(node, ast.AttributeAccess):
            obj_val = self._visit(node.obj, env)
            if isinstance(obj_val, MyoObject):
                return obj_val.get_field(node.attr)
            elif isinstance(obj_val, dict) and node.attr in obj_val:
                return obj_val[node.attr]
            return 0.0

        elif isinstance(node, ast.IfStmt):
            cond = self._visit(node.condition, env)
            if cond != 0.0:
                for stmt in node.body:
                    self._visit(stmt, env)

        elif isinstance(node, ast.MethodCall):
            method_name = node.method
            if node.obj is None and method_name in self.classes:
                return self._instantiate_class(method_name, node.args, env)

            obj_val = self._visit(node.obj, env) if node.obj else None
            args_evaluated = [self._visit(a, env) for a in node.args]

            if isinstance(obj_val, dict) and method_name in obj_val:
                return obj_val[method_name](args_evaluated)
            elif isinstance(obj_val, MyoObject):
                class_def = self.classes.get(obj_val.class_name)
                for method in class_def.methods:
                    if method.name == method_name:
                        call_env = {"object": obj_val}
                        for i, param in enumerate(method.params):
                            if i < len(args_evaluated):
                                call_env[param] = args_evaluated[i]
                        ret_val = None
                        for stmt in method.body:
                            ret_val = self._visit(stmt, call_env)
                        return ret_val
            elif method_name in env:
                func_node = env[method_name]
                call_env = {}
                for i, param in enumerate(func_node.params):
                    if i < len(args_evaluated):
                        call_env[param] = args_evaluated[i]
                for stmt in func_node.body:
                    self._visit(stmt, call_env)

        return None

    def _instantiate_class(self, class_name, args, env):
        obj = MyoObject(class_name)
        class_def = self.classes[class_name]
        args_evaluated = [self._visit(a, env) for a in args]
        for method in class_def.methods:
            if method.name == "create":
                call_env = {"object": obj}
                for i, param in enumerate(method.params):
                    if i < len(args_evaluated):
                        call_env[param] = args_evaluated[i]
                for stmt in method.body:
                    self._visit(stmt, call_env)
        return obj

    def _start_lifecycle_loop(self):
        self._graphics_init([1280, 720])
        player_instance = None
        if "Player" in self.classes:
            player_instance = self._instantiate_class("Player", [], env={})

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    break

            if not self.running:
                break

            if player_instance:
                class_def = self.classes["Player"]
                for method in class_def.methods:
                    if method.name == "update":
                        call_env = {"object": player_instance}
                        for stmt in method.body:
                            self._visit(stmt, call_env)

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()

def compile_to_ir(source_file, output_ll):
    print(f"[*] Compiling {source_file} to LLVM IR...")
    with open(source_file, "r") as f:
        source_code = f.read()

    ast_tree = parser.parse(source_code)
    if not ast_tree:
        print("[!] Compilation aborted: Syntax error.")
        sys.exit(1)

    from codegen import MyoCompiler
    compiler = MyoCompiler()
    llvm_ir = compiler.compile(ast_tree)
    with open(output_ll, "w") as f:
        f.write(llvm_ir)
    return output_ll

def link_executable(ll_file, exe_name):
    print(f"[*] Linking native executable: {exe_name}...")
    if os.name == 'nt':
        system_root = os.environ.get("SystemRoot", "C:\\Windows")
        msvcrt_path = os.path.join(system_root, "System32", "msvcrt.dll")
        user32_path = os.path.join(system_root, "System32", "user32.dll")
        gdi32_path = os.path.join(system_root, "System32", "gdi32.dll")
        
        cmd = [
            "clang", "-target", "x86_64-pc-windows-gnu",
            ll_file, "runtime.c", "-o", exe_name,
            "-nostdlib",
            "-Wl,-e,main",
            msvcrt_path,
            user32_path,
            gdi32_path
        ]
    else:
        cmd = ["clang", ll_file, "runtime.c", "-o", exe_name]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print("[!] Linker Error:")
        print(e.stderr)
        sys.exit(1)
    print(f"[+] Successfully built: {exe_name}")

def main():
    arg_parser = argparse.ArgumentParser(description="Myo CLI Engine Driver")
    subparsers = arg_parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build", help="Build executable")
    build_parser.add_argument("file", help="Source file (.myo)")
    build_parser.add_argument("--to", help="Output binary name", default="game.exe")

    run_parser = subparsers.add_parser("run", help="Run via interpreter")
    run_parser.add_argument("file", help="Source file (.myo)")

    args = arg_parser.parse_args()

    if not args.file.endswith(".myo"):
        print("[!] Target file must be a .myo file.")
        sys.exit(1)

    if args.command == "build":
        ll_output = args.file.replace(".myo", ".ll")
        compile_to_ir(args.file, ll_output)
        link_executable(ll_output, args.to)
    elif args.command == "run":
        with open(args.file, "r") as f:
            source_code = f.read()
        ast_tree = parser.parse(source_code)
        if not ast_tree:
            sys.exit(1)
        interpreter = MyoInterpreter()
        interpreter.interpret(ast_tree)

if __name__ == "__main__":
    main()