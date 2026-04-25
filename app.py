import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import file_ops

# ── Windows 11 light palette ─────────────────────────────────────────────────
BG          = "#f3f3f3"
TOPBAR_BG   = "#ffffff"
SIDEBAR_BG  = "#f9f9f9"
CONTENT_BG  = "#ffffff"
ITEM_BG     = "#ffffff"
ITEM_HOVER  = "#e5e5e5"
ITEM_SEL    = "#ddeeff"
BORDER      = "#e0e0e0"
ACCENT      = "#0067c0"
TEXT_MAIN   = "#1a1a1a"
TEXT_SUB    = "#555555"
TEXT_DIM    = "#999999"
TOOLBAR_BTN = "#f5f5f5"
TOOLBAR_HOV = "#e0e0e0"
TOOLBAR_ACT = "#d0d0d0"

FOLDER_GOLD  = "#ffb900"
FOLDER_LIGHT = "#ffd75e"
FOLDER_DARK  = "#e09b00"
FOLDER_BODY  = "#ffc73a"


def draw_folder(canvas, cx, cy, w=72, h=56, hover=False, selected=False):
    """Draw a Windows-style yellow folder icon centred at cx,cy."""
    canvas.delete("icon")
    if hover or selected:
        gold  = "#ffd75e"; light = "#ffe799"; dark = "#c98b00"; body = "#ffcc4d"
    else:
        gold  = FOLDER_GOLD; light = FOLDER_LIGHT; dark = FOLDER_DARK; body = FOLDER_BODY

    x1, y1 = cx - w//2, cy - h//2
    x2, y2 = cx + w//2, cy + h//2
    tab_w   = int(w * 0.38)
    tab_h   = int(h * 0.13)
    body_y  = y1 + int(h * 0.20)

    # Back panel
    canvas.create_rectangle(x1, body_y, x2, y2,
                             fill=dark, outline="", tags="icon")
    # Tab
    canvas.create_rectangle(x1, body_y - tab_h, x1 + tab_w, body_y + 2,
                             fill=dark, outline="", tags="icon")
    # Round top-right of tab (small triangle fake)
    canvas.create_polygon(x1+tab_w, body_y-tab_h,
                           x1+tab_w+tab_h, body_y-tab_h,
                           x1+tab_w+tab_h, body_y,
                           fill=dark, outline="", tags="icon")
    # Body
    canvas.create_rectangle(x1, body_y, x2, y2,
                             fill=body, outline="", tags="icon")
    # Front lighter panel
    front_y = body_y + int(h * 0.12)
    canvas.create_rectangle(x1+2, front_y, x2-2, y2-2,
                             fill=gold, outline="", tags="icon")
    # Top shine strip
    canvas.create_rectangle(x1+2, front_y, x2-2, front_y + int(h*0.09),
                             fill=light, outline="", tags="icon")
    # Subtle bottom shadow
    canvas.create_rectangle(x1+2, y2 - int(h*0.09), x2-2, y2-2,
                             fill=dark, outline="", tags="icon")


class FolderTile(tk.Frame):
    W, H = 100, 100

    def __init__(self, parent, name, on_single, on_double, on_right):
        super().__init__(parent, bg=ITEM_BG,
                         width=self.W, height=self.H, cursor="hand2")
        self.pack_propagate(False)
        self.name      = name
        self._sel      = False
        self._hov      = False

        self.cvs = tk.Canvas(self, width=self.W, height=68,
                             bg=ITEM_BG, highlightthickness=0)
        self.cvs.pack()
        draw_folder(self.cvs, self.W//2, 36)

        lbl_text = name if len(name) <= 15 else name[:13] + "…"
        self.lbl = tk.Label(self, text=lbl_text, bg=ITEM_BG,
                            fg=TEXT_MAIN, font=("Segoe UI", 8),
                            wraplength=self.W-6, justify=tk.CENTER)
        self.lbl.pack()

        for w in (self, self.cvs, self.lbl):
            w.bind("<Button-1>",        lambda e: on_single(self))
            w.bind("<Double-Button-1>", lambda e: on_double(self))
            w.bind("<Button-3>",        lambda e: on_right(self, e))
            w.bind("<Enter>",           self._enter)
            w.bind("<Leave>",           self._leave)

    def _apply(self):
        col = ITEM_SEL if self._sel else (ITEM_HOVER if self._hov else ITEM_BG)
        self.config(bg=col)
        self.cvs.config(bg=col)
        self.lbl.config(bg=col)
        draw_folder(self.cvs, self.W//2, 36,
                    hover=self._hov, selected=self._sel)

    def set_selected(self, v):
        self._sel = v; self._apply()

    def _enter(self, _=None):
        self._hov = True
        if not self._sel: self._apply()

    def _leave(self, _=None):
        self._hov = False
        if not self._sel: self._apply()


class FileExplorerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("File Explorer")
        self.root.geometry("1100x680")
        self.root.configure(bg=BG)
        self.root.minsize(700, 450)

        self.current_path  = os.path.expanduser("~")
        self.history       = [self.current_path]
        self.hidx          = 0
        self.sel_tile      = None
        self.sel_path      = None
        self._tiles        = []

        self._styles()
        self._build_titlebar()
        self._build_toolbar()
        self._build_body()
        self._build_statusbar()

        self.navigate(self.current_path, push=False)

    # ── TTK styles ────────────────────────────────────────────────────────────
    def _styles(self):
        s = ttk.Style()
        s.theme_use("clam")
        s.configure("Treeview",
            background=SIDEBAR_BG, foreground=TEXT_MAIN,
            fieldbackground=SIDEBAR_BG, rowheight=28,
            font=("Segoe UI", 9), borderwidth=0, relief="flat")
        s.configure("Treeview.Heading", background=SIDEBAR_BG,
                    foreground=TEXT_DIM, font=("Segoe UI", 8, "bold"))
        s.map("Treeview",
              background=[("selected", ITEM_SEL)],
              foreground=[("selected", TEXT_MAIN)])
        s.configure("Vertical.TScrollbar", troughcolor=BG, background=BORDER)
        s.configure("Horizontal.TScrollbar", troughcolor=BG, background=BORDER)

    # ── Title bar (mimics Windows chrome) ─────────────────────────────────────
    def _build_titlebar(self):
        bar = tk.Frame(self.root, bg=TOPBAR_BG,
                       highlightbackground=BORDER, highlightthickness=1)
        bar.pack(side=tk.TOP, fill=tk.X)

        # Tab label
        tab = tk.Frame(bar, bg=TOPBAR_BG)
        tab.pack(side=tk.LEFT, padx=6, pady=4)
        tk.Label(tab, text="🗂", bg=TOPBAR_BG,
                 font=("Segoe UI", 11)).pack(side=tk.LEFT)
        self.title_var = tk.StringVar(value="File Explorer")
        tk.Label(tab, textvariable=self.title_var, bg=TOPBAR_BG,
                 fg=TEXT_MAIN, font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=4)

        # Window controls (decorative)
        ctrl = tk.Frame(bar, bg=TOPBAR_BG)
        ctrl.pack(side=tk.RIGHT)
        for sym, col, hcol in [("─", TOPBAR_BG, TOOLBAR_HOV),
                                ("□", TOPBAR_BG, TOOLBAR_HOV),
                                ("✕", TOPBAR_BG, "#c42b1c")]:
            b = tk.Button(ctrl, text=sym, bg=TOPBAR_BG, fg=TEXT_MAIN,
                          relief=tk.FLAT, font=("Segoe UI", 10),
                          width=4, pady=4, bd=0,
                          activebackground=hcol, activeforeground="#ffffff",
                          cursor="hand2")
            b.pack(side=tk.LEFT)

    # ── Nav + address bar ─────────────────────────────────────────────────────
    def _build_toolbar(self):
        # Row 1: nav + address
        nav_bar = tk.Frame(self.root, bg=TOPBAR_BG)
        nav_bar.pack(side=tk.TOP, fill=tk.X)
        tk.Frame(nav_bar, bg=BORDER, height=1).pack(side=tk.BOTTOM, fill=tk.X)

        nav = tk.Frame(nav_bar, bg=TOPBAR_BG)
        nav.pack(side=tk.LEFT, padx=8, pady=6)

        self.btn_back = self._nav_btn(nav, "←", self.go_back)
        self.btn_fwd  = self._nav_btn(nav, "→", self.go_forward)
        self._nav_btn(nav, "↑", self.go_up)
        self._nav_btn(nav, "↻", lambda: self.navigate(self.current_path, push=False))

        # Address bar
        addr = tk.Frame(nav_bar, bg="#ffffff",
                        highlightbackground=BORDER, highlightthickness=1)
        addr.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6, pady=6)
        self.path_var = tk.StringVar()
        tk.Entry(addr, textvariable=self.path_var, bg="#ffffff",
                 fg=TEXT_MAIN, font=("Segoe UI", 10), relief=tk.FLAT,
                 bd=5, insertbackground=ACCENT
                 ).pack(fill=tk.X)
        addr.bind_all("<Return>",
                      lambda e: self.navigate(self.path_var.get().strip()))

        # Row 2: action toolbar (New, Cut, Copy, Rename, Delete, Sort, View)
        tb = tk.Frame(self.root, bg=TOPBAR_BG)
        tb.pack(side=tk.TOP, fill=tk.X)
        tk.Frame(tb, bg=BORDER, height=1).pack(side=tk.BOTTOM, fill=tk.X)

        inner = tk.Frame(tb, bg=TOPBAR_BG)
        inner.pack(side=tk.LEFT, padx=8, pady=4)

        # New button (dropdown-style)
        new_btn = self._tb_btn(inner, "⊕  New  ▾", None)
        new_btn.config(command=lambda: self._new_menu(new_btn))

        tk.Frame(inner, bg=BORDER, width=1, height=22).pack(side=tk.LEFT, padx=6)

        self._tb_btn(inner, "✂", None, tip="Cut")
        self._tb_btn(inner, "⎘", None, tip="Copy")
        self._tb_btn(inner, "📋", None, tip="Paste")

        tk.Frame(inner, bg=BORDER, width=1, height=22).pack(side=tk.LEFT, padx=6)

        self._tb_btn(inner, "✎  Rename", self.rename_item)
        self._tb_btn(inner, "🗑  Delete", self.delete_item)

        tk.Frame(inner, bg=BORDER, width=1, height=22).pack(side=tk.LEFT, padx=6)
        self._tb_btn(inner, "⊞  Sort ▾", None)
        self._tb_btn(inner, "👁  View ▾", None)

        # Details on right
        tk.Label(tb, text="Details", bg=TOPBAR_BG, fg=TEXT_SUB,
                 font=("Segoe UI", 9), cursor="hand2",
                 padx=12).pack(side=tk.RIGHT, pady=4)

    def _nav_btn(self, parent, text, cmd):
        b = tk.Button(parent, text=text, command=cmd,
            bg=TOPBAR_BG, fg=TEXT_MAIN, relief=tk.FLAT,
            font=("Segoe UI", 11), width=3, cursor="hand2",
            activebackground=TOOLBAR_HOV, bd=0)
        b.pack(side=tk.LEFT, padx=1)
        b.bind("<Enter>", lambda e: b.config(bg=TOOLBAR_HOV))
        b.bind("<Leave>", lambda e: b.config(bg=TOPBAR_BG))
        return b

    def _tb_btn(self, parent, text, cmd, tip=""):
        b = tk.Button(parent, text=text, command=cmd if cmd else lambda: None,
            bg=TOOLBAR_BTN, fg=TEXT_MAIN, relief=tk.FLAT,
            font=("Segoe UI", 9), padx=10, pady=3,
            cursor="hand2", activebackground=TOOLBAR_ACT, bd=0,
            highlightbackground=BORDER, highlightthickness=0)
        b.pack(side=tk.LEFT, padx=2)
        b.bind("<Enter>", lambda e: b.config(bg=TOOLBAR_HOV))
        b.bind("<Leave>", lambda e: b.config(bg=TOOLBAR_BTN))
        return b

    def _new_menu(self, widget):
        m = tk.Menu(self.root, tearoff=0, font=("Segoe UI", 9),
                    bg=TOPBAR_BG, fg=TEXT_MAIN,
                    activebackground=ITEM_SEL, activeforeground=TEXT_MAIN)
        m.add_command(label="📁  Folder", command=self.create_folder)
        m.add_command(label="📄  File",   command=self.create_file)
        x = widget.winfo_rootx()
        y = widget.winfo_rooty() + widget.winfo_height()
        m.tk_popup(x, y)

    # ── Body: sidebar + content ───────────────────────────────────────────────
    def _build_body(self):
        body = tk.Frame(self.root, bg=BG)
        body.pack(fill=tk.BOTH, expand=True)

        # ── Content area ──
        content = tk.Frame(body, bg=CONTENT_BG)
        content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Horizontal scrollbar at bottom
        hbar = ttk.Scrollbar(content, orient=tk.HORIZONTAL)
        hbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Vertical scrollbar at right
        vbar = ttk.Scrollbar(content, orient=tk.VERTICAL)
        vbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.cvs = tk.Canvas(content, bg=CONTENT_BG, highlightthickness=0,
                             xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        self.cvs.pack(fill=tk.BOTH, expand=True)
        hbar.config(command=self.cvs.xview)
        vbar.config(command=self.cvs.yview)

        self.grid_frame = tk.Frame(self.cvs, bg=CONTENT_BG)
        self.grid_win = self.cvs.create_window((0, 0), window=self.grid_frame,
                                                anchor="nw")

        self.grid_frame.bind("<Configure>", self._on_frame_config)
        self.cvs.bind("<Configure>",        self._on_canvas_config)
        self.cvs.bind("<MouseWheel>",
                      lambda e: self.cvs.yview_scroll(-1*(e.delta//120), "units"))
        self.cvs.bind("<Shift-MouseWheel>",
                      lambda e: self.cvs.xview_scroll(-1*(e.delta//120), "units"))
        self.cvs.bind("<Button-1>",  self._deselect)
        self.grid_frame.bind("<Button-1>", self._deselect)
        self.cvs.bind("<Button-3>",  self._bg_ctx)
        self.grid_frame.bind("<Button-3>", self._bg_ctx)

    def _on_frame_config(self, _=None):
        self.cvs.configure(scrollregion=self.cvs.bbox("all"))

    def _on_canvas_config(self, event):
        self.cvs.itemconfig(self.grid_win, width=event.width)
        self._relayout()

    # ── Status bar ────────────────────────────────────────────────────────────
    def _build_statusbar(self):
        bar = tk.Frame(self.root, bg=BG,
                       highlightbackground=BORDER, highlightthickness=1)
        bar.pack(side=tk.BOTTOM, fill=tk.X)
        inner = tk.Frame(bar, bg=BG)
        inner.pack(fill=tk.X, padx=14, pady=3)
        self.status_var = tk.StringVar(value="")
        tk.Label(inner, textvariable=self.status_var, bg=BG,
                 fg=TEXT_SUB, font=("Segoe UI", 8),
                 anchor=tk.W).pack(side=tk.LEFT)
        # View toggle icons (decorative)
        tk.Label(inner, text="☰  ⊞", bg=BG, fg=TEXT_DIM,
                 font=("Segoe UI", 10)).pack(side=tk.RIGHT)

    # ── Navigation ────────────────────────────────────────────────────────────
    def navigate(self, path, push=True):
        path = path.strip()
        if not os.path.isdir(path):
            messagebox.showerror("Error", f"Not a folder:\n{path}")
            return
        self.current_path = path
        self.path_var.set(path)
        folder_name = os.path.basename(path) or path
        self.title_var.set(folder_name or "File Explorer")
        if push:
            self.history = self.history[:self.hidx+1]
            self.history.append(path)
            self.hidx = len(self.history)-1
        self._update_nav()
        self._refresh()

    def go_back(self):
        if self.hidx > 0:
            self.hidx -= 1
            self.navigate(self.history[self.hidx], push=False)

    def go_forward(self):
        if self.hidx < len(self.history)-1:
            self.hidx += 1
            self.navigate(self.history[self.hidx], push=False)

    def go_up(self):
        p = os.path.dirname(self.current_path)
        if p != self.current_path:
            self.navigate(p)

    def _update_nav(self):
        cb = self.hidx > 0
        cf = self.hidx < len(self.history)-1
        self.btn_back.config(state=tk.NORMAL if cb else tk.DISABLED,
                             fg=TEXT_MAIN if cb else TEXT_DIM)
        self.btn_fwd.config(state=tk.NORMAL if cf else tk.DISABLED,
                            fg=TEXT_MAIN if cf else TEXT_DIM)

    # ── Grid ──────────────────────────────────────────────────────────────────
    def _refresh(self):
        for t in self._tiles: t.destroy()
        self._tiles    = []
        self.sel_tile  = None
        self.sel_path  = None

        folders, files = file_ops.list_directory(self.current_path)
        total = len(folders) + len(files)
        self.status_var.set(f"{total} item{'s' if total != 1 else ''}")

        if total == 0:
            tk.Label(self.grid_frame, text="This folder is empty",
                     bg=CONTENT_BG, fg=TEXT_DIM,
                     font=("Segoe UI", 12)).grid(row=0, column=0,
                                                  padx=40, pady=60)
            self._on_frame_config()
            return

        for name in folders:
            tile = FolderTile(self.grid_frame, name,
                              self._click, self._dbl, self._rclick)
            self._tiles.append(tile)

        self._relayout()

    def _relayout(self):
        # Remove existing grid placements
        for t in self._tiles:
            t.grid_forget()

        w         = self.cvs.winfo_width() or 900
        col_count = max(1, (w - 16) // (FolderTile.W + 8))
        row = col  = 0
        for tile in self._tiles:
            tile.grid(row=row, column=col, padx=4, pady=4, sticky="n")
            col += 1
            if col >= col_count:
                col = 0; row += 1

        self.grid_frame.update_idletasks()
        self._on_frame_config()

    # ── Tile events ───────────────────────────────────────────────────────────
    def _click(self, tile):
        if self.sel_tile and self.sel_tile != tile:
            self.sel_tile.set_selected(False)
        tile.set_selected(True)
        self.sel_tile = tile
        self.sel_path = os.path.join(self.current_path, tile.name)
        self.status_var.set(f"1 item selected  ·  {tile.name}")

    def _dbl(self, tile):
        self.navigate(os.path.join(self.current_path, tile.name))

    def _rclick(self, tile, event):
        self._click(tile)
        m = tk.Menu(self.root, tearoff=0, font=("Segoe UI", 9),
                    bg=TOPBAR_BG, fg=TEXT_MAIN,
                    activebackground=ITEM_SEL, activeforeground=TEXT_MAIN)
        m.add_command(label="Open",   command=lambda: self._dbl(tile))
        m.add_separator()
        m.add_command(label="Rename", command=self.rename_item)
        m.add_command(label="Delete", command=self.delete_item)
        m.tk_popup(event.x_root, event.y_root)

    def _deselect(self, _=None):
        if self.sel_tile:
            self.sel_tile.set_selected(False)
            self.sel_tile = None
            self.sel_path = None
            folders, files = file_ops.list_directory(self.current_path)
            total = len(folders) + len(files)
            self.status_var.set(f"{total} item{'s' if total != 1 else ''}")

    def _bg_ctx(self, event):
        m = tk.Menu(self.root, tearoff=0, font=("Segoe UI", 9),
                    bg=TOPBAR_BG, fg=TEXT_MAIN,
                    activebackground=ITEM_SEL, activeforeground=TEXT_MAIN)
        m.add_command(label="New Folder", command=self.create_folder)
        m.add_command(label="New File",   command=self.create_file)
        m.add_separator()
        m.add_command(label="Refresh",
                      command=lambda: self.navigate(self.current_path, push=False))
        m.tk_popup(event.x_root, event.y_root)

    # ── CRUD ──────────────────────────────────────────────────────────────────
    def create_folder(self):
        name = simpledialog.askstring("New Folder", "Folder name:",
                                      parent=self.root)
        if name:
            try:
                file_ops.create_folder(self.current_path, name)
                self._refresh()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def create_file(self):
        name = simpledialog.askstring("New File", "File name:",
                                      parent=self.root)
        if name:
            try:
                file_ops.create_file(self.current_path, name)
                self._refresh()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def rename_item(self):
        if not self.sel_path:
            messagebox.showinfo("No selection", "Click a folder first.")
            return
        old  = os.path.basename(self.sel_path)
        new  = simpledialog.askstring("Rename", "New name:",
                                      initialvalue=old, parent=self.root)
        if new and new != old:
            try:
                file_ops.rename_item(self.sel_path, new)
                self.sel_tile = None; self.sel_path = None
                self._refresh()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def delete_item(self):
        if not self.sel_path:
            messagebox.showinfo("No selection", "Click a folder first.")
            return
        name = os.path.basename(self.sel_path)
        if messagebox.askyesno("Delete",
                f"Permanently delete '{name}'?\nThis cannot be undone."):
            try:
                file_ops.delete_item(self.sel_path)
                self.sel_tile = None; self.sel_path = None
                self._refresh()
            except Exception as e:
                messagebox.showerror("Error", str(e))
