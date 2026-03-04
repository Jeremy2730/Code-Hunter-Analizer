import sys

from .gui.app import CodeHunterApp
from .main_cli import main as cli_main

def main():
    if "--gui" in sys.argv:
        app = CodeHunterApp()
        app.mainloop()
    else:
        cli_main()

if __name__ == "__main__":
    main()