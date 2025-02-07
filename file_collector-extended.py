import os
import tkinter as tk
from tkinter import ttk, messagebox

class Node:
    """A simple class representing a file or folder node in our tree."""
    def __init__(self, path, is_file):
        self.path = path
        self.name = os.path.basename(path) if path else path
        self.is_file = is_file
        self.children = []
        self.var = None       # BooleanVar to keep track of the checkbox state
        self.parent = None    # Parent reference to allow upward update

def build_tree(root_path):
    """Recursively build a tree (of Node objects) from the given root_path."""
    if not os.path.isdir(root_path):
        # It's a file node
        return Node(root_path, True)

    # It's a directory node
    root_node = Node(root_path, False)
    for entry in sorted(os.listdir(root_path)):
        entry_path = os.path.join(root_path, entry)
        # Skip certain hidden/system files if you want
        # if entry.startswith('.'):
        #     continue
        entry_node = build_tree(entry_path)
        entry_node.parent = root_node
        root_node.children.append(entry_node)

    return root_node

def set_state_recursive(node, new_state):
    """Recursively set the checkbox state (True/False) for node and all its children."""
    node.var.set(new_state)
    for child in node.children:
        set_state_recursive(child, new_state)

def update_parent_state(node):
    """
    After a child's state changes, update its ancestors' state.
    - If ALL children are checked => parent is checked.
    - If ANY child is unchecked => parent is unchecked.
    Then recurse up the chain.
    """
    parent = node.parent
    if parent is None:
        return

    all_checked = all(child.var.get() for child in parent.children)
    parent.var.set(all_checked)
    update_parent_state(parent)

def on_check(node):
    """
    Called whenever a checkbox is toggled.
    - If a folder is toggled, set all its children to the same state.
    - Then update ancestor states accordingly.
    """
    new_state = node.var.get()
    if not node.is_file:   # For directories, propagate to children
        set_state_recursive(node, new_state)
    update_parent_state(node)

def create_checklist_ui(parent_frame, node, indent=0):
    """
    Recursively create checkbuttons for each node in the tree,
    indenting each child level for a hierarchical look.
    """

    # Make one row for this item
    row_frame = tk.Frame(parent_frame)
    row_frame.pack(anchor='w')

    # Add indentation label
    # Each indent is e.g., 3 or 4 spaces. You can adjust to your liking:
    indent_label = tk.Label(row_frame, text="    " * indent)
    indent_label.pack(side='left')

    # Create the checkbox
    node.var = tk.BooleanVar(value=False)
    cb = tk.Checkbutton(
        row_frame,
        text=node.name,
        variable=node.var,
        command=lambda n=node: on_check(n)
    )
    cb.pack(side='left', anchor='w')

    # If the node is a directory, create children below (with incremented indent)
    if not node.is_file:
        for child in node.children:
            create_checklist_ui(parent_frame, child, indent + 1)

def gather_selected_files(node, selected=None):
    """Traverse the tree and gather the paths of all checked files."""
    if selected is None:
        selected = []
    if node.is_file and node.var.get():
        selected.append(node.path)
    for child in node.children:
        gather_selected_files(child, selected)
    return selected

def write_file_contents(selected_files):
    """Given a list of file paths, write their contents to 'results.txt'."""
    result_file = "results.txt"

    with open(result_file, "w", encoding="utf-8") as result:
        for file_path in selected_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                result.write(f"{file_path}\n")
                result.write("==========================\n")
                result.write(content + "\n")
                result.write("==========================\n")
            except Exception as e:
                print(f"Error reading file {file_path}: {e}")

    messagebox.showinfo("Done", f"Selected files have been written to {result_file}.")

def generate_results(root_node):
    """Gather all checked files from the tree and write them to results.txt."""
    selected_files = gather_selected_files(root_node)
    if not selected_files:
        messagebox.showwarning("No Selection", "No files were selected.")
        return
    write_file_contents(selected_files)

def main():
    # Ask the user for the folder path via stdin
    folder = input("Enter the folder path to display checkboxes: ").strip()
    if not os.path.isdir(folder):
        print("The specified folder does not exist.")
        return

    # Build the tree of files/folders
    root_node = build_tree(folder)

    # Create the Tk GUI
    root = tk.Tk()
    root.title("Select Files and Folders")

    # A scrollable canvas if your folder has lots of items
    canvas = tk.Canvas(root)
    scrollbar = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    # Pack canvas + scrollbar side by side
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Build the hierarchical checklist
    create_checklist_ui(scrollable_frame, root_node, indent=0)

    # Add a button to generate results
    generate_button = tk.Button(root, text="Generate Results",
                                command=lambda: generate_results(root_node))
    generate_button.pack(pady=5)

    root.mainloop()

if __name__ == "__main__":
    main()