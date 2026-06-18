import os
import tkinter as tk
from tkinter import ttk, messagebox

# WARNING: Tkinter is strictly for the compiler toolchain configuration.
# The Myo Engine strictly relies on WebGPU/Hardware APIs for game presentation.

ENV_FILE = ".myoenv"

class MyoConfigTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Myo Systemic Configuration Tool")
        self.root.geometry("400x250")
        self.root.resizable(False, False)

        # Variables
        self.vec_var = tk.StringVar(value="vec3")
        self.os_var = tk.StringVar(value="windows")
        self.arch_var = tk.StringVar(value="x86_64")

        self._load_existing()
        self._build_ui()

    def _load_existing(self):
        if os.path.exists(ENV_FILE):
            with open(ENV_FILE, "r") as f:
                for line in f:
                    if "=" in line:
                        k, v = line.strip().split("=")
                        if k == "MYO_GRAPHIC_VECTOR_DEFAULT": self.vec_var.set(v)
                        elif k == "MYO_TARGET_OS": self.os_var.set(v)
                        elif k == "MYO_TARGET_ARCH": self.arch_var.set(v)

    def _build_ui(self):
        ttk.Label(self.root, text="Myo Architecture Configurator", font=("Arial", 14, "bold")).pack(pady=10)

        frame = ttk.Frame(self.root)
        frame.pack(pady=5, padx=20, fill="x")

        ttk.Label(frame, text="Graphic Vector Default:").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Combobox(frame, textvariable=self.vec_var, values=["vec2", "vec3"], state="readonly").grid(row=0, column=1, sticky="ew")

        ttk.Label(frame, text="Target OS:").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Combobox(frame, textvariable=self.os_var, values=["windows", "linux", "macos"], state="readonly").grid(row=1, column=1, sticky="ew")

        ttk.Label(frame, text="Target Architecture:").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Combobox(frame, textvariable=self.arch_var, values=["x86_64", "aarch64"], state="readonly").grid(row=2, column=1, sticky="ew")

        frame.columnconfigure(1, weight=1)

        ttk.Button(self.root, text="Save Configuration", command=self.save_config).pack(pady=20)

    def save_config(self):
        with open(ENV_FILE, "w") as f:
            f.write(f"MYO_GRAPHIC_VECTOR_DEFAULT={self.vec_var.get()}\n")
            f.write(f"MYO_TARGET_OS={self.os_var.get()}\n")
            f.write(f"MYO_TARGET_ARCH={self.arch_var.get()}\n")
        messagebox.showinfo("Success", "Compiler Environment Variables Saved to .myoenv")

if __name__ == "__main__":
    root = tk.Tk()
    app = MyoConfigTool(root)
    root.mainloop()