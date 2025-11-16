import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os
import numpy as np # Necesario para el panel 3D

# --- Importaciones para 3D ---
try:
    import meshio
except ImportError:
    print("Error: Se requiere la biblioteca 'meshio'.")
    print("Por favor, instálala con: pip install meshio")
    exit()

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk
)
from mpl_toolkits.mplot3d import Axes3D

# --- ---

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
        # Nota: Se corrigió la lógica para que sea más estándar
        delta = 0
        if event.num == 4:
            delta = -1 # Linux scroll up
        elif event.num == 5:
            delta = 1 # Linux scroll down
        elif event.delta > 0:
            delta = -1 # Windows/macOS scroll up
        elif event.delta < 0:
            delta = 1 # Windows/macOS scroll down
            
        if delta != 0:
            self.scroll_canvas.yview_scroll(delta, "units")

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
    # --- MODIFICACIÓN: Recibe 'main_view' en lugar de 'detail_panel' ---
    def __init__(self, parent, controller, animal_data, main_view, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.controller = controller
        self.animal_data = animal_data
        self.main_view = main_view  # <-- Guardar referencia a MainView
        
        self.animal_image = self._load_animal_image()

        self._create_widgets()

    def _load_animal_image(self):
        """Carga y redimensiona la imagen para esta tarjeta."""
        try:
            # Intentar cargar la imagen real
            name_img = self.controller.load_img_name(self.animal_data['id'])
            path_img_animal = os.path.join(os.getcwd(), 'img', name_img)
            return MainView._load_image(path_img_animal, size=(100, 100))
        except Exception as e:
            # Fallback si el controlador o la imagen fallan (para testing)
            print(f"Error cargando imagen real {self.animal_data.get('id')}: {e}")
            try:
                # Intentar cargar imagen de placeholder
                placeholder_path = self.animal_data.get('placeholder_img')
                if placeholder_path and os.path.exists(placeholder_path):
                     return MainView._load_image(placeholder_path, size=(100, 100))
                else:
                    return None
            except Exception as e2:
                print(f"Error cargando imagen placeholder: {e2}")
                return None

    def _create_widgets(self):
        """Crea los widgets internos de la tarjeta."""
        animal_button = ttk.Button(
            self, 
            image=self.animal_image,
            command=self._show_details 
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

    def _show_details(self):
        """
        Se llama al hacer clic en la tarjeta.
        Le dice a la MainView que cambie al panel de detalles.
        """
        print(f"Mostrando detalles para: {self.animal_data['nombre_comun']}")
        # Llamar al método de MainView para cambiar de vista
        self.main_view.show_detail_view(self.animal_data)


# --- Clase Panel Detallado ---
class DetailPanel(ttk.Frame):
    """
    Un Frame de Tkinter que carga y muestra un archivo .obj y otros detalles.
    """
    # --- MODIFICACIÓN: Recibe 'main_view' ---
    def __init__(self, parent, main_view, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.main_view = main_view 
        
        self.figure = None
        self.canvas = None
        self.toolbar = None
        
        # Frame para el modelo 3D
        self.model_frame = ttk.Frame(self, style='TFrame') 
        self.model_frame.pack(fill=tk.BOTH, expand=True)

        # Frame para la información (puedes añadir más aquí)
        self.info_frame = ttk.Frame(self, padding=10, style='TFrame') 
        self.info_frame.pack(fill=tk.X)

        # Boton volver
        self.back_button = ttk.Button(
            self.info_frame, 
            text="< Volver a la lista", 
            command=self.main_view.show_list_view 
        )
        self.back_button.pack(side=tk.LEFT, anchor='nw', padx=5, pady=5)

        # Frame para etiquetas
        self.info_labels_frame = ttk.Frame(self.info_frame, style='TFrame')
        self.info_labels_frame.pack(fill=tk.X, expand=True)

        # --- Etiquetas para la info ---
        self.info_label_common = ttk.Label(self.info_labels_frame, text="", font=("arial", 20, "bold"), style='TLabel', anchor='center')
        self.info_label_common.pack(fill=tk.X, pady=(0,5))
        self.info_label_scientific = ttk.Label(self.info_labels_frame, text="", font=("arial", 16), style='TLabel', anchor='center')
        self.info_label_scientific.pack(fill=tk.X)

        ttk.Label(self.info_labels_frame, text="Descripcion", font=("arial", 20, "bold"), style='TLabel', anchor='center').pack(fill=tk.X)
        self.info_label_description = ttk.Label(self.info_labels_frame, text="", font=("arial", 16), style='TLabel', anchor='center')
        self.info_label_description.pack(fill=tk.X)



    def load_animal_data(self, animal_data):
        """Carga todos los datos del animal en el panel."""
        
        # Actualizar etiquetas de texto
        self.info_label_common.config(text=animal_data.get('nombre_comun', 'N/A'))
        self.info_label_scientific.config(text=animal_data.get('nombre_cientifico', 'N/A'))
        self.info_label_description.config(text=animal_data.get('descripcion', 'N/A'))

        # Cargar modelo 3D
        obj_name = animal_data.get('ruta_modelo_3d') 
        obj_path = os.path.join(os.getcwd(), 'models', obj_name)


        if obj_path and os.path.exists(obj_path):
            self.load_model(obj_path)
        elif obj_path:
            print(f"No se encontró el archivo .obj en la ruta: {obj_path}")
            self.show_error(f"No se encontró: {obj_path}")
        else:
            print(f"No hay archivo .obj definido para {animal_data['nombre_comun']}")
            self.show_error(f"No hay modelo 3D para {animal_data['nombre_comun']}")


    def load_model(self, filepath):
        """
        Carga un modelo .obj y lo muestra en el frame.
        """
        if not os.path.exists(filepath):
            print(f"Error: No se encontró el archivo {filepath}")
            self.show_error(f"No se encontró el archivo: {filepath}")
            return
            
        # 1. Limpiar el frame de widgets anteriores
        self._clear_widgets()

        try:
            # 2. Leer el archivo .obj usando meshio
            mesh = meshio.read(filepath)
            points = mesh.points
            
            if 'triangle' not in mesh.cells_dict:
                if 'quad' in mesh.cells_dict:
                     quads = mesh.cells_dict['quad']
                     tri1 = quads[:, [0, 1, 2]]
                     tri2 = quads[:, [0, 2, 3]]
                     cells = np.vstack([tri1, tri2])
                else:
                    print("Error: No se encontraron 'triangle' o 'quad' en las celdas del mesh.")
                    self.show_error("El modelo .obj no tiene una malla compatible.")
                    return
            else:
                cells = mesh.cells_dict['triangle']

            x, y, z = points[:, 0], points[:, 1], points[:, 2]

            # 3. Crear la figura de Matplotlib
            self.figure = plt.figure(figsize=(5, 4))
            self.figure.patch.set_facecolor('#f7f7f7') 
            
            ax = self.figure.add_subplot(111, projection='3d')
            ax.set_facecolor('#f7f7f7')
            ax.plot_trisurf(x, y, z, triangles=cells, cmap='viridis', edgecolor='none')
            self._auto_scale_axes(ax, x, y, z)

            # 5. Incrustar la figura de Matplotlib en Tkinter
            self.canvas = FigureCanvasTkAgg(self.figure, master=self.model_frame)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

            # 6. Añadir la barra de herramientas de navegación
            self.toolbar = NavigationToolbar2Tk(self.canvas, self.model_frame)
            self.toolbar.update()
            # No empaquetes la barra de herramientas si no la quieres visible
            # self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        except Exception as e:
            print(f"Error cargando el modelo: {e}")
            self.show_error(f"Error al cargar el modelo:\n{e}")

    def show_error(self, message):
        """Muestra un mensaje de error en el panel."""
        self._clear_widgets()
        self.label = ttk.Label(self.model_frame, text=message, foreground="red", style='TLabel') # Aplicar estilo
        self.label.pack(pady=20, padx=20)

    def _clear_widgets(self):
        """Destruye todos los widgets hijos del frame del modelo."""
        for widget in self.model_frame.winfo_children():
            widget.destroy()
        
        # Cerrar la figura de matplotlib para liberar memoria
        if self.figure:
            plt.close(self.figure)
            
        self.figure = None
        self.canvas = None
        self.toolbar = None

    def _auto_scale_axes(self, ax, x, y, z):
        """Ajusta los límites de los ejes para que el modelo no se vea deformado."""
        max_range = np.array([x.max()-x.min(), y.max()-y.min(), z.max()-z.min()]).max() / 2.0
        if max_range == 0: max_range = 1.0 # Evitar división por cero si es un punto

        mid_x = (x.max()+x.min()) * 0.5
        mid_y = (y.max()+y.min()) * 0.5
        mid_z = (z.max()+z.min()) * 0.5
        
        ax.set_xlim(mid_x - max_range, mid_x + max_range)
        ax.set_ylim(mid_y - max_range, mid_y + max_range)
        ax.set_zlim(mid_z - max_range, mid_z + max_range)


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
        self.geometry("1280x720") # Añadido para un tamaño predeterminado
        
        self.search_icon_image = None
        
        self._setup_styles()
        self._setup_layout()

    @staticmethod
    def _load_image(path, size=None):
        """Método auxiliar estático para cargar imágenes."""
        if not os.path.exists(path):
            print(f"Advertencia: No se encontró la imagen en {path}")
            return None
        
        try:
            img_open = Image.open(path)
            if size:
                # Usar Resampling.LANCZOS para mejor calidad de redimensionado
                img_open = img_open.resize(size, Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(img_open)
        except Exception as e:
            print(f"Error abriendo la imagen {path}: {e}")
            return None

    def _setup_styles(self):
        """Configura los estilos de la aplicación."""
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background='#f7f7f7')
        style.configure('TLabel', background='#f7f7f7')
        style.configure("Gray.TFrame", background="#B6B2B2")

    # --- MODIFICACIÓN: _setup_layout ---
    def _setup_layout(self):
        """Crea y organiza los widgets principales de la UI."""
        
        # 1. Frame principal gris
        main_frame = ttk.Frame(self, style="Gray.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Configurar columnas para el layout: [Sidebar] [Content]
        main_frame.columnconfigure(0, weight=1) # Sidebar (angosta)
        main_frame.columnconfigure(1, weight=3) # Content Area (ancha)
        main_frame.rowconfigure(0, weight=1)

        # 2. Crear y empaquetar el Menú Lateral
        sidebar_frame = self._create_sidebar(main_frame) 
        sidebar_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # 3. Contenedor de vistas
        self.content_area = ttk.Frame(main_frame, style='TFrame')
        self.content_area.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        self.content_area.grid_rowconfigure(0, weight=1)
        self.content_area.grid_columnconfigure(0, weight=1)

        # 4. Crear AMBAS vistas (lista y detalle) dentro del content_area
        self.scroll_area = ScrollableFrame(self.content_area, padding=10)
        self.scroll_area.grid(row=0, column=0, sticky="nsew")
        
        # Pasar 'self' (MainView) al DetailPanel
        self.detail_view = DetailPanel(self.content_area, self, style='TFrame') 
        self.detail_view.grid(row=0, column=0, sticky="nsew")
        
        # 5. Guardar referencia al container de la lista
        self.content_container = self.scroll_area.scrollable_frame
        
        # 6. Poblar el contenido
        self._populate_content(self.content_container)
        
        # 7. Mostrar la vista de lista al inicio
        self.show_list_view()

    def _create_sidebar(self, parent):
        """
        Crea el menú lateral (SOLO con la búsqueda).
        """
        menu_lateral_frame = ttk.Frame(parent, relief='solid', style='TFrame')
        
        # --- Título ---
        ttk.Label(
            menu_lateral_frame,
            text="Animales",
            font=self.font_titulos
        ).pack(pady=(0, 10), padx=10)

        # --- Barra de Búsqueda ---
        search_frame = ttk.Frame(menu_lateral_frame, style='TFrame')
        search_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        try:
            path_img = os.path.join(os.getcwd(), 'ui', 'img', 'search.png')
            self.search_icon_image = self._load_image(path_img, size=(20, 20))
        except Exception as e:
            print(f"No se pudo cargar el icono de búsqueda: {e}")
            self.search_icon_image = None
        
        search_icon_label = ttk.Label(
            search_frame,
            image=self.search_icon_image,
            style='TLabel'
        )
        search_icon_label.pack(side=tk.LEFT, padx=(0, 5))

        self.search_entry = ttk.Entry(search_frame)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.search_entry.bind("<KeyRelease>", self._on_search_change)
        
        # El ScrollableFrame YA NO se crea aquí
        
        return menu_lateral_frame

    def _on_search_change(self, event=None):
        """
        Se llama cada vez que el usuario teclea en la barra de búsqueda.
        Filtra estados Y animales y vuelve a poblar el contenido.
        """
        search_term = self.search_entry.get()
        
        # Asegurarse de que el controlador existe
        if not self.controller:
            print("Controlador no inicializado.")
            return
            
        filtered_data = self.controller.get_filtered_data(search_term)
        
        for widget in self.content_container.winfo_children():
            widget.destroy()

        self._populate_content(self.content_container, filtered_data)
        
        self.show_list_view()

    def _populate_content(self, container, data_to_display = None):
        """
        Carga y muestra las tarjetas de animales en el 'container'.
        """
        if not self.controller:
             print("Controlador no inicializado.")
             return
             
        if data_to_display is None:
            try:
                states = self.controller.load_initial_states()
                data_to_display = {}
                for state_name in states:
                    data_to_display[state_name] = self.controller.load_animals_by_state(state_name)
            except Exception as e:
                print(f"Error cargando datos iniciales: {e}")
                ttk.Label(container, text=f"Error cargando datos: {e}").pack()
                return

        if not data_to_display:
            ttk.Label(container, text="No se encontraron animales.").pack()
            return
            
        for state_name, animals in data_to_display.items():
            
            if not animals:
                continue
            
            ttk.Label(
                container,
                text=state_name,
                anchor='center',
                font=self.font_titulos
            ).pack(fill='x', padx=10, pady=(10, 5))

            # Contenedor para la fila de tarjetas
            cards_wrapper_frame = ttk.Frame(container, style='TFrame')          
            cards_wrapper_frame.pack() 
            
            for animal in animals:
                animal_card = AnimalCard(
                    cards_wrapper_frame, 
                    self.controller, 
                    animal,
                    self  
                )
                animal_card.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
    
    def show_detail_view(self, animal_data):
        """Oculta la lista y muestra el panel de detalles."""
        self.scroll_area.grid_remove() # Ocultar lista
        self.detail_view.grid() # Mostrar detalles
        self.detail_view.load_animal_data(animal_data) # Cargar datos

    def show_list_view(self):
        """Oculta el panel de detalles y muestra la lista."""
        self.detail_view.grid_remove() # Ocultar detalles
        self.scroll_area.grid() # Mostrar lista