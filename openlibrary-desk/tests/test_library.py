from app.database import connect
from app.library_service import Library
from app import file_service as fs

def make(tmp_path, name, text):
    p = tmp_path / name; p.write_text(text); return p

def test_remove_does_not_delete_file(tmp_path):
    lib = Library(connect(":memory:")); f = make(tmp_path, "a.txt", "hola")
    lib.add(fs.describe(f)); lib.remove(lib.list()[0]["id"])
    assert f.exists() and lib.list() == []

def test_duplicates_by_hash(tmp_path):
    lib = Library(connect(":memory:"))
    assert lib.add(fs.describe(make(tmp_path, "a.txt", "igual")))
    assert not lib.add(fs.describe(make(tmp_path, "b.txt", "igual")))

def test_combined_search(tmp_path):
    lib = Library(connect(":memory:"))
    lib.add(fs.describe(make(tmp_path, "python_basico.md", "1")))
    lib.add(fs.describe(make(tmp_path, "historia.md", "2")))
    assert len(lib.list("python MD Pendiente")) == 1
