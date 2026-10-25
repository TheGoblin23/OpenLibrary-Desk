from datetime import datetime

ORDERS = {"Agregado": "added_at DESC", "Título": "title COLLATE NOCASE",
          "Autor": "author COLLATE NOCASE", "Último uso": "last_opened_at DESC"}
COLUMNS = {"title", "author", "description", "category", "tags", "material_type",
           "reading_status", "progress", "favorite", "file_path", "format", "file_hash"}
SEARCH_COLS = ("title", "author", "description", "tags", "category", "format", "reading_status")

def _now():
    return datetime.now().isoformat(timespec="seconds")

class Library:
    def __init__(self, con):
        self.con = con

    def add(self, data):
        """Devuelve False si el archivo ya está (misma ruta o mismo contenido)."""
        q, a = "SELECT 1 FROM materials WHERE file_path=?", [data.get("file_path")]
        if data.get("file_hash"):
            q += " OR file_hash=?"; a.append(data["file_hash"])
        if self.con.execute(q, a).fetchone():
            return False
        d = {k: v for k, v in data.items() if k in COLUMNS}
        d["added_at"] = _now()
        self.con.execute(f"INSERT INTO materials({', '.join(d)}) VALUES({', '.join('?' * len(d))})", list(d.values()))
        self.con.commit()
        return True

    def update(self, mid, **kw):
        kw = {k: v for k, v in kw.items() if k in COLUMNS}
        self.con.execute(f"UPDATE materials SET {', '.join(k + '=?' for k in kw)} WHERE id=?", [*kw.values(), mid])
        self.con.commit()

    def remove(self, mid):
        """Quita el registro del catálogo. Nunca toca el archivo original."""
        self.con.execute("DELETE FROM materials WHERE id=?", (mid,))
        self.con.commit()

    def mark_opened(self, mid):
        self.con.execute("UPDATE materials SET last_opened_at=? WHERE id=?", (_now(), mid))
        self.con.commit()

    def get(self, mid):
        return self.con.execute("SELECT * FROM materials WHERE id=?", (mid,)).fetchone()

    def list(self, search="", type=None, status=None, favorite=False, order="Agregado"):
        sql, args = "SELECT * FROM materials WHERE 1=1", []
        for term in search.split():
            sql += " AND (" + " OR ".join(f"{c} LIKE ?" for c in SEARCH_COLS) + ")"
            args += [f"%{term}%"] * len(SEARCH_COLS)
        if type:
            sql += " AND material_type=?"; args.append(type)
        if status:
            sql += " AND reading_status=?"; args.append(status)
        if favorite:
            sql += " AND favorite=1"
        sql += " ORDER BY " + ORDERS.get(order, ORDERS["Agregado"])
        return self.con.execute(sql, args).fetchall()
