import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os
import numpy as np # Necesario para el panel 3D
import pyvista as pv

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
            path_img_animal = os.path.join(os.getcwd(), name_img)
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
    Panel que utiliza PyVista (VTK) para manejar modelos de Alta Resolución con Texturas PBR.
    """
    def __init__(self, parent, main_view, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.main_view = main_view 
        self.current_mesh = None 
        self.texture_paths = {} # Diccionario para guardar las texturas cargadas
        
        # --- Layout Principal (Igual que antes) ---
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # 1. Header
        self.info_frame = ttk.Frame(self, padding=10, style='TFrame') 
        self.info_frame.grid(row=0, column=0, sticky="ew")

        self.back_button = ttk.Button(self.info_frame, text="< Volver a la lista", command=self.main_view.show_list_view)
        self.back_button.pack(side=tk.LEFT, anchor='nw')

        self.info_labels_frame = ttk.Frame(self.info_frame, style='TFrame')
        self.info_labels_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=20)

        self.lbl_comun = ttk.Label(self.info_labels_frame, text="", font=("arial", 18, "bold"), style='TLabel')
        self.lbl_comun.pack(anchor='w')
        self.lbl_cientifico = ttk.Label(self.info_labels_frame, text="", font=("arial", 12, "italic"), style='TLabel')
        self.lbl_cientifico.pack(anchor='w')

        # 2. Área de Visualización
        self.viz_frame = ttk.Frame(self, style='Gray.TFrame')
        self.viz_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.viz_frame.columnconfigure(0, weight=1)
        self.viz_frame.rowconfigure(0, weight=1)

        self.preview_label = ttk.Label(self.viz_frame, text="Cargando...", anchor="center", style='TLabel')
        self.preview_label.grid(row=0, column=0, sticky="nsew", padx=1, pady=1)

        # 3. Botón Interactivo
        self.btn_open_3d = ttk.Button(
            self.viz_frame, 
            text="ABRIR VISOR 3D", 
            command=self.open_interactive_viewer,
            state="disabled"
        )
        self.btn_open_3d.grid(row=1, column=0, sticky="ew", padx=10, pady=10)

        # 4. Descripción
        self.desc_frame = ttk.Frame(self, padding=10, style='TFrame')
        self.desc_frame.grid(row=2, column=0, sticky="ew")
        
        # Aumenté el título a tamaño 16
        ttk.Label(
            self.desc_frame, 
            text="Descripción:", 
            font=("arial", 16, "bold"), 
            style='TLabel'
        ).pack(anchor='w')
        
        # Aumenté el texto del cuerpo a tamaño 14
        self.lbl_desc = ttk.Label(
            self.desc_frame, 
            text="", 
            wraplength=1000, # Aumenté un poco el ancho de envoltura para que aproveche el espacio
            font=("arial", 14), # <--- AQUÍ ESTÁ EL CAMBIO IMPORTANTE
            style='TLabel'
        )
        self.lbl_desc.pack(fill=tk.X)

    def load_animal_data(self, animal_data):
        # Resetear UI
        self.lbl_comun.config(text=animal_data.get('nombre_comun', 'N/A'))
        self.lbl_cientifico.config(text=animal_data.get('nombre_cientifico', 'N/A'))
        self.lbl_desc.config(text=animal_data.get('descripcion', 'N/A'))
        self.preview_label.config(image='', text="Cargando vista previa...")
        self.btn_open_3d.config(state="disabled")
        self.current_mesh = None
        self.texture_paths = {} # Limpiar texturas anteriores

        obj_name = animal_data.get('ruta_modelo_3d') 
        if not obj_name:
            self.preview_label.config(text="No hay modelo 3D asignado.")
            return

        obj_path = os.path.join(os.getcwd(), obj_name)
        if not os.path.exists(obj_path):
            self.preview_label.config(text=f"Archivo no encontrado: {obj_name}")
            return

        # Cargar asíncronamente
        self.after(50, lambda: self._load_pyvista_mesh(obj_path))

    def _get_textures_from_folder(self, obj_path):
        """
        Busca automáticamente texturas en la misma carpeta del OBJ.
        Asume que las texturas contienen palabras clave como 'base', 'metallic', etc.
        """
        folder = os.path.dirname(obj_path)
        textures = {
            "base": None,
            "metallic": None,
            "roughness": None,
            "normal": None
        }
        
        # Escanear archivos en la carpeta
        try:
            for file in os.listdir(folder):
                full_path = os.path.join(folder, file)
                if not os.path.isfile(full_path): continue
                
                filename_lower = file.lower()
                
                # Lógica simple de detección por nombre
                # Ajusta estas palabras clave según tus nombres de archivo reales
                if "base" in filename_lower or "color" in filename_lower or "diffuse" in filename_lower:
                    textures["base"] = pv.read_texture(full_path)
                elif "metallic" in filename_lower or "metal" in filename_lower:
                    textures["metallic"] = pv.read_texture(full_path)
                elif "roughness" in filename_lower or "rough" in filename_lower:
                    textures["roughness"] = pv.read_texture(full_path)
                elif "normal" in filename_lower:
                    textures["normal"] = pv.read_texture(full_path)
        except Exception as e:
            print(f"Advertencia buscando texturas: {e}")
            
        return textures

    def _load_pyvista_mesh(self, obj_path):
        try:
            self.current_mesh = pv.read(obj_path)
            
            # Cargar texturas
            self.loaded_textures = self._get_textures_from_folder(obj_path)
            
            # Crear captura de pantalla (Preview simple, solo color base)
            plotter = pv.Plotter(off_screen=True, window_size=[600, 400])
            plotter.set_background("#f7f7f7")
            
            # Para la preview estática, usamos solo el color base si existe, o blanco por defecto
            if self.loaded_textures["base"]:
                plotter.add_mesh(self.current_mesh, texture=self.loaded_textures["base"])
            else:
                plotter.add_mesh(self.current_mesh, color="white")
                
            plotter.view_isometric()
            
            img_array = plotter.screenshot(None, return_img=True)
            plotter.close()

            image = Image.fromarray(img_array)
            self.photo = ImageTk.PhotoImage(image)

            self.preview_label.config(image=self.photo, text="")
            self.btn_open_3d.config(state="normal")
            print(f"Modelo cargado: {self.current_mesh.n_points} vértices.")

        except Exception as e:
            print(f"Error PyVista: {e}")
            self.preview_label.config(text=f"Error cargando modelo:\n{e}")

    def open_interactive_viewer(self):
        print("--- Intentando abrir visor 3D ---")
        if not self.current_mesh:
            return

        try:
            p = pv.Plotter()
            p.add_text("Presiona 'q' para cerrar", font_size=12)
            
            # Detectar si tenemos texturas PBR
            use_pbr = False
            if self.loaded_textures.get("metallic") or self.loaded_textures.get("roughness"):
                use_pbr = True

            # Intentamos añadir la malla con argumentos PBR
            try:
                p.add_mesh(
                    self.current_mesh,
                    texture=self.loaded_textures.get("base"),
                    metallic_texture=self.loaded_textures.get("metallic"),
                    roughness_texture=self.loaded_textures.get("roughness"),
                    normal_texture=self.loaded_textures.get("normal"),
                    pbr=use_pbr,
                    # Fallbacks numéricos por si faltan texturas pero activamos PBR
                    metallic=1.0 if (use_pbr and not self.loaded_textures.get("metallic")) else None,
                    roughness=0.5 if (use_pbr and not self.loaded_textures.get("roughness")) else None
                )
                # Si pasa esta línea, PBR funciona. Añadimos luz para que se vea bien.
                if use_pbr:
                     p.add_light(pv.Light(position=(10, 10, 10), intensity=0.8))

            except TypeError:
                # --- BLOQUE DE SEGURIDAD PARA VERSIONES ANTIGUAS ---
                print("ADVERTENCIA: Tu versión de PyVista no soporta PBR. Cargando modo simple.")
                p.clear() # Limpiamos por si acaso
                #p.add_text("Modo Compatibilidad (Sin PBR)", font_size=10, position='upper_left')
                
                # Carga estándar (Solo textura base o color blanco)
                if self.loaded_textures.get("base"):
                    p.add_mesh(self.current_mesh, texture=self.loaded_textures.get("base"))
                else:
                    p.add_mesh(self.current_mesh, color="white")

            p.show()

        except Exception as e:
            print(f"ERROR CRÍTICO: {e}")
            import traceback
            traceback.print_exc()


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