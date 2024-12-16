import tkinter as tk
from html.parser import HTMLParser
from tkinter import messagebox

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

    def handle_decl(self, decl):
        # Handle DOCTYPE declarations
        # Store it as a special node
        node = Node(is_doctype=True, data=decl.upper())
        self.stack[-1].add_child(node)

    def handle_starttag(self, tag, attrs):
        # If it's a void element, add and don't push to stack
        if tag.lower() in VOID_ELEMENTS:
            node = Node(tag=tag, attrs=dict(attrs))
            self.stack[-1].add_child(node)
        else:
            node = Node(tag=tag, attrs=dict(attrs))
            self.stack[-1].add_child(node)
            self.stack.append(node)

    def handle_endtag(self, tag):
        # Pop only if the tag is on the stack and not a void element
        if tag.lower() not in VOID_ELEMENTS and len(self.stack) > 1:
            # Pop until we find a matching start tag
            # (For well-formed HTML, it should be the top)
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
        try:
            parser.feed(code)
            parser.close()
        except Exception as e:
            messagebox.showerror("Parse Error", str(e))
            return code

        tree = parser.get_tree()
        formatted = self.format_node(tree, 0)
        # Strip extra whitespace and ensure newline at end
        return formatted.strip() + "\n"

    def format_node(self, node, depth):
        if node.tag == "__ROOT__":
            result = ""
            for child in node.children:
                result += self.format_node(child, depth)
            return result

        indent = " " * (depth * self.indent_size)

        # Handle doctype
        if node.is_doctype:
            return f"<!{node.data}>\n"

        # Handle comment
        if node.is_comment:
            return indent + f"<!-- {node.data} -->\n"

        # Text node
        if node.tag is None and node.data is not None:
            # Return text as is, with indentation
            # Keep as a block text if it has multiple lines
            lines = node.data.split('\n')
            formatted_lines = []
            for line in lines:
                line = line.strip()
                if line:
                    formatted_lines.append(indent + line)
            if not formatted_lines:
                return ""
            return "\n".join(formatted_lines) + "\n"

        # Element node
        attrs_str = ""
        if node.attrs:
            parts = [f'{k}="{v}"' for k,v in node.attrs.items()]
            attrs_str = " " + " ".join(parts)

        start_tag = f"<{node.tag}{attrs_str}>"

        # Void element: no children, no closing tag
        if node.tag.lower() in VOID_ELEMENTS:
            return indent + start_tag + "\n"

        if not node.children:
            # Empty element
            return indent + start_tag + f"</{node.tag}>\n"

        # If children exist, determine if we can inline them
        # Check if all children are text-only
        if all(c.tag is None and not c.is_comment and not c.is_doctype for c in node.children):
            # Inline text children
            inline_text = " ".join(c.data for c in node.children if c.data)
            return indent + start_tag + inline_text + f"</{node.tag}>\n"
        else:
            # Block format children
            result = indent + start_tag + "\n"
            for c in node.children:
                result += self.format_node(c, depth + 1)
            result += indent + f"</{node.tag}>\n"
            return result

class FormatterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("HTML Code Formatter")

        self.input_label = tk.Label(root, text="Unformatted HTML:")
        self.input_label.pack()

        self.input_text = tk.Text(root, height=15, width=80)
        self.input_text.pack()

        self.format_button = tk.Button(root, text="Format Code", command=self.format_code)
        self.format_button.pack()

        self.output_label = tk.Label(root, text="Formatted HTML:")
        self.output_label.pack()

        self.output_text = tk.Text(root, height=15, width=80)
        self.output_text.pack()

    def format_code(self):
        code = self.input_text.get("1.0", tk.END)
        formatter = HTMLFormatter()
        formatted_code = formatter.format_html(code)
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, formatted_code)

if __name__ == "__main__":
    root = tk.Tk()
    app = FormatterGUI(root)
    root.mainloop()
