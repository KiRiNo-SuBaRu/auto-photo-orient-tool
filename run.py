# run.py
import sys
from image_orient_tool.app import create_app
from image_orient_tool.main_window import MainWindow

def main():
    app, settings = create_app()
    window = MainWindow(settings)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()