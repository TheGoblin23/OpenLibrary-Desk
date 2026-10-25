import queue, threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from app import file_service as fs
from app.library_service import ORDERS

BG, SIDE, CARD, FG, MUTED, ACC = "#1f2026", "#26272e", "#34353f", "#e6e6ee", "#9a9ab0", "#b9a4ff"
TYPES = ("Libro", "Documento", "Estudio")
STATES = ("Pendiente", "Leyendo", "Terminado")
NAV = [("BIBLIOTECA", None), ("Todos", {}), ("Libros", {"type": "Libro"}),
       ("Documentos", {"type": "Documento"}), ("Estudio", {"type": "Estudio"}),
       ("LECTURA", None), ("Pendientes", {"status": "Pendiente"}),
       ("Leyendo", {"status": "Leyendo"}), ("Terminados", {"status": "Terminado"}),
       ("Favoritos", {"favorite": True})]


class EditDialog(tk.Toplevel):
    def __init__(self, parent, row, on_save):
        super().__init__(parent, bg=SIDE)
        self.title("Editar material"); self.transient(parent); self.grab_set()
        self.on_save, self.vars = on_save, {}
        spec = [("title", "Título", None), ("author", "Autor", None), ("category", "Categoría", None),
                ("tags", "Etiquetas (separadas por comas)", None), ("material_type", "Tipo", TYPES),
                ("reading_status", "Estado", STATES), ("progress", "Progreso (%)", None)]
        for i, (k, label, vals) in enumerate(spec):
            tk.Label(self, text=label, bg=SIDE, fg=MUTED).grid(row=i, column=0, sticky="w", padx=12, pady=4)
            v = tk.StringVar(value=str(row[k] if row[k] is not None else ""))
            w = ttk.Combobox(self, textvariable=v, values=vals, state="readonly") if vals \
                else ttk.Entry(self, textvariable=v, width=42)
            w.grid(row=i, column=1, padx=12, pady=4, sticky="ew"); self.vars[k] = v
        tk.Label(self, text="Descripción", bg=SIDE, fg=MUTED).grid(row=7, column=0, sticky="nw", padx=12, pady=4)
        self.desc = tk.Text(self, height=4, width=42, bg=CARD, fg=FG, insertbackground=FG, relief="flat")
        self.desc.insert("1.0", row["description"] or ""); self.desc.grid(row=7, column=1, padx=12, pady=4)
        self.fav = tk.IntVar(value=row["favorite"])
        tk.Checkbutton(self, text="Favorito", variable=self.fav, bg=SIDE, fg=FG, selectcolor=CARD,
                       activebackground=SIDE, activeforeground=FG).grid(row=8, column=1, sticky="w", padx=12)
        bar = tk.Frame(self, bg=SIDE); bar.grid(row=9, column=0, columnspan=2, pady=10)
        ttk.Button(bar, text="Guardar", command=self.save).pack(side="left", padx=6)
        ttk.Button(bar, text="Cancelar", command=self.destroy).pack(side="left", padx=6)

    def save(self):
        data = {k: v.get().strip() for k, v in self.vars.items()}
        if not data["title"]:
            messagebox.showwarning("Falta el título", "Escribí un título para el material.", parent=self); return
        try:
            data["progress"] = max(0, min(100, int(data["progress"] or 0)))
        except ValueError:
            data["progress"] = 0
        if data["reading_status"] == "Terminado":
            data["progress"] = 100
        data["description"] = self.desc.get("1.0", "end").strip()
        data["favorite"] = self.fav.get()
        self.on_save(data); self.destroy()


class MainWindow(tk.Tk):
    def __init__(self, lib):
        super().__init__()
        self.lib, self.filter, self.missing, self._job = lib, {}, set(), None
        self.title("OpenLibrary Desk"); self.geometry("980x600"); self.minsize(720, 420); self.configure(bg=BG)
        self._style(); self._build(); self.refresh()

    def _style(self):
        s = ttk.Style(self); s.theme_use("clam")
        s.configure("Treeview", background=CARD, fieldbackground=CARD, foreground=FG, rowheight=32, borderwidth=0)
        s.configure("Treeview.Heading", background=SIDE, foreground=MUTED, relief="flat", padding=6)
        s.map("Treeview", background=[("selected", "#4a4466")])
        s.configure("TButton", padding=6)

    def _build(self):
        self.columnconfigure(1, weight=1); self.rowconfigure(0, weight=1)
        side = tk.Frame(self, bg=SIDE, width=200); side.grid(row=0, column=0, sticky="ns"); side.grid_propagate(False)
        tk.Label(side, text="OpenLibrary Desk", bg=SIDE, fg=FG, font=("TkDefaultFont", 12, "bold")).pack(anchor="w", padx=14, pady=(16, 0))
        tk.Label(side, text="Tu biblioteca personal", bg=SIDE, fg=MUTED).pack(anchor="w", padx=14, pady=(0, 12))
        self.nav = {}
        for name, flt in NAV:
            if flt is None:
                tk.Label(side, text=name, bg=SIDE, fg=ACC, font=("TkDefaultFont", 9)).pack(anchor="w", padx=14, pady=(14, 2)); continue
            lb = tk.Label(side, text=name, bg=SIDE, fg=FG, anchor="w", padx=14, pady=5, cursor="hand2")
            lb.pack(fill="x"); lb.bind("<Button-1>", lambda e, n=name, f=flt: self.select_nav(n, f)); self.nav[name] = lb
        main = tk.Frame(self, bg=BG); main.grid(row=0, column=1, sticky="nsew", padx=14, pady=14)
        main.columnconfigure(0, weight=1); main.rowconfigure(1, weight=1)
        top = tk.Frame(main, bg=BG); top.grid(row=0, column=0, sticky="ew", pady=(0, 10)); top.columnconfigure(0, weight=1)
        self.q = tk.StringVar(); self.q.trace_add("write", lambda *_: self._debounce())
        e = tk.Entry(top, textvariable=self.q, bg=CARD, fg=FG, insertbackground=FG, relief="flat", font=("TkDefaultFont", 11))
        e.grid(row=0, column=0, sticky="ew", ipady=7, padx=(0, 8))
        self.order = tk.StringVar(value="Agregado")
        cb = ttk.Combobox(top, textvariable=self.order, values=list(ORDERS), state="readonly", width=10)
        cb.grid(row=0, column=1, padx=2); cb.bind("<<ComboboxSelected>>", lambda e: self.refresh())
        ttk.Button(top, text="Añadir archivos", command=self.add_files).grid(row=0, column=2, padx=2)
        ttk.Button(top, text="Importar carpeta", command=self.add_folder).grid(row=0, column=3, padx=2)
        ttk.Button(top, text="Verificar", command=self.verify).grid(row=0, column=4, padx=2)
        cols = ("title", "author", "format", "type", "status", "progress", "fav")
        self.tree = ttk.Treeview(main, columns=cols, show="headings", selectmode="browse")
        for c, t, w in zip(cols, ("Título", "Autor", "Formato", "Tipo", "Estado", "Progreso", "★"), (300, 160, 70, 90, 90, 70, 30)):
            self.tree.heading(c, text=t); self.tree.column(c, width=w, anchor="w" if c in ("title", "author") else "center")
        self.tree.tag_configure("missing", foreground="#e88")
        self.tree.grid(row=1, column=0, sticky="nsew")
        self.status = tk.StringVar(); tk.Label(main, textvariable=self.status, bg=BG, fg=MUTED, anchor="w").grid(row=2, column=0, sticky="ew", pady=(8, 0))
        self.tree.bind("<Double-1>", lambda e: self.open_selected())
        self.tree.bind("<Return>", lambda e: self.open_selected())
        self.tree.bind("<Button-3>", self.menu); self.tree.bind("<Button-2>", self.menu)
        self.select_nav("Todos", {})

    def select_nav(self, name, flt):
        self.filter = flt
        for n, lb in self.nav.items():
            lb.configure(bg=CARD if n == name else SIDE, fg=ACC if n == name else FG)
        self.refresh()

    def _debounce(self):
        if self._job: self.after_cancel(self._job)
        self._job = self.after(200, self.refresh)

    def refresh(self):
        keep = self.selected_id()
        self.tree.delete(*self.tree.get_children())
        rows = self.lib.list(self.q.get(), order=self.order.get(), **self.filter)
        for r in rows:
            self.tree.insert("", "end", iid=str(r["id"]), tags=("missing",) if r["id"] in self.missing else (),
                             values=(r["title"], r["author"], r["format"], r["material_type"], r["reading_status"],
                                     f'{r["progress"]}%', "★" if r["favorite"] else ""))
        if keep and self.tree.exists(str(keep)): self.tree.selection_set(str(keep))
        self.status.set(f"{len(rows)} materiales" + (f" · {len(self.missing)} archivos no encontrados" if self.missing else ""))

    def selected_id(self):
        s = self.tree.selection()
        return int(s[0]) if s else None

    # --- importación (el escaneo y el hash corren fuera del hilo de la interfaz) ---
    def add_files(self):
        paths = filedialog.askopenfilenames(title="Añadir archivos")
        if paths: self._import(paths)

    def add_folder(self):
        d = filedialog.askdirectory(title="Importar carpeta")
        if d: self._import([d])

    def _import(self, paths):
        self.q_in, self.stats = queue.Queue(), {"new": 0, "dup": 0, "err": 0}
        def work():
            for f in fs.scan(paths):
                try: self.q_in.put(fs.describe(f))
                except OSError: self.q_in.put(None)
            self.q_in.put("done")
        threading.Thread(target=work, daemon=True).start()
        self.status.set("Importando…"); self.after(50, self._poll)

    def _poll(self):
        for _ in range(100):
            try: item = self.q_in.get_nowait()
            except queue.Empty: break
            if item == "done":
                self.refresh(); s = self.stats
                self.status.set(f'Importación lista: {s["new"]} nuevos, {s["dup"]} duplicados, {s["err"]} con error'); return
            if item is None: self.stats["err"] += 1
            elif self.lib.add(item): self.stats["new"] += 1
            else: self.stats["dup"] += 1
        self.status.set(f'Importando… {self.stats["new"]} nuevos'); self.after(50, self._poll)

    # --- acciones sobre el elemento seleccionado ---
    def open_selected(self):
        mid = self.selected_id()
        if not mid: return
        row = self.lib.get(mid)
        if not fs.exists(row["file_path"]):
            self.missing.add(mid); self.refresh()
            messagebox.showwarning("Archivo no encontrado", f'No se encuentra:\n{row["file_path"]}'); return
        fs.open_external(row["file_path"]); self.lib.mark_opened(mid)

    def edit_selected(self):
        mid = self.selected_id()
        if mid: EditDialog(self, self.lib.get(mid), lambda d: (self.lib.update(mid, **d), self.refresh()))

    def set_field(self, **kw):
        mid = self.selected_id()
        if mid:
            if kw.get("reading_status") == "Terminado": kw["progress"] = 100
            self.lib.update(mid, **kw); self.refresh()

    def toggle_fav(self):
        mid = self.selected_id()
        if mid: self.set_field(favorite=0 if self.lib.get(mid)["favorite"] else 1)

    def remove_selected(self):
        mid = self.selected_id()
        if mid and messagebox.askyesno("Quitar del catálogo", "Se quitará la ficha del catálogo.\nEl archivo original NO se borrará. ¿Continuar?"):
            self.lib.remove(mid); self.missing.discard(mid); self.refresh()

    def verify(self):
        self.missing = {r["id"] for r in self.lib.list() if not fs.exists(r["file_path"])}; self.refresh()

    def menu(self, event):
        iid = self.tree.identify_row(event.y)
        if not iid: return
        self.tree.selection_set(iid)
        m = tk.Menu(self, tearoff=0)
        m.add_command(label="Abrir", command=self.open_selected)
        m.add_command(label="Editar…", command=self.edit_selected)
        m.add_command(label="Favorito (alternar)", command=self.toggle_fav)
        sub = tk.Menu(m, tearoff=0)
        for st in STATES: sub.add_command(label=st, command=lambda s=st: self.set_field(reading_status=s))
        m.add_cascade(label="Estado", menu=sub); m.add_separator()
        m.add_command(label="Quitar del catálogo", command=self.remove_selected)
        m.tk_popup(event.x_root, event.y_root)
