import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os

class ScrollableFrame(ttk.Frame):
    """
    Un frame que contiene un canvas y una scrollbar vertical.
    El contenido debe añadirse a 'self.scrollable_frame'.
    """
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        # 1. El Canvas que actuará como "visor"
        self.scroll_canvas = tk.Canvas(
            self, 
            background="#f7f7f7", 
            highlightthickness=0
        )

        # 2. La Scrollbar
        self.scrollbar_y = ttk.Scrollbar(
            self, 
            orient=tk.VERTICAL, 
            command=self.scroll_canvas.yview
        )
        self.scroll_canvas.configure(yscrollcommand=self.scrollbar_y.set)

        # 3. El Frame INTERNO donde irá todo el contenido
        # Este es el frame que el exterior debe usar
        self.scrollable_frame = ttk.Frame(self.scroll_canvas, style='TFrame')

        # 4. Colocar el frame interno dentro del canvas
        self.content_window_id = self.scroll_canvas.create_window(
            (0, 0), 
            window=self.scrollable_frame, 
            anchor="nw"
        )

        # 5. Empaquetar los componentes
        self.scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.scroll_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 6. Binds (conexiones de eventos)
        self.scrollable_frame.bind("<Configure>", self._on_frame_configure)
        self.scroll_canvas.bind("<Configure>", self._on_canvas_configure)
        
        # Bindeos de la rueda del mouse para multi-plataforma
        self._bind_mouse_wheel(self.scroll_canvas)
        self._bind_mouse_wheel(self.scrollable_frame)
        self._bind_mouse_wheel(self) # Bindear el frame principal también

    def _on_frame_configure(self, event):
        """Actualiza la región de scroll del canvas."""
        self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        """Asegura que el frame interno llene el ancho del canvas."""
        canvas_width = event.width
        self.scroll_canvas.itemconfig(self.content_window_id, width=canvas_width)

    def _on_mouse_wheel(self, event):
        """Maneja el evento de la rueda del mouse para el scroll."""
        if event.num == 4 or event.delta > 0:
            self.scroll_canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:
            self.scroll_canvas.yview_scroll(1, "units")

    def _bind_mouse_wheel(self, widget):
        """Aplica los bindeos de la rueda del mouse a un widget."""
        widget.bind("<MouseWheel>", self._on_mouse_wheel) # Windows/macOS
        widget.bind("<Button-4>", self._on_mouse_wheel)   # Linux (scroll up)
        widget.bind("<Button-5>", self._on_mouse_wheel)   # Linux (scroll down)


# --- Componente Reutilizable: AnimalCard ---

class AnimalCard(ttk.Frame):
    """
    Una tarjeta individual que muestra la info de un animal.
    """
    def __init__(self, parent, controller, animal_data, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.controller = controller
        self.animal_data = animal_data
        
        # Almacenamos la imagen como atributo para evitar que sea
        # eliminada por el garbage collector
        self.animal_image = self._load_animal_image()

        self._create_widgets()

    def _load_animal_image(self):
        """Carga y redimensiona la imagen para esta tarjeta."""
        try:
            name_img = self.controller.load_img_name(self.animal_data['id'])
            path_img_animal = os.path.join(os.getcwd(), 'ui', name_img)
            return MainView._load_image(path_img_animal, size=(100, 100))
        except Exception as e:
            print(f"Error cargando imagen {self.animal_data.get('id')}: {e}")
            # Retorna una imagen placeholder o None
            return None 

    def _create_widgets(self):
        """Crea los widgets internos de la tarjeta."""
        animal_button = ttk.Button(
            self, 
            image=self.animal_image
            # Aquí podrías añadir un comando, ej:
            # command=lambda: self.controller.show_animal_details(self.animal_data['id'])
        )
        animal_button.pack(ipadx=5, ipady=5, expand=True)

        nombre_comun = ttk.Label(
            self, 
            text=self.animal_data['nombre_comun']
        )
        nombre_comun.pack()
        
        nombre_cientifico = ttk.Label(
            self, 
            text=self.animal_data['nombre_cientifico']
        )
        nombre_cientifico.pack()


# --- Clase Principal de la Vista ---

class MainView(tk.Tk):
    """
    Ventana principal de la aplicación.
    """
    font_titulos = ("arial", 20, "bold")
    font_estados = ("arial", 16, "bold")

    def __init__(self, controller):
        super().__init__()
        self.title("Catálogo de Fauna Mexicana 3D")
        
        self.controller = controller
        self.attributes('-zoomed', True)
        
        self.search_icon_image = None
        
        self._setup_styles()
        self._setup_layout()

    @staticmethod
    def _load_image(path, size=None):
        """Método auxiliar estático para cargar imágenes."""
        if not os.path.exists(path):
            print(f"Advertencia: No se encontró la imagen en {path}")
            return None
        
        img_open = Image.open(path)
        if size:
            img_open = img_open.resize(size)
        return ImageTk.PhotoImage(img_open)

    def _setup_styles(self):
        """Configura los estilos de la aplicación."""
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background='#f7f7f7')
        style.configure('TLabel', background='#f7f7f7')
        style.configure("Gray.TFrame", background="#B6B2B2")

    def _setup_layout(self):
        """Crea y organiza los widgets principales de la UI."""
        
        # 1. Frame principal gris
        main_frame = ttk.Frame(self, style="Gray.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 2. Crear y empaquetar el Menú Lateral
        self._create_sidebar(main_frame)

        # 3. Crear y empaquetar el Área de Contenido con Scroll
        # Usamos nuestro componente personalizado ScrollableFrame
        scroll_area = ScrollableFrame(main_frame, padding=10)
        scroll_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.content_container = scroll_area.scrollable_frame

        # 4. Poblar el contenido dentro del frame scrollable
        # Nota: Le pasamos 'scroll_area.scrollable_frame', 
        # que es el frame INTERNO del componente.
        self._populate_content(scroll_area.scrollable_frame)

    def _create_sidebar(self, parent):
        """Crea el menú lateral con la barra de búsqueda."""
        menu_lateral_frame = ttk.Frame(parent, relief='solid')
        menu_lateral_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        ttk.Label(
            menu_lateral_frame,
            text="Animales",
            font=self.font_titulos
        ).pack(pady=(0, 10), padx=10)

        # Frame para el icono y la entrada de búsqueda
        search_frame = ttk.Frame(menu_lateral_frame)
        search_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Icono de Búsqueda
        path_img = os.path.join(os.getcwd(), 'ui', 'img', 'search.png')
        self.search_icon_image = self._load_image(path_img) 
        
        search_icon_label = ttk.Label(
            search_frame,
            image=self.search_icon_image
        )
        search_icon_label.pack(side=tk.LEFT, padx=(0, 5))

        # Input de búsqueda
        self.search_entry = ttk.Entry(search_frame)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.search_entry.bind("<KeyRelease>", self._on_search_change)

    def _on_search_change(self, event=None):
        """
        << IMPLEMENTACIÓN ACTUALIZADA >>
        Se llama cada vez que el usuario teclea en la barra de búsqueda.
        Filtra estados Y animales y vuelve a poblar el contenido.
        """
        search_term = self.search_entry.get()
        
        filtered_data = self.controller.get_filtered_data(search_term)
        
        for widget in self.content_container.winfo_children():
            widget.destroy()

        self._populate_content(self.content_container, filtered_data)

    def _populate_content(self, container, data_to_display = None):
            """
            Carga y muestra las tarjetas de animales en el 'container'.
            Si 'data_to_display' es None, carga todos los estados iniciales.
            Si 'data_to_display' es un dict (incluso vacío), usa ese dict.
            """
            
            # Si 'data_to_display' es None
            if data_to_display is None:
                states = self.controller.load_initial_states()
                
                # Construir el diccionario de datos "todo"
                data_to_display = {}
                for state_name in states:
                    data_to_display[state_name] = self.controller.load_animals_by_state(state_name)

            
            for state_name, animals in data_to_display.items():
                
                # No mostrar la sección si un estado no tiene animales
                if not animals:
                    continue
                
                # Título del estado
                ttk.Label(
                    container,
                    text=state_name,
                    anchor='center',
                    font=self.font_titulos
                ).pack(fill='x', padx=10, pady=(10, 5))

                # Contenedor para la fila de tarjetas
                cards_wrapper_frame = ttk.Frame(container)          
                cards_wrapper_frame.pack() 
                
                # Cargar animales y crear tarjetas
                
                for animal in animals:
                    animal_card = AnimalCard(
                        cards_wrapper_frame, 
                        self.controller, 
                        animal
                    )
                    animal_card.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)