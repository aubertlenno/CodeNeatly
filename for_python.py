import tkinter as tk
from tkinter import messagebox
import ast
import networkx as nx
from graphviz import Digraph
from PIL import Image, ImageTk


# Formatter class
class CodeFormatter:
    def __init__(self):
        self.indent_size = 4
        self.formatted_code = ''
        self.current_indent = 0
    def format_code(self, code):
        try:
            # 1) Parse code into AST (this catches SyntaxError)
            tree = ast.parse(code)
            
            # 2) If parsing is successful, you can optionally run the code here:
            compiled_code = compile(tree, filename="<user-input>", mode="exec")
            exec(compiled_code, {})
            
            # If the code runs successfully, format it
            self.formatted_code = ''
            self.current_indent = 0
            self.visit(tree)
            return self.formatted_code

        except SyntaxError as e:
            messagebox.showerror("Syntax Error", f"{e}")
            return code
        except Exception as e:
            # This will catch NameError, TypeError, etc. during runtime
            messagebox.showerror("Runtime Error", str(e))
            return code


    def visit(self, node):
        if node is None:
            return
        method_name = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method_name, self.generic_visit)
        visitor(node)

    def generic_visit(self, node):
        # Visit all child nodes
        for child in ast.iter_child_nodes(node):
            self.visit(child)

    def visit_Module(self, node):
        for stmt in node.body:
            self.visit(stmt)

    def visit_ClassDef(self, node):
        # Handle decorators
        for decorator in node.decorator_list:
            self.write_indent()
            decorator_str = self.get_node_name(decorator)
            self.formatted_code += f"@{decorator_str}\n"
        
        # Write class definition
        self.write_indent()
        bases = [self.get_node_name(base) for base in node.bases]
        bases_str = f"({', '.join(bases)})" if bases else ""
        self.formatted_code += f"class {node.name}{bases_str}:\n"
        self.current_indent += 1

        if not node.body:
            self.write_indent()
            self.formatted_code += "pass\n"
        else:
            for stmt in node.body:
                self.visit(stmt)
        
        self.current_indent -= 1
        self.formatted_code += '\n'

    def visit_FunctionDef(self, node):
        # Handle decorators
        for decorator in node.decorator_list:
            self.write_indent()
            decorator_str = self.get_node_name(decorator)
            self.formatted_code += f"@{decorator_str}\n"

        self.write_indent()
        args = [arg.arg for arg in node.args.args]
        args_str = ', '.join(args)
        self.formatted_code += f"def {node.name}({args_str}):\n"
        self.current_indent += 1
        if not node.body:
            self.write_indent()
            self.formatted_code += "pass\n"
        else:
            for stmt in node.body:
                self.visit(stmt)
        self.current_indent -= 1
        self.formatted_code += '\n'

    def visit_AsyncFunctionDef(self, node):
        # Handle decorators
        for decorator in node.decorator_list:
            self.write_indent()
            decorator_str = self.get_node_name(decorator)
            self.formatted_code += f"@{decorator_str}\n"

        self.write_indent()
        args = [arg.arg for arg in node.args.args]
        args_str = ', '.join(args)
        self.formatted_code += f"async def {node.name}({args_str}):\n"
        self.current_indent += 1
        if not node.body:
            self.write_indent()
            self.formatted_code += "pass\n"
        else:
            for stmt in node.body:
                self.visit(stmt)
        self.current_indent -= 1
        self.formatted_code += '\n'

    def visit_Return(self, node):
        self.write_indent()
        self.formatted_code += "return"
        if node.value is not None:
            self.formatted_code += f" {self.get_node_name(node.value)}"
        self.formatted_code += '\n'

    def visit_Raise(self, node):
        self.write_indent()
        self.formatted_code += "raise"
        if node.exc is not None:
            self.formatted_code += f" {self.get_node_name(node.exc)}"
        if node.cause is not None:
            self.formatted_code += f" from {self.get_node_name(node.cause)}"
        self.formatted_code += '\n'

    def visit_Expr(self, node):
        self.write_indent()
        expr_str = self.get_node_name(node.value)
        self.formatted_code += f"{expr_str}\n"

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
        iter_ = self.get_node_name(node.iter)
        self.formatted_code += f"for {target} in {iter_}:\n"
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

    def visit_While(self, node):
        self.write_indent()
        test = self.get_node_name(node.test)
        self.formatted_code += f"while {test}:\n"
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

    def visit_AugAssign(self, node):
        self.write_indent()
        target = self.get_node_name(node.target)
        op = self.get_operator(node.op)
        value = self.get_node_name(node.value)
        self.formatted_code += f"{target} {op}= {value}\n"

    def visit_Import(self, node):
        self.write_indent()
        names = [alias.name if alias.asname is None else f"{alias.name} as {alias.asname}" for alias in node.names]
        self.formatted_code += f"import {', '.join(names)}\n"

    def visit_ImportFrom(self, node):
        self.write_indent()
        module = node.module if node.module else ""
        names = [alias.name if alias.asname is None else f"{alias.name} as {alias.asname}" for alias in node.names]
        self.formatted_code += f"from {module} import {', '.join(names)}\n"

    def visit_Pass(self, node):
        self.write_indent()
        self.formatted_code += "pass\n"

    def visit_Break(self, node):
        self.write_indent()
        self.formatted_code += "break\n"

    def visit_Continue(self, node):
        self.write_indent()
        self.formatted_code += "continue\n"

    def visit_Try(self, node):
        self.write_indent()
        self.formatted_code += "try:\n"
        self.current_indent += 1
        for stmt in node.body:
            self.visit(stmt)
        self.current_indent -= 1
        for handler in node.handlers:
            self.write_indent()
            if handler.type:
                type_str = self.get_node_name(handler.type)
                if handler.name:
                    name_str = f" as {handler.name}"
                else:
                    name_str = ""
                self.formatted_code += f"except {type_str}{name_str}:\n"
            else:
                self.formatted_code += "except:\n"
            self.current_indent += 1
            for stmt in handler.body:
                self.visit(stmt)
            self.current_indent -= 1
        if node.orelse:
            self.write_indent()
            self.formatted_code += "else:\n"
            self.current_indent += 1
            for stmt in node.orelse:
                self.visit(stmt)
            self.current_indent -= 1
        if node.finalbody:
            self.write_indent()
            self.formatted_code += "finally:\n"
            self.current_indent += 1
            for stmt in node.finalbody:
                self.visit(stmt)
            self.current_indent -= 1

    def visit_With(self, node):
        self.write_indent()
        items = [self.get_node_name(item.context_expr) for item in node.items]
        items_str = ', '.join(items)
        self.formatted_code += f"with {items_str}:\n"
        self.current_indent += 1
        for stmt in node.body:
            self.visit(stmt)
        self.current_indent -= 1

    def write_indent(self):
        self.formatted_code += ' ' * (self.current_indent * self.indent_size)

    def get_node_name(self, node):
        if node is None:
            return ''
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Call):
            func_name = self.get_node_name(node.func)
            args = [self.get_node_name(arg) for arg in node.args]
            args_str = ', '.join(args)
            return f"{func_name}({args_str})"
        elif isinstance(node, ast.Constant):
            return repr(node.value)
        elif isinstance(node, ast.Str):  # For Python <3.8
            return repr(node.s)
        elif isinstance(node, ast.Num):  # For Python <3.8
            return repr(node.n)
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
            slice_ = self.get_node_name(node.slice)
            return f"{value}[{slice_}]"
        elif isinstance(node, ast.Index):  # For Python <3.9
            return self.get_node_name(node.value)
        elif isinstance(node, ast.Slice):
            lower = self.get_node_name(node.lower)
            upper = self.get_node_name(node.upper)
            step = self.get_node_name(node.step)
            slice_parts = ':'.join(filter(None, [lower, upper, step]))
            return slice_parts
        elif isinstance(node, ast.ListComp):
            elt = self.get_node_name(node.elt)
            generators = ' '.join([self.get_node_name(gen) for gen in node.generators])
            return f"[{elt} {generators}]"
        elif isinstance(node, ast.GeneratorExp):
            elt = self.get_node_name(node.elt)
            generators = ' '.join([self.get_node_name(gen) for gen in node.generators])
            return f"({elt} {generators})"
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
        elif isinstance(node, ast.comprehension):
            target = self.get_node_name(node.target)
            iter_ = self.get_node_name(node.iter)
            ifs = ' '.join([f"if {self.get_node_name(if_)}" for if_ in node.ifs])
            return f"for {target} in {iter_} {ifs}"
        elif isinstance(node, ast.Lambda):
            args = [arg.arg for arg in node.args.args]
            body = self.get_node_name(node.body)
            return f"lambda {', '.join(args)}: {body}"
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
        else:
            return ''

    def get_operator(self, op):
        operators = {
            ast.Add: '+',
            ast.Sub: '-',
            ast.Mult: '*',
            ast.MatMult: '@',
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
            ast.Invert: '~',
            ast.Not: 'not ',
            ast.UAdd: '+',
            ast.USub: '-',
            ast.Eq: '==',
            ast.NotEq: '!=',
            ast.Lt: '<',
            ast.LtE: '<=',
            ast.Gt: '>',
            ast.GtE: '>=',
            ast.Is: 'is',
            ast.IsNot: 'is not',
            ast.In: 'in',
            ast.NotIn: 'not in',
        }
        return operators.get(type(op), '')
    
    def visualize_ast(self, code):
        try:
            tree = ast.parse(code)
            graph = Digraph(format="png")
            self._add_nodes(graph, tree, "root")
            return graph
        except SyntaxError as e:
            messagebox.showerror("Syntax Error", f"{e}")
            return None

    def _add_nodes(self, graph, node, parent_name):
        node_id = str(id(node))
        label = type(node).__name__
        graph.node(node_id, label)

        if parent_name != "root":
            graph.edge(parent_name, node_id)

        for child in ast.iter_child_nodes(node):
            self._add_nodes(graph, child, node_id)

# GUI Application

class FormatterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Python Code Formatter")

        # Input Text Widget
        self.input_label = tk.Label(root, text="Unformatted Code:")
        self.input_label.pack()
        self.input_text = tk.Text(root, height=10, width=80)
        self.input_text.pack()

        # Buttons
        self.format_button = tk.Button(root, text="Format Code", command=self.format_code)
        self.format_button.pack()

        self.visualize_button = tk.Button(root, text="Visualize LL Parsing", command=self.visualize_code)
        self.visualize_button.pack()

        # Output Text Widget
        self.output_label = tk.Label(root, text="Formatted Code:")
        self.output_label.pack()
        self.output_text = tk.Text(root, height=10, width=80)
        self.output_text.pack()

        # Visualization Canvas
        self.canvas = tk.Canvas(root, width=600, height=400)
        self.canvas.pack()

    def format_code(self):
        code = self.input_text.get("1.0", tk.END)
        formatter = CodeFormatter()
        formatted_code = formatter.format_code(code)
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, formatted_code)

    def visualize_code(self):
        code = self.input_text.get("1.0", tk.END)
        formatter = CodeFormatter()
        graph = formatter.visualize_ast(code)
        if graph:
            graph.render('ast_tree', format='png', cleanup=False)
            img = Image.open('ast_tree.png')
            img = img.resize((600, 400))
            img = ImageTk.PhotoImage(img)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=img)
            self.canvas.image = img


# Main Execution
if __name__ == "__main__":
    root = tk.Tk()
    app = FormatterGUI(root)
    root.mainloop()