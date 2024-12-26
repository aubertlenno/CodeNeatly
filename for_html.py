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
        self.errors = []

    def handle_decl(self, decl):
        try:
            node = Node(is_doctype=True, data=decl.upper())
            self.stack[-1].add_child(node)
        except Exception as e:
            self.errors.append(f"Error handling DOCTYPE: {e}")

    def handle_starttag(self, tag, attrs):
        try:
            # If it's a void element, add and don't push to stack
            if tag.lower() in VOID_ELEMENTS:
                node = Node(tag=tag, attrs=dict(attrs))
                self.stack[-1].add_child(node)
            else:
                node = Node(tag=tag, attrs=dict(attrs))
                self.stack[-1].add_child(node)
                self.stack.append(node)
        except Exception as e:
            self.errors.append(f"Error processing start tag <{tag}>: {e}")

    def handle_endtag(self, tag):
        try:
            if tag.lower() not in VOID_ELEMENTS and len(self.stack) > 1:
                # Pop until we find a matching start tag
                if self.stack[-1].tag == tag:
                    self.stack.pop()
                else:
                    self.errors.append(f"Warning: Unmatched end tag </{tag}>")
        except Exception as e:
            self.errors.append(f"Error processing end tag </{tag}>: {e}")

    def handle_data(self, data):
        try:
            stripped = data.strip()
            if stripped:
                node = Node(data=stripped)
                self.stack[-1].add_child(node)
        except Exception as e:
            self.errors.append(f"Error processing data: {e}")

    def handle_comment(self, data):
        try:
            node = Node(data=data.strip(), is_comment=True)
            self.stack[-1].add_child(node)
        except Exception as e:
            self.errors.append(f"Error processing comment: {e}")

    def get_tree(self):
        if len(self.stack) > 1:
            self.errors.append("Error: Missing end tags for some elements.")
        return self.root

    def get_errors(self):
        return self.errors


class HTMLFormatter:
    def __init__(self, indent_size=4):
        self.indent_size = indent_size

    def format_html(self, code):
        parser = HTMLTreeBuilder()
        try:
            # Check for basic HTML validity
            if "<" not in code or ">" not in code:
                raise ValueError("Input does not appear to be valid HTML.")

            parser.feed(code)
            parser.close()
        except ValueError as e:
            messagebox.showerror("Invalid Input", str(e))
            return code
        except Exception as e:
            messagebox.showerror("Parse Error", f"Critical Parsing Error: {e}")
            return code

        errors = parser.get_errors()
        if errors:
            messagebox.showwarning("HTML Warnings", "\n".join(errors))

        tree = parser.get_tree()
        formatted = self.format_node(tree, 0)
        return formatted.strip() + "\n"


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
            lines = node.data.split('\n')
            return "\n".join(indent + line.strip() for line in lines if line.strip()) + "\n"

        attrs_str = " ".join(f'{k}="{v}"' for k, v in node.attrs.items())
        start_tag = f"<{node.tag} {attrs_str}".strip() + ">"

        if node.tag.lower() in VOID_ELEMENTS:
            return indent + start_tag + "\n"

        if not node.children:
            return indent + start_tag + f"</{node.tag}>\n"

        result = indent + start_tag + "\n"
        for child in node.children:
            result += self.format_node(child, depth + 1)
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
