import tkinter as tk
from src.gui import TTSApp
from dotenv import load_dotenv
import os

def main():
    # Load environment variables from .env if it exists
    load_dotenv()
    
    root = tk.Tk()
    app = TTSApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
