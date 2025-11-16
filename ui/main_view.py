# Principal Class than defines the window of the app and the main structure

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os




class MainView(tk.Tk):
    """
        Main window
    """
    font_titulos = ("arial", 20, "bold")
    font_estados = ("arial", 16, "bold")

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

        self.create_widgets()

        
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

        # 1. Crear Menu Lateral
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
            font=self.font_titulos).pack(pady=(0, 10), padx=10
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
        
        # centrar el label
        content_frame = ttk.Frame(
            main_frame,
            padding=10
        )
        content_frame.pack(
            side=tk.LEFT, 
            fill=tk.BOTH, 
            expand=True
        )


        states = self.controller.load_initial_states()
        for state_name in states:
            
            titulo_estado = ttk.Label(
                content_frame,
                text=state_name,
                anchor='center',
                font=self.font_titulos
            ).pack(fill='x', padx=10, pady=2)

            animals_row_container = ttk.Frame(
                        content_frame,
                        padding=10
                    )
            animals_row_container.pack(
                        fill=tk.BOTH, 
                        expand=True
                    )

            cards_wrapper_frame = ttk.Frame(animals_row_container)
            
            cards_wrapper_frame.pack() 
            

            animals = self.controller.load_animals_by_state(state_name)
            
            path_img = os.path.join(os.getcwd(), 'ui', 'img', 'search.png')
            download_icon = tk.PhotoImage(file=path_img)

            for animal in animals:
                animal_card_frame = ttk.Frame(cards_wrapper_frame) 
                
                
                animal_card_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

                
                download_button = ttk.Button(
                    animal_card_frame, 
                    image=download_icon
                )
                download_button.pack(
                    ipadx=5,
                    ipady=5,
                    expand=True
                )
                download_button.image = download_icon 

                nombre_comun = ttk.Label(
                    animal_card_frame, 
                    text=animal['nombre_comun']
                )
                nombre_comun.pack()
                
                nombre_cientifico = ttk.Label(
                    animal_card_frame, 
                    text=animal['nombre_cientifico']
                )
                nombre_cientifico.pack()







