import sqlite3
import os

DB_FILE = os.path.join(os.getcwd(), 'data', 'animales.db')


# Datos (versión corta de tu mock)
LISTA_ESTADOS = [
    "Aguascalientes", "Baja California", "Baja California Sur", "Campeche",
    "Chiapas", "Chihuahua", "Ciudad de México", "Coahuila",
    "Colima", "Durango", "Guanajuato", "Guerrero",
    "Hidalgo", "Jalisco", "México", "Michoacán",
    "Morelos", "Nayarit", "Nuevo León", "Oaxaca",
    "Puebla", "Querétaro", "Quintana Roo", "San Luis Potosí",
    "Sinaloa", "Sonora", "Tabasco", "Tamaulipas",
    "Tlaxcala", "Veracruz", "Yucatán", "Zacatecas"
]

# Descripción larga de marcador de posición
descripcion_larga = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
    "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. "
    "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. "
    "Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. "
    "Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."
)

# --- INICIO DEL SCRIPT ---

# Borrar la base de datos antigua si existe, para empezar de cero
if os.path.exists(DB_FILE):
    os.remove(DB_FILE)
    print("Base de datos anterior eliminada.")

# Conectar (creará el archivo 'animales.db')
try:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    print("Conexión a la base de datos establecida.")

    # --- 1. Crear Tablas ---
    
    # Crear tabla de estados
    cursor.execute('''
    CREATE TABLE estados (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL UNIQUE
    )
    ''')
    print("Tabla 'estados' creada.")

    # Crear tabla de animales
    cursor.execute('''
    CREATE TABLE animales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_comun TEXT NOT NULL,
        nombre_cientifico TEXT,
        descripcion TEXT,
        ruta_modelo_3d TEXT,
        ruta_img TEXT,
        estado_id INTEGER NOT NULL,
        FOREIGN KEY (estado_id) REFERENCES estados(id)
    )
    ''')
    print("Tabla 'animales' creada.")

    # --- 2. Insertar Estados ---
    
    # Guardamos los estados en una lista de tuplas para 'executemany'
    estados_para_insertar = [(estado,) for estado in LISTA_ESTADOS]
    
    # 'executemany' es mucho más rápido para insertar lotes
    cursor.executemany("INSERT INTO estados (nombre) VALUES (?)", estados_para_insertar)
    print(f"Insertados {len(LISTA_ESTADOS)} estados.")

    # --- 3. Insertar Animales (Simulados) ---
    
    #print("Insertando animales (5 por estado)...")
    #animales_para_insertar = []
    
    # Para la simulación, volvemos a consultar los estados para obtener sus IDs
    #cursor.execute("SELECT id, nombre FROM estados")
    #estados_con_id = cursor.fetchall() # Lista de tuplas (id, nombre)
    
    #animal_id_counter = 1
    #for estado_id, estado_nombre in estados_con_id:
    #    for i in range(5): # 5 animales por estado
    #        nombre_comun = f"Animal de {estado_nombre} #{i+1}"
    #        nombre_cientifico = f"Genus species {animal_id_counter}"
    #        
    #        # (nombre_comun, nombre_cientifico, descripcion, modelo, img, estado_id)
    #        animal_tupla = (
    #            nombre_comun,
    #            nombre_cientifico,
    #            f"Descripción para {nombre_comun}. {descripcion_larga}",
    #            f'null.obj',
    #            f'null.jpg',
    #            estado_id  # Usamos el ID del estado
    #        )
    #        animales_para_insertar.append(animal_tupla)
    #        animal_id_counter += 1

    # Insertar todos los animales de golpe
    #cursor.executemany('''
    #    INSERT INTO animales 
    #    (nombre_comun, nombre_cientifico, descripcion, ruta_modelo_3d, ruta_img, estado_id) 
    #    VALUES (?, ?, ?, ?, ?, ?)
    #''', animales_para_insertar)

    #print(f"Insertados {len(animales_para_insertar)} animales.")

    # --- 4. Guardar y Cerrar ---
    conn.commit()
    print("¡Base de datos creada y poblada con éxito!")

except sqlite3.Error as e:
    print(f"Error de SQLite: {e}")
finally:
    if conn:
        conn.close()

if __name__ == '__main__':
    print("Ejecutando script para crear la base de datos...")
    # (Este script se ejecuta directamente desde la terminal: python crear_db.py)