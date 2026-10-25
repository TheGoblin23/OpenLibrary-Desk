import hashlib, os, subprocess, sys
from pathlib import Path

BOOKS = {"EPUB", "MOBI", "AZW3"}
SUPPORTED = {"PDF", "EPUB", "MOBI", "AZW3", "TXT", "MD", "DOCX", "ODT", "HTML",
             "CSV", "JSON", "JPG", "PNG", "WEBP", "ZIP", "MP3", "OGG"}

def sha256(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while block := f.read(chunk):
            h.update(block)
    return h.hexdigest()

def describe(path):
    p = Path(path).resolve()
    fmt = p.suffix.lstrip(".").upper()
    return {
        "title": p.stem.replace("_", " ").replace("-", " ").strip() or p.name,
        "file_path": str(p), "format": fmt,
        "material_type": "Libro" if fmt in BOOKS else "Documento",
        "file_hash": sha256(p),
    }

def scan(paths):
    """Expande carpetas y devuelve archivos de formatos admitidos."""
    for raw in paths:
        p = Path(raw)
        files = p.rglob("*") if p.is_dir() else [p]
        for f in files:
            if f.is_file() and f.suffix.lstrip(".").upper() in SUPPORTED:
                yield f

def exists(path):
    return Path(path).exists()

def open_external(path):
    if sys.platform.startswith("win"):
        os.startfile(path)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])
