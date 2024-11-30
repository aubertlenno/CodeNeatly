import tkinter as tk
from tkinter import messagebox
import ast
import textwrap
import tokenize
import io
import keyword

# Formatter class
class CodeFormatter:
    def __init__(self):
        self.indent_size = 4
        self.formatted_code = ''
        self.current_indent = 0

    def format_code(self, code):
        try:
            # Parse code into AST
            tree = ast.parse(code)
            self.formatted_code = ''
            self.current_indent = 0
            self.visit(tree)
            return self.formatted_code
        except SyntaxError as e:
            messagebox.showerror("Syntax Error", f"{e}")
            return code

    def visit(self, node):
        method_name = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method_name, self.generic_visit)
        visitor(node)

    def generic_visit(self, node):
        # Visit all child nodes
        if isinstance(node, ast.Module):
            for stmt in node.body:
                self.visit(stmt)
        else:
            for field, value in ast.iter_fields(node):
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, ast.AST):
                            self.visit(item)
                elif isinstance(value, ast.AST):
                    self.visit(value)

    def visit_Module(self, node):
        for stmt in node.body:
            self.visit(stmt)

    def visit_FunctionDef(self, node):
        self.write_indent()
        args = [arg.arg for arg in node.args.args]
        args_str = ', '.join(args)
        self.formatted_code += f"def {node.name}({args_str}):\n"
        self.current_indent += 1
        for stmt in node.body:
            self.visit(stmt)
        self.current_indent -= 1
        self.formatted_code += '\n'

    def visit_Return(self, node):
        self.write_indent()
        self.formatted_code += "return "
        self.visit(node.value)
        self.formatted_code += '\n'

    def visit_Expr(self, node):
        self.write_indent()
        self.visit(node.value)
        self.formatted_code += '\n'

    def visit_Call(self, node):
        func_name = self.get_node_name(node.func)
        args = [self.get_node_name(arg) for arg in node.args]
        args_str = ', '.join(args)
        self.formatted_code += f"{func_name}({args_str})"

    def visit_Assign(self, node):
        self.write_indent()
        targets = [self.get_node_name(t) for t in node.targets]
        value = self.get_node_name(node.value)
        self.formatted_code += f"{' = '.join(targets)} = {value}\n"

    def visit_If(self, node):
        self.write_indent()
        test = self.get_node_name(node.test)
        self.formatted_code += f"if {test}:\n"
        self.current_indent += 1
        for stmt in node.body:
            self.visit(stmt)
        self.current_indent -= 1
        if node.orelse:
            self.write_indent()
            self.formatted_code += f"else:\n"
            self.current_indent += 1
            for stmt in node.orelse:
                self.visit(stmt)
            self.current_indent -= 1

    def visit_For(self, node):
        self.write_indent()
        target = self.get_node_name(node.target)
        iter = self.get_node_name(node.iter)
        self.formatted_code += f"for {target} in {iter}:\n"
        self.current_indent += 1
        for stmt in node.body:
            self.visit(stmt)
        self.current_indent -= 1

    def visit_While(self, node):
        self.write_indent()
        test = self.get_node_name(node.test)
        self.formatted_code += f"while {test}:\n"
        self.current_indent += 1
        for stmt in node.body:
            self.visit(stmt)
        self.current_indent -= 1

    def visit_AugAssign(self, node):
        self.write_indent()
        target = self.get_node_name(node.target)
        op = self.get_operator(node.op)
        value = self.get_node_name(node.value)
        self.formatted_code += f"{target} {op}= {value}\n"

    def visit_Import(self, node):
        self.write_indent()
        names = [alias.name for alias in node.names]
        self.formatted_code += f"import {', '.join(names)}\n"

    def visit_ImportFrom(self, node):
        self.write_indent()
        module = node.module
        names = [alias.name for alias in node.names]
        self.formatted_code += f"from {module} import {', '.join(names)}\n"

    def visit_Pass(self, node):
        self.write_indent()
        self.formatted_code += f"pass\n"

    def write_indent(self):
        self.formatted_code += ' ' * (self.current_indent * self.indent_size)

    def get_node_name(self, node):
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Call):
            func_name = self.get_node_name(node.func)
            args = [self.get_node_name(arg) for arg in node.args]
            args_str = ', '.join(args)
            return f"{func_name}({args_str})"
        elif isinstance(node, ast.Constant):
            return repr(node.value)
        elif isinstance(node, ast.BinOp):
            left = self.get_node_name(node.left)
            op = self.get_operator(node.op)
            right = self.get_node_name(node.right)
            return f"({left} {op} {right})"
        elif isinstance(node, ast.Attribute):
            value = self.get_node_name(node.value)
            return f"{value}.{node.attr}"
        elif isinstance(node, ast.Subscript):
            value = self.get_node_name(node.value)
            slice = self.get_node_name(node.slice)
            return f"{value}[{slice}]"
        elif isinstance(node, ast.Index):
            return self.get_node_name(node.value)
        elif isinstance(node, ast.Str):
            return repr(node.s)
        elif isinstance(node, ast.Num):
            return repr(node.n)
        elif isinstance(node, ast.Compare):
            left = self.get_node_name(node.left)
            ops = [self.get_operator(op) for op in node.ops]
            comparators = [self.get_node_name(comp) for comp in node.comparators]
            comparisons = ' '.join(f"{op} {comp}" for op, comp in zip(ops, comparators))
            return f"{left} {comparisons}"
        elif isinstance(node, ast.BoolOp):
            op = self.get_operator(node.op)
            values = [self.get_node_name(v) for v in node.values]
            return f" {op} ".join(values)
        elif isinstance(node, ast.UnaryOp):
            op = self.get_operator(node.op)
            operand = self.get_node_name(node.operand)
            return f"{op}{operand}"
        elif isinstance(node, ast.Lambda):
            args = [arg.arg for arg in node.args.args]
            body = self.get_node_name(node.body)
            return f"lambda {', '.join(args)}: {body}"
        elif isinstance(node, ast.Dict):
            keys = [self.get_node_name(k) for k in node.keys]
            values = [self.get_node_name(v) for v in node.values]
            items = ', '.join(f"{k}: {v}" for k, v in zip(keys, values))
            return f"{{{items}}}"
        elif isinstance(node, ast.List):
            elements = [self.get_node_name(e) for e in node.elts]
            return f"[{', '.join(elements)}]"
        elif isinstance(node, ast.Tuple):
            elements = [self.get_node_name(e) for e in node.elts]
            return f"({', '.join(elements)})"
        else:
            return ''

    def get_operator(self, op):
        operators = {
            ast.Add: '+',
            ast.Sub: '-',
            ast.Mult: '*',
            ast.Div: '/',
            ast.Mod: '%',
            ast.Pow: '**',
            ast.LShift: '<<',
            ast.RShift: '>>',
            ast.BitOr: '|',
            ast.BitXor: '^',
            ast.BitAnd: '&',
            ast.FloorDiv: '//',
            ast.And: 'and',
            ast.Or: 'or',
            ast.Eq: '==',
            ast.NotEq: '!=',
            ast.Lt: '<',
            ast.LtE: '<=',
            ast.Gt: '>',
            ast.GtE: '>=',
            ast.Not: 'not',
            ast.UAdd: '+',
            ast.USub: '-',
        }
        return operators.get(type(op), '')

# GUI Application
class FormatterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Python Code Formatter")

        # Input Text Widget
        self.input_label = tk.Label(root, text="Unformatted Code:")
        self.input_label.pack()
        self.input_text = tk.Text(root, height=15, width=80)
        self.input_text.pack()

        # Format Button
        self.format_button = tk.Button(root, text="Format Code", command=self.format_code)
        self.format_button.pack()

        # Output Text Widget
        self.output_label = tk.Label(root, text="Formatted Code:")
        self.output_label.pack()
        self.output_text = tk.Text(root, height=15, width=80)
        self.output_text.pack()

    def format_code(self):
        code = self.input_text.get("1.0", tk.END)
        formatter = CodeFormatter()
        formatted_code = formatter.format_code(code)
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, formatted_code)

# Main Execution
if __name__ == "__main__":
    root = tk.Tk()
    app = FormatterGUI(root)
    root.mainloop()
