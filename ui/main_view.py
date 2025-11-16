# Principal Class than defines the window of the app and the main structure

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os

class MainView(tk.Tk):
    """
        Main window
    """
    
    def __init__(self, controller):
        super().__init__()
        self.title("Catálogo de Fauna Mexicana 3D")
        self.geometry("1000x650")
        self.controller = controller
        
        # Configuración del estilo de la aplicación
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background='#f7f7f7')
        style.configure('TLabel', background='#f7f7f7')
        style.configure("Gray.TFrame", background="#B6B2B2")

        self. create_widgets()

        
    def create_sidebar():
        pass

    def create_widgets(self):
        main_frame = ttk.Frame(self, style="Gray.TFrame")
        main_frame.pack(
            fill=tk.BOTH, 
            expand=True, 
            padx=10, 
            pady=10
        )

        # Crear Menu Lateral
        menu_lateral_frame = ttk.Frame(
            main_frame,
            relief='solid')
        
        menu_lateral_frame.pack(
            side=tk.LEFT,
            fill=tk.Y,
            padx=(0,10)
        )
        ttk.Label(
            menu_lateral_frame,
            text="Animales",
            font=("arial", 20, "bold")).pack(pady=(0, 10), padx=10
        )

        # Icono Busqueda
        search_frame = ttk.Frame(menu_lateral_frame)
        search_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        path_img = os.path.join(os.getcwd(),'ui','img', 'search.png')
        img_open = Image.open(path_img)
        self.search_icon_image = ImageTk.PhotoImage(img_open)
        search_icon_label = ttk.Label(
                search_frame,
                image=self.search_icon_image
            )
        search_icon_label.pack(side=tk.LEFT, padx=(0, 5))


        # Input busqueda
        search_entry = ttk.Entry(search_frame)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
