import sqlite3
import os
DB_PATH = os.path.join(os.getcwd(), 'data', 'animales.db')
# Función útil para convertir los resultados de SQLite (tuplas)
# en diccionarios, que es lo que tu vista espera.
def _dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

class AppController:
    def __init__(self, db_path=DB_PATH):
        # Conectar a la base de datos
        # 'check_same_thread=False' es importante para tkinter
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        
        # Configurar la conexión para que devuelva diccionarios
        self.conn.row_factory = _dict_factory
        print(f"Controlador conectado a {db_path}")

    def load_initial_states(self):
        """
        Carga la lista de nombres de estados desde la DB.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT nombre FROM estados ORDER BY nombre ASC")
            # Extraer solo el nombre de cada diccionario
            states = [row['nombre'] for row in cursor.fetchall()]
            return states
        except sqlite3.Error as e:
            print(f"Error al cargar estados: {e}")
            return []

    def load_animals_by_state(self, state_name):
        """
        Devuelve la lista de animales para un estado específico.
        """
        try:
            cursor = self.conn.cursor()
            # 1. Encontrar el ID del estado
            cursor.execute("SELECT id FROM estados WHERE nombre = ?", (state_name,))
            estado_row = cursor.fetchone()
            
            if not estado_row:
                print(f"Estado no encontrado: {state_name}")
                return []
            
            estado_id = estado_row['id']
            
            # 2. Obtener los animales de ESE estado
            # Añadimos 'estado' al SELECT para que el diccionario lo incluya
            cursor.execute("""
                SELECT a.*, e.nombre as estado 
                FROM animales a
                JOIN estados e ON a.estado_id = e.id
                WHERE a.estado_id = ?
                ORDER BY a.nombre_comun
            """, (estado_id,))
            
            animals = cursor.fetchall()
            return animals
        except sqlite3.Error as e:
            print(f"Error al cargar animales: {e}")
            return []
            
    def get_filtered_data(self, search_term):
        """
        Filtra estados y animales basado en un término de búsqueda,
        directamente en la base de datos.
        """
        search_term_lower = search_term.lower().strip()
        
        if not search_term_lower:
            # Si no hay búsqueda, llamamos a la lógica original (o una versión optimizada)
            # Por simplicidad, devolvemos todo agrupado
            all_data = {}
            for state in self.load_initial_states():
                all_data[state] = self.load_animals_by_state(state)
            return all_data

        # Preparamos el término de búsqueda para SQL (con comodines '%')
        query_term = f"%{search_term_lower}%"

        try:
            cursor = self.conn.cursor()
            # Esta es la consulta mágica de SQL.
            # Busca el término en el nombre del animal, el nombre científico
            # O el nombre del estado al que pertenece.
            cursor.execute("""
                SELECT a.*, e.nombre as estado
                FROM animales a
                JOIN estados e ON a.estado_id = e.id
                WHERE 
                    LOWER(a.nombre_comun) LIKE ? OR
                    LOWER(a.nombre_cientifico) LIKE ? OR
                    LOWER(e.nombre) LIKE ?
                ORDER BY e.nombre, a.nombre_comun
            """, (query_term, query_term, query_term))
            
            results = cursor.fetchall() # Lista de todos los animales que coinciden
            
            # Ahora agrupamos los resultados por estado (como espera tu vista)
            filtered_data = {}
            for animal in results:
                state_name = animal['estado']
                if state_name not in filtered_data:
                    filtered_data[state_name] = []
                filtered_data[state_name].append(animal)
                
            return filtered_data
            
        except sqlite3.Error as e:
            print(f"Error al filtrar datos: {e}")
            return {}

    def load_img_name(self, animal_id):
        """
        Obtiene una sola ruta de imagen por ID.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT ruta_img FROM animales WHERE id = ?", (animal_id,))
            result = cursor.fetchone()
            return result['ruta_img'] if result else None
        except sqlite3.Error as e:
            print(f"Error al cargar imagen: {e}")
            return None

    def display_animal_details(self, animal_data):
        """
        El controlador le pasa los datos a la vista.
        (Esta función es llamada por la VISTA, y le dice a la VISTA
        que se actualice, por lo que el nombre es un poco confuso)
        """
        # En tu AppController real, esta lógica estaría en la vista
        # o el controlador llamaría a un método de la vista.
        print(f"Controlador: 'VISTA, muestra detalles para {animal_data['nombre_comun']}'")
        if hasattr(self, 'view'):
             self.view.display_detail(animal_data)
        else:
             print("Advertencia: El controlador no tiene referencia a la vista (self.view).")

    def set_view(self, view):
        self.view = view