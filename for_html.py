import tkinter as tk
from html.parser import HTMLParser
from tkinter import messagebox
from graphviz import Digraph
from PIL import Image, ImageTk

# Define HTML5 void elements
VOID_ELEMENTS = {"area", "base", "br", "col", "embed", "hr", "img", "input",
                 "link", "meta", "param", "source", "track", "wbr"}

class Node:
    def __init__(self, tag=None, attrs=None, data=None, is_comment=False, is_doctype=False):
        self.tag = tag
        self.attrs = attrs if attrs is not None else {}
        self.data = data
        self.children = []
        self.is_comment = is_comment
        self.is_doctype = is_doctype

    def add_child(self, node):
        self.children.append(node)

class HTMLTreeBuilder(HTMLParser):
    def __init__(self):
        super().__init__()
        self.root = Node(tag="__ROOT__")
        self.stack = [self.root]
        self.errors = []

    def handle_decl(self, decl):
        node = Node(is_doctype=True, data=decl.upper())
        self.stack[-1].add_child(node)

    def handle_starttag(self, tag, attrs):
        if tag.lower() in VOID_ELEMENTS:
            node = Node(tag=tag, attrs=dict(attrs))
            self.stack[-1].add_child(node)
        else:
            node = Node(tag=tag, attrs=dict(attrs))
            self.stack[-1].add_child(node)
            self.stack.append(node)

    def handle_endtag(self, tag):
        if tag.lower() not in VOID_ELEMENTS and len(self.stack) > 1:
            if self.stack[-1].tag == tag:
                self.stack.pop()

    def handle_data(self, data):
        stripped = data.strip()
        if stripped:
            node = Node(data=stripped)
            self.stack[-1].add_child(node)

    def handle_comment(self, data):
        node = Node(data=data.strip(), is_comment=True)
        self.stack[-1].add_child(node)

    def get_tree(self):
        return self.root

class HTMLFormatter:
    def __init__(self, indent_size=4):
        self.indent_size = indent_size

    def format_html(self, code):
        parser = HTMLTreeBuilder()
        parser.feed(code)
        parser.close()
        tree = parser.get_tree()
        return self.format_node(tree, 0)

    def format_node(self, node, depth):
        if node.tag == "__ROOT__":
            result = ""
            for child in node.children:
                result += self.format_node(child, depth)
            return result

        indent = " " * (depth * self.indent_size)
        if node.is_doctype:
            return f"<!{node.data}>\n"
        if node.is_comment:
            return indent + f"<!-- {node.data} -->\n"
        if node.tag is None and node.data:
            return indent + node.data + "\n"

        attrs_str = " ".join(f'{k}="{v}"' for k, v in node.attrs.items())
        start_tag = f"<{node.tag} {attrs_str}".strip() + ">"
        if node.tag.lower() in VOID_ELEMENTS:
            return indent + start_tag + "\n"

        result = indent + start_tag + "\n"
        for child in node.children:
            result += self.format_node(child, depth + 1)
        result += indent + f"</{node.tag}>\n"
        return result

    def visualize_html_tree(self, tree):
        graph = Digraph(format="png")
        self.add_nodes(graph, tree, "root")
        return graph

    def add_nodes(self, graph, node, parent_name):
        node_id = str(id(node))
        label = node.tag if node.tag else (node.data if node.data else "Text")
        graph.node(node_id, label)
        if parent_name != "root":
            graph.edge(parent_name, node_id)
        for child in node.children:
            self.add_nodes(graph, child, node_id)

class FormatterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("HTML Formatter with Visualization")

        self.input_label = tk.Label(root, text="Unformatted HTML:")
        self.input_label.pack()

        self.input_text = tk.Text(root, height=10, width=80)
        self.input_text.pack()

        self.format_button = tk.Button(root, text="Format Code", command=self.format_code)
        self.format_button.pack()

        self.visualize_button = tk.Button(root, text="Visualize LL Parsing", command=self.visualize_html)
        self.visualize_button.pack()

        self.output_label = tk.Label(root, text="Formatted HTML:")
        self.output_label.pack()

        self.output_text = tk.Text(root, height=10, width=80)
        self.output_text.pack()

        self.canvas = tk.Canvas(root, width=600, height=400)
        self.canvas.pack()

    def format_code(self):
        code = self.input_text.get("1.0", tk.END)
        formatter = HTMLFormatter()
        formatted_code = formatter.format_html(code)
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, formatted_code)

    def visualize_html(self):
        code = self.input_text.get("1.0", tk.END)
        formatter = HTMLFormatter()
        parser = HTMLTreeBuilder()
        parser.feed(code)
        tree = parser.get_tree()
        graph = formatter.visualize_html_tree(tree)
        graph.render('html_tree', format='png', cleanup=False)
        img = Image.open('html_tree.png')
        img = img.resize((600, 400))
        img = ImageTk.PhotoImage(img)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=img)
        self.canvas.image = img

if __name__ == "__main__":
    root = tk.Tk()
    app = FormatterGUI(root)
    root.mainloop()
