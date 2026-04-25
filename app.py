import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import file_ops


class FileExplorerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gesture Explorer")
        self.root.geometry("1000x650")
        self.root.configure(bg="#1e1e2e")

        self.current_path = os.path.expanduser("~")
        self.selected_item_path = None

        self._build_styles()
        self._build_toolbar()
        self._build_main_area()
        self._build_status_bar()

        self.refresh_tree()
        self.refresh_list(self.current_path)

    # ── Styles ──────────────────────────────────────────────────────────────

    def _build_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Treeview",
            background="#181825", foreground="#cdd6f4",
            fieldbackground="#181825", rowheight=24,
            font=("Courier New", 10))
        style.configure("Treeview.Heading",
            background="#313244", foreground="#cba6f7", font=("Courier New", 10, "bold"))
        style.map("Treeview", background=[("selected", "#45475a")])

        style.configure("TFrame", background="#1e1e2e")
        style.configure("TPanedwindow", background="#1e1e2e")

    # ── Toolbar ─────────────────────────────────────────────────────────────

    def _build_toolbar(self):
        toolbar = tk.Frame(self.root, bg="#313244", pady=4)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        btn_cfg = dict(bg="#45475a", fg="#cdd6f4", relief=tk.FLAT,
                       padx=10, pady=3, cursor="hand2",
                       font=("Courier New", 10), activebackground="#585b70")

        tk.Button(toolbar, text="⬆ Up", command=self.go_up, **btn_cfg).pack(side=tk.LEFT, padx=4)
        tk.Button(toolbar, text="📁 New Folder", command=self.create_folder, **btn_cfg).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="📄 New File", command=self.create_file, **btn_cfg).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="✏ Rename", command=self.rename_item, **btn_cfg).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="🗑 Delete", command=self.delete_item, **btn_cfg).pack(side=tk.LEFT, padx=2)

        self.path_var = tk.StringVar(value=self.current_path)
        path_entry = tk.Entry(toolbar, textvariable=self.path_var, bg="#181825",
                              fg="#a6e3a1", insertbackground="#cdd6f4",
                              font=("Courier New", 10), relief=tk.FLAT, bd=4)
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        path_entry.bind("<Return>", self.navigate_to_path)

    # ── Main Area ────────────────────────────────────────────────────────────

    def _build_main_area(self):
        paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        # Left: folder tree
        left_frame = tk.Frame(paned, bg="#181825")
        paned.add(left_frame, weight=1)

        tree_scroll = ttk.Scrollbar(left_frame)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree = ttk.Treeview(left_frame, yscrollcommand=tree_scroll.set, selectmode="browse")
        self.tree.heading("#0", text="Folders", anchor=tk.W)
        self.tree.pack(fill=tk.BOTH, expand=True)
        tree_scroll.config(command=self.tree.yview)

        self.tree.bind("<<TreeviewOpen>>", self.on_tree_open)
        self.tree.bind("<ButtonRelease-1>", self.on_tree_select)
        self.tree.bind("<Button-3>", self.show_tree_context_menu)

        # Right: split between file list and editor
        right_paned = ttk.PanedWindow(paned, orient=tk.VERTICAL)
        paned.add(right_paned, weight=3)

        # File list
        list_frame = tk.Frame(right_paned, bg="#181825")
        right_paned.add(list_frame, weight=2)

        list_scroll = ttk.Scrollbar(list_frame)
        list_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.file_list = tk.Listbox(list_frame, yscrollcommand=list_scroll.set,
            bg="#181825", fg="#cdd6f4", selectbackground="#45475a",
            font=("Courier New", 11), relief=tk.FLAT, bd=0,
            activestyle="none", cursor="hand2")
        self.file_list.pack(fill=tk.BOTH, expand=True)
        list_scroll.config(command=self.file_list.yview)

        self.file_list.bind("<Double-Button-1>", self.on_list_double_click)
        self.file_list.bind("<ButtonRelease-1>", self.on_list_select)
        self.file_list.bind("<Button-3>", self.show_list_context_menu)

        # Editor
        editor_frame = tk.Frame(right_paned, bg="#181825")
        right_paned.add(editor_frame, weight=3)

        editor_label = tk.Label(editor_frame, text="File Editor",
            bg="#313244", fg="#cba6f7", font=("Courier New", 10, "bold"), pady=4)
        editor_label.pack(fill=tk.X)

        editor_scroll = ttk.Scrollbar(editor_frame)
        editor_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.editor = tk.Text(editor_frame, yscrollcommand=editor_scroll.set,
            bg="#181825", fg="#cdd6f4", insertbackground="#cdd6f4",
            font=("Courier New", 11), relief=tk.FLAT, bd=8,
            undo=True, wrap=tk.WORD)
        self.editor.pack(fill=tk.BOTH, expand=True)
        editor_scroll.config(command=self.editor.yview)

        save_btn = tk.Button(editor_frame, text="💾 Save File",
            command=self.save_file,
            bg="#a6e3a1", fg="#1e1e2e", font=("Courier New", 10, "bold"),
            relief=tk.FLAT, padx=10, pady=4, cursor="hand2")
        save_btn.pack(pady=4)

        self.editing_path = None

    # ── Status Bar ───────────────────────────────────────────────────────────

    def _build_status_bar(self):
        self.status_var = tk.StringVar(value="Ready")
        status = tk.Label(self.root, textvariable=self.status_var,
            bg="#313244", fg="#a6adc8", anchor=tk.W,
            font=("Courier New", 9), padx=8)
        status.pack(side=tk.BOTTOM, fill=tk.X)

    # ── Tree ─────────────────────────────────────────────────────────────────

    def refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        root_node = self.tree.insert("", tk.END, text=self.current_path,
                                     values=[self.current_path], open=True)
        self._populate_tree(root_node, self.current_path)

    def _populate_tree(self, parent, path):
        folders, _ = file_ops.list_directory(path)
        for folder in folders:
            full = os.path.join(path, folder)
            node = self.tree.insert(parent, tk.END, text=f"📁 {folder}", values=[full])
            self.tree.insert(node, tk.END, text="loading...")  # lazy placeholder

    def on_tree_open(self, event):
        node = self.tree.focus()
        children = self.tree.get_children(node)
        if len(children) == 1 and self.tree.item(children[0], "text") == "loading...":
            self.tree.delete(children[0])
            path = self.tree.item(node, "values")[0]
            self._populate_tree(node, path)

    def on_tree_select(self, event):
        node = self.tree.focus()
        if node:
            path = self.tree.item(node, "values")[0]
            if path and os.path.isdir(path):
                self.current_path = path
                self.path_var.set(path)
                self.refresh_list(path)
                self.status_var.set(f"Browsing: {path}")

    # ── File List ─────────────────────────────────────────────────────────────

    def refresh_list(self, path):
        self.file_list.delete(0, tk.END)
        folders, files = file_ops.list_directory(path)
        for f in folders:
            self.file_list.insert(tk.END, f"📁  {f}")
        for f in files:
            self.file_list.insert(tk.END, f"📄  {f}")
        self._list_items = [(f, True) for f in folders] + [(f, False) for f in files]

    def on_list_double_click(self, event):
        idx = self.file_list.curselection()
        if not idx:
            return
        name, is_dir = self._list_items[idx[0]]
        full_path = os.path.join(self.current_path, name)
        if is_dir:
            self.current_path = full_path
            self.path_var.set(full_path)
            self.refresh_list(full_path)
            self.refresh_tree()
            self.status_var.set(f"Entered: {full_path}")
        else:
            self.open_file(full_path)

    def on_list_select(self, event):
        idx = self.file_list.curselection()
        if idx:
            name, _ = self._list_items[idx[0]]
            self.selected_item_path = os.path.join(self.current_path, name)

    # ── Editor ────────────────────────────────────────────────────────────────

    def open_file(self, path):
        try:
            content = file_ops.read_file(path)
            self.editor.delete("1.0", tk.END)
            self.editor.insert(tk.END, content)
            self.editing_path = path
            self.status_var.set(f"Editing: {path}")
        except Exception as e:
            messagebox.showerror("Error", f"Cannot open file:\n{e}")

    def save_file(self):
        if not self.editing_path:
            messagebox.showinfo("No file", "No file is currently open in the editor.")
            return
        content = self.editor.get("1.0", tk.END)
        try:
            file_ops.write_file(self.editing_path, content)
            self.status_var.set(f"Saved: {self.editing_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not save:\n{e}")

    # ── Toolbar Actions ───────────────────────────────────────────────────────

    def go_up(self):
        parent = os.path.dirname(self.current_path)
        if parent != self.current_path:
            self.current_path = parent
            self.path_var.set(parent)
            self.refresh_list(parent)
            self.refresh_tree()

    def navigate_to_path(self, event=None):
        path = self.path_var.get().strip()
        if os.path.isdir(path):
            self.current_path = path
            self.refresh_list(path)
            self.refresh_tree()
        else:
            messagebox.showerror("Invalid path", f"Not a directory:\n{path}")

    def create_folder(self):
        name = simpledialog.askstring("New Folder", "Folder name:", parent=self.root)
        if name:
            try:
                file_ops.create_folder(self.current_path, name)
                self.refresh_list(self.current_path)
                self.refresh_tree()
                self.status_var.set(f"Created folder: {name}")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def create_file(self):
        name = simpledialog.askstring("New File", "File name:", parent=self.root)
        if name:
            try:
                path = file_ops.create_file(self.current_path, name)
                self.refresh_list(self.current_path)
                self.open_file(path)
                self.status_var.set(f"Created file: {name}")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def rename_item(self):
        if not self.selected_item_path:
            messagebox.showinfo("No selection", "Select a file or folder first.")
            return
        old_name = os.path.basename(self.selected_item_path)
        new_name = simpledialog.askstring("Rename", "New name:", initialvalue=old_name, parent=self.root)
        if new_name and new_name != old_name:
            try:
                file_ops.rename_item(self.selected_item_path, new_name)
                self.selected_item_path = None
                self.refresh_list(self.current_path)
                self.refresh_tree()
                self.status_var.set(f"Renamed to: {new_name}")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def delete_item(self):
        if not self.selected_item_path:
            messagebox.showinfo("No selection", "Select a file or folder first.")
            return
        name = os.path.basename(self.selected_item_path)
        confirm = messagebox.askyesno("Delete", f"Delete '{name}'?\nThis cannot be undone.")
        if confirm:
            try:
                file_ops.delete_item(self.selected_item_path)
                self.selected_item_path = None
                self.refresh_list(self.current_path)
                self.refresh_tree()
                self.status_var.set(f"Deleted: {name}")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    # ── Context Menus ─────────────────────────────────────────────────────────

    def show_list_context_menu(self, event):
        idx = self.file_list.nearest(event.y)
        if idx >= 0:
            self.file_list.selection_clear(0, tk.END)
            self.file_list.selection_set(idx)
            name, _ = self._list_items[idx]
            self.selected_item_path = os.path.join(self.current_path, name)

        menu = tk.Menu(self.root, tearoff=0, bg="#313244", fg="#cdd6f4",
                       activebackground="#45475a", font=("Courier New", 10))
        menu.add_command(label="📁 New Folder", command=self.create_folder)
        menu.add_command(label="📄 New File", command=self.create_file)
        if self.selected_item_path:
            menu.add_separator()
            menu.add_command(label="✏ Rename", command=self.rename_item)
            menu.add_command(label="🗑 Delete", command=self.delete_item)
        menu.tk_popup(event.x_root, event.y_root)

    def show_tree_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
        menu = tk.Menu(self.root, tearoff=0, bg="#313244", fg="#cdd6f4",
                       activebackground="#45475a", font=("Courier New", 10))
        menu.add_command(label="📁 New Folder", command=self.create_folder)
        menu.add_command(label="📄 New File", command=self.create_file)
        menu.tk_popup(event.x_root, event.y_root)
