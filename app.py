import os
import platform
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import file_ops
import queue

# ── Palette ───────────────────────────────────────────────────────────────────
BG          = "#f3f3f3"
TOPBAR_BG   = "#ffffff"
CONTENT_BG  = "#ffffff"
ITEM_BG     = "#ffffff"
ITEM_HOVER  = "#e5e5e5"
ITEM_SEL    = "#ddeeff"
BORDER      = "#e0e0e0"
ACCENT      = "#0067c0"
TEXT_MAIN   = "#1a1a1a"
TEXT_SUB    = "#555555"
TEXT_DIM    = "#999999"
TOOLBAR_HOV = "#e0e0e0"

FOLDER_GOLD  = "#ffb900"
FOLDER_LIGHT = "#ffd75e"
FOLDER_DARK  = "#e09b00"
FOLDER_BODY  = "#ffc73a"

FILE_BG      = "#e8f0fe"
FILE_BORDER  = "#4a90d9"


# ── Folder icon ───────────────────────────────────────────────────────────────
def draw_folder(canvas, cx, cy, w=72, h=56, hover=False, selected=False):
    """Draw a Windows-style yellow folder icon centred at cx, cy."""
    canvas.delete("icon")
    if hover or selected:
        gold  = "#ffd75e"; light = "#ffe799"; dark = "#c98b00"; body = "#ffcc4d"
    else:
        gold  = FOLDER_GOLD; light = FOLDER_LIGHT; dark = FOLDER_DARK; body = FOLDER_BODY

    x1, y1 = cx - w // 2, cy - h // 2
    x2, y2 = cx + w // 2, cy + h // 2
    tab_w   = int(w * 0.38)
    tab_h   = int(h * 0.13)
    body_y  = y1 + int(h * 0.20)

    canvas.create_rectangle(x1, body_y, x2, y2, fill=dark, outline="", tags="icon")
    canvas.create_rectangle(x1, body_y - tab_h, x1 + tab_w, body_y + 2,
                            fill=dark, outline="", tags="icon")
    canvas.create_polygon(x1 + tab_w, body_y - tab_h,
                          x1 + tab_w + tab_h, body_y - tab_h,
                          x1 + tab_w + tab_h, body_y,
                          fill=dark, outline="", tags="icon")
    canvas.create_rectangle(x1, body_y, x2, y2, fill=body, outline="", tags="icon")
    front_y = body_y + int(h * 0.12)
    canvas.create_rectangle(x1 + 2, front_y, x2 - 2, y2 - 2,
                            fill=gold, outline="", tags="icon")
    canvas.create_rectangle(x1 + 2, front_y, x2 - 2, front_y + int(h * 0.09),
                            fill=light, outline="", tags="icon")
    canvas.create_rectangle(x1 + 2, y2 - int(h * 0.09), x2 - 2, y2 - 2,
                            fill=dark, outline="", tags="icon")


# ── Folder tile ───────────────────────────────────────────────────────────────
class FolderTile(tk.Frame):
    W, H   = 100, 100
    IS_DIR = True

    def __init__(self, parent, name, on_single, on_double, on_right):
        super().__init__(parent, bg=ITEM_BG,
                         width=self.W, height=self.H, cursor="hand2")
        self.pack_propagate(False)
        self.name = name
        self._sel = False
        self._hov = False

        self.cvs = tk.Canvas(self, width=self.W, height=68,
                             bg=ITEM_BG, highlightthickness=0)
        self.cvs.pack()
        draw_folder(self.cvs, self.W // 2, 36)

        lbl_text = name if len(name) <= 15 else name[:13] + "…"
        self.lbl = tk.Label(self, text=lbl_text, bg=ITEM_BG,
                            fg=TEXT_MAIN, font=("Segoe UI", 8),
                            wraplength=self.W - 6, justify=tk.CENTER)
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
        draw_folder(self.cvs, self.W // 2, 36,
                    hover=self._hov, selected=self._sel)

    def set_selected(self, v):
        self._sel = v
        self._apply()

    def _enter(self, _=None):
        self._hov = True
        if not self._sel:
            self._apply()

    def _leave(self, _=None):
        self._hov = False
        if not self._sel:
            self._apply()


# ── File tile ─────────────────────────────────────────────────────────────────
class FileTile(tk.Frame):
    W, H   = 100, 100
    IS_DIR = False

    def __init__(self, parent, name, on_single, on_double, on_right):
        super().__init__(parent, bg=ITEM_BG,
                         width=self.W, height=self.H, cursor="hand2")
        self.pack_propagate(False)
        self.name = name
        self._sel = False
        self._hov = False

        self.cvs = tk.Canvas(self, width=self.W, height=68,
                             bg=ITEM_BG, highlightthickness=0)
        self.cvs.pack()
        self._draw()

        lbl_text = name if len(name) <= 15 else name[:13] + "…"
        self.lbl = tk.Label(self, text=lbl_text, bg=ITEM_BG,
                            fg=TEXT_MAIN, font=("Segoe UI", 8),
                            wraplength=self.W - 6, justify=tk.CENTER)
        self.lbl.pack()

        for w in (self, self.cvs, self.lbl):
            w.bind("<Button-1>",        lambda e: on_single(self))
            w.bind("<Double-Button-1>", lambda e: on_double(self))
            w.bind("<Button-3>",        lambda e: on_right(self, e))
            w.bind("<Enter>",           self._enter)
            w.bind("<Leave>",           self._leave)

    def _draw(self):
        self.cvs.delete("icon")
        cx, cy = self.W // 2, 34
        w, h   = 36, 46
        x1, y1 = cx - w // 2, cy - h // 2
        x2, y2 = cx + w // 2, cy + h // 2
        fold   = 10
        bg     = FILE_BG if not self._sel else "#c8dcfc"
        self.cvs.create_polygon(
            x1, y1,  x2 - fold, y1,  x2, y1 + fold,  x2, y2,  x1, y2,
            fill=bg, outline=FILE_BORDER, tags="icon")
        self.cvs.create_polygon(
            x2 - fold, y1,  x2 - fold, y1 + fold,  x2, y1 + fold,
            fill="#c0d4f0", outline=FILE_BORDER, tags="icon")
        for i, yoff in enumerate([18, 24, 30]):
            self.cvs.create_line(x1 + 6, y1 + yoff, x2 - 6, y1 + yoff,
                                 fill=FILE_BORDER, tags="icon")

    def _apply(self):
        col = ITEM_SEL if self._sel else (ITEM_HOVER if self._hov else ITEM_BG)
        self.config(bg=col)
        self.cvs.config(bg=col)
        self.lbl.config(bg=col)
        self._draw()

    def set_selected(self, v):
        self._sel = v
        self._apply()

    def _enter(self, _=None):
        self._hov = True
        if not self._sel:
            self._apply()

    def _leave(self, _=None):
        self._hov = False
        if not self._sel:
            self._apply()


# ── App ───────────────────────────────────────────────────────────────────────
class FileExplorerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("File Explorer")
        self.root.geometry("1100x680")
        self.root.configure(bg=BG)
        self.root.minsize(700, 450)

        self.current_path = os.path.expanduser("~")
        self.history      = [self.current_path]
        self.hidx         = 0
        self.sel_tile     = None
        self.sel_path     = None
        self._tiles       = []

        self._build_toolbar()
        self._build_body()
        self._build_statusbar()

        self.root.bind("<Tab>",       self._on_tab)
        self.root.bind("<Shift-Tab>", self._on_shift_tab)
        self.root.bind("<Return>",    self._on_enter)

        # Queue must exist before navigate() in case a message arrives early
        self.ai_queue = queue.Queue()
        self.check_ai_queue()
        self.navigate(self.current_path, push=False)

    # ── Toolbar ───────────────────────────────────────────────────────────────
    def _build_toolbar(self):
        nav_bar = tk.Frame(self.root, bg=TOPBAR_BG)
        nav_bar.pack(side=tk.TOP, fill=tk.X)
        tk.Frame(nav_bar, bg=BORDER, height=1).pack(side=tk.BOTTOM, fill=tk.X)

        nav = tk.Frame(nav_bar, bg=TOPBAR_BG)
        nav.pack(side=tk.LEFT, padx=8, pady=6)

        self.btn_back = self._nav_btn(nav, "←", self.go_back)
        self.btn_fwd  = self._nav_btn(nav, "→", self.go_forward)
        self._nav_btn(nav, "↑", self.go_up)
        self._nav_btn(nav, "↻", lambda: self.navigate(self.current_path, push=False))

    def _nav_btn(self, parent, text, cmd):
        b = tk.Button(parent, text=text, command=cmd,
                      bg=TOPBAR_BG, fg=TEXT_MAIN, relief=tk.FLAT,
                      font=("Segoe UI", 11), width=3, cursor="hand2",
                      activebackground=TOOLBAR_HOV, bd=0)
        b.pack(side=tk.LEFT, padx=1)
        b.bind("<Enter>", lambda e: b.config(bg=TOOLBAR_HOV))
        b.bind("<Leave>", lambda e: b.config(bg=TOPBAR_BG))
        return b

    # ── Body ──────────────────────────────────────────────────────────────────
    def _build_body(self):
        body = tk.Frame(self.root, bg=BG)
        body.pack(fill=tk.BOTH, expand=True)

        content = tk.Frame(body, bg=CONTENT_BG)
        content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.cvs = tk.Canvas(content, bg=CONTENT_BG, highlightthickness=0)
        self.cvs.pack(fill=tk.BOTH, expand=True)

        self.grid_frame = tk.Frame(self.cvs, bg=CONTENT_BG)
        self.grid_win   = self.cvs.create_window((0, 0), window=self.grid_frame,
                                                  anchor="nw")

        self.grid_frame.bind("<Configure>", self._on_frame_config)
        self.cvs.bind("<Configure>",        self._on_canvas_config)

        # Cross-platform mousewheel scroll
        self.cvs.bind("<MouseWheel>",       self._on_scroll_y)
        self.cvs.bind("<Button-4>",         self._on_scroll_y)   # Linux scroll up
        self.cvs.bind("<Button-5>",         self._on_scroll_y)   # Linux scroll down
        self.cvs.bind("<Shift-MouseWheel>", self._on_scroll_x)

        self.cvs.bind("<Button-1>",         self._deselect)
        self.grid_frame.bind("<Button-1>",  self._deselect)
        self.cvs.bind("<Button-3>",         self._bg_ctx)
        self.grid_frame.bind("<Button-3>",  self._bg_ctx)

    def _on_scroll_y(self, event):
        if event.num == 4:          # Linux scroll up
            self.cvs.yview_scroll(-1, "units")
        elif event.num == 5:        # Linux scroll down
            self.cvs.yview_scroll(1, "units")
        else:
            # macOS: event.delta is ±1 already; Windows: ±120
            amount = -1 if event.delta > 0 else 1
            self.cvs.yview_scroll(amount, "units")

    def _on_scroll_x(self, event):
        amount = -1 if event.delta > 0 else 1
        self.cvs.xview_scroll(amount, "units")

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
        tk.Label(inner, text="☰  ⊞", bg=BG, fg=TEXT_DIM,
                 font=("Segoe UI", 10)).pack(side=tk.RIGHT)

    # ── Navigation ────────────────────────────────────────────────────────────
    def navigate(self, path, push=True):
        path = path.strip()
        if not os.path.isdir(path):
            messagebox.showerror("Error", f"Not a folder:\n{path}")
            return
        self.current_path = path
        self.root.title(os.path.basename(path) or path)
        if push:
            self.history = self.history[:self.hidx + 1]
            self.history.append(path)
            self.hidx = len(self.history) - 1
        self._update_nav()
        self._refresh()

    def go_back(self):
        if self.hidx > 0:
            self.hidx -= 1
            self.navigate(self.history[self.hidx], push=False)

    def go_forward(self):
        if self.hidx < len(self.history) - 1:
            self.hidx += 1
            self.navigate(self.history[self.hidx], push=False)

    def go_up(self):
        p = os.path.dirname(self.current_path)
        if p != self.current_path:
            self.navigate(p)

    def _update_nav(self):
        can_back = self.hidx > 0
        can_fwd  = self.hidx < len(self.history) - 1
        self.btn_back.config(state=tk.NORMAL if can_back else tk.DISABLED,
                             fg=TEXT_MAIN if can_back else TEXT_DIM)
        self.btn_fwd.config(state=tk.NORMAL if can_fwd else tk.DISABLED,
                            fg=TEXT_MAIN if can_fwd else TEXT_DIM)

    # ── Grid ──────────────────────────────────────────────────────────────────
    def _refresh(self):
        # Destroy ALL children (including any "empty folder" labels)
        for w in self.grid_frame.winfo_children():
            w.destroy()
        self._tiles   = []
        self.sel_tile = None
        self.sel_path = None

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

        for name in files:
            tile = FileTile(self.grid_frame, name,
                            self._click, self._open_file, self._rclick)
            self._tiles.append(tile)

        self._relayout()

    def _relayout(self):
        for t in self._tiles:
            t.grid_forget()

        w         = self.cvs.winfo_width() or 900
        col_count = max(1, (w - 16) // (FolderTile.W + 8))
        row = col = 0
        for tile in self._tiles:
            tile.grid(row=row, column=col, padx=4, pady=4, sticky="n")
            col += 1
            if col >= col_count:
                col = 0
                row += 1

        self.grid_frame.update_idletasks()
        self._on_frame_config()

    # ── Tile events ───────────────────────────────────────────────────────────
    def _on_enter(self, event):
        if self.sel_tile:
            self._dbl(self.sel_tile)
        return "break"

    def _on_tab(self, event):
        if not self._tiles:
            return "break"
        idx = (self._tiles.index(self.sel_tile) + 1) % len(self._tiles) \
              if self.sel_tile in self._tiles else 0
        self._click(self._tiles[idx])
        return "break"

    def _on_shift_tab(self, event):
        if not self._tiles:
            return "break"
        idx = (self._tiles.index(self.sel_tile) - 1) % len(self._tiles) \
              if self.sel_tile in self._tiles else len(self._tiles) - 1
        self._click(self._tiles[idx])
        return "break"

    def _click(self, tile):
        if self.sel_tile and self.sel_tile != tile:
            self.sel_tile.set_selected(False)
        tile.set_selected(True)
        self.sel_tile = tile
        self.sel_path = os.path.join(self.current_path, tile.name)
        self.status_var.set(f"1 item selected  ·  {tile.name}")

    def _dbl(self, tile):
        """Double-click a folder → navigate into it."""
        if tile.IS_DIR:
            self.navigate(os.path.join(self.current_path, tile.name))

    def _open_file(self, tile):
        """Double-click a file → open with default OS app."""
        path = os.path.join(self.current_path, tile.name)
        try:
            if platform.system() == "Darwin":
                subprocess.Popen(["open", path])
            elif platform.system() == "Windows":
                os.startfile(path)
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _rclick(self, tile, event):
        self._click(tile)
        m = tk.Menu(self.root, tearoff=0, font=("Segoe UI", 9),
                    bg=TOPBAR_BG, fg=TEXT_MAIN,
                    activebackground=ITEM_SEL, activeforeground=TEXT_MAIN)
        if tile.IS_DIR:
            m.add_command(label="Open", command=lambda: self._dbl(tile))
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
            messagebox.showinfo("No selection", "Select an item first.")
            return
        old = os.path.basename(self.sel_path)
        new = simpledialog.askstring("Rename", "New name:",
                                     initialvalue=old, parent=self.root)
        if new and new != old:
            try:
                file_ops.rename_item(self.sel_path, new)
                self.sel_tile = None
                self.sel_path = None
                self._refresh()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def delete_item(self):
        if not self.sel_path:
            messagebox.showinfo("No selection", "Select an item first.")
            return
        name = os.path.basename(self.sel_path)
        if messagebox.askyesno("Delete",
                               f"Permanently delete '{name}'?\nThis cannot be undone."):
            try:
                file_ops.delete_item(self.sel_path)
                self.sel_tile = None
                self.sel_path = None
                self._refresh()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    # ── AI gesture queue ──────────────────────────────────────────────────────
    def execute_ai_action(self, gesture_label):
        if gesture_label == "GESTURE_CREATE":
            self.create_file()
        elif gesture_label == "GESTURE_DELETE":
            self.delete_item()
        elif gesture_label == "GESTURE_RENAME":
            self.rename_item()
        elif gesture_label == "GESTURE_OPEN":
            if self.sel_tile:
                self._dbl(self.sel_tile)
        elif gesture_label == "GESTURE_BACK":
            self.go_back()

    def check_ai_queue(self):
        try:
            gesture_label = self.ai_queue.get_nowait()
            self.execute_ai_action(gesture_label)
        except queue.Empty:
            pass
        self.root.after(100, self.check_ai_queue)
