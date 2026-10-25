from app.database import connect
from app.library_service import Library
from app.ui.main_window import MainWindow

if __name__ == "__main__":
    MainWindow(Library(connect())).mainloop()
