import sqlite3
import os

nuevos_animales = []
DB_FILE = os.path.join(os.getcwd(), 'data', 'animales.db')

def validar_lista_animales(lista_animales, set_estados_db, set_animales_db):
    """
    Valida una lista de diccionarios de animales antes de la inserción.
    
    Comprueba:
    1. Campos requeridos.
    2. Existencia del estado en la DB.
    3. Duplicados de 'nombre_comun' en la DB.
    4. Existencia de los archivos de imagen y modelo.
    
    Retorna (animales_validos, errores)
    """
    animales_validos = []
    errores = []
    campos_requeridos = {'nombre_comun', 'nombre_cientifico', 'descripcion', 
                         'ruta_modelo_3d', 'ruta_img', 'estado_nombre'}

    for i, animal in enumerate(lista_animales):
        es_valido = True
        id_animal_str = f"Animal #{i+1} ('{animal.get('nombre_comun', 'NOMBRE_FALTANTE')}')"

        campos_no_vacios = set(animal.keys())
        for key in campos_no_vacios:
            if animal[key].strip == '':
                errores.append(f"  [ERROR] {id_animal_str}: El campo '{key}' está presente pero no puede estar vacío.")
                es_valido = False

        # 1. Validar campos requeridos
        campos_faltantes = campos_requeridos - set(animal.keys())
        if campos_faltantes:
            errores.append(f"  [ERROR] {id_animal_str}: Faltan campos: {', '.join(campos_faltantes)}")
            es_valido = False
            continue # No se pueden hacer más validaciones si faltan claves
        

        # 2. Validar existencia de estado
        if animal['estado_nombre'] not in set_estados_db:
            errores.append(f"  [ERROR] {id_animal_str}: El estado '{animal['estado_nombre']}' no existe en la base de datos.")
            es_valido = False
            
        # 3. Validar duplicado de animal
        if animal['nombre_comun'] in set_animales_db:
            errores.append(f"  [ERROR] {id_animal_str}: El animal '{animal['nombre_comun']}' ya existe en la base de datos.")
            es_valido = False

        # 4. Validar existencia de archivos
        # Asume que las rutas son relativas al directorio principal (donde corres el script)
        ruta_img_completa = os.path.join(os.getcwd(), animal['ruta_img'])
        if not os.path.exists(ruta_img_completa):
            errores.append(f"  [ERROR] {id_animal_str}: No se encontró el archivo de imagen: {animal['ruta_img']}")
            es_valido = False
            
        ruta_modelo_completa = os.path.join(os.getcwd(), animal['ruta_modelo_3d'])
        if not os.path.exists(ruta_modelo_completa):
            errores.append(f"  [ERROR] {id_animal_str}: No se encontró el archivo de modelo 3D: {animal['ruta_modelo_3d']}")
            es_valido = False


        if es_valido:
            animales_validos.append(animal)
            
    return animales_validos, errores


def agregar_animales_a_db():
    """
    Se conecta a la base de datos, valida la lista de 'nuevos_animales'
    y añade solo los que son válidos.
    """
    
    if not os.path.exists(DB_FILE):
        print(f"Error: No se encontró la base de datos '{DB_FILE}'.")
        print("Asegúrate de ejecutar 'main.py' o 'crear_db.py' primero.")
        return

    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        print(f"Conectado a '{DB_FILE}'.")

        # --- 1. OBTENER DATOS PARA VALIDACIÓN ---
        print("Cargando datos existentes para validación...")
        
        # Obtener todos los nombres de estados
        cursor.execute("SELECT nombre FROM estados")
        set_estados_db = {row[0] for row in cursor.fetchall()}
        
        # Obtener todos los nombres de animales
        cursor.execute("SELECT nombre_comun FROM animales")
        set_animales_db = {row[0] for row in cursor.fetchall()}
        
        # Obtener un mapa de nombre_estado -> id_estado
        cursor.execute("SELECT nombre, id FROM estados")
        mapa_estados_id = {row[0]: row[1] for row in cursor.fetchall()}

        # --- 2. VALIDAR ---
        print(f"\nValidando {len(nuevos_animales)} animales de la lista...")
        animales_para_insertar, errores = validar_lista_animales(
            nuevos_animales, set_estados_db, set_animales_db
        )

        # --- 3. REPORTAR ERRORES ---
        if errores:
            print(f"\nSe encontraron {len(errores)} problemas. Estos animales NO se agregarán:")
            for error in errores:
                print(error)
        else:
            print("¡Todas las validaciones pasaron!")

        if not animales_para_insertar:
            print("\nNo hay animales válidos para agregar. Terminando.")
            return

        # --- 4. INSERTAR ANIMALES VÁLIDOS ---
        print(f"\nInsertando {len(animales_para_insertar)} animales válidos...")
        total_agregados = 0
        
        for animal in animales_para_insertar:
            try:
                # El estado_id ya fue validado, así que lo podemos tomar con seguridad
                estado_id = mapa_estados_id[animal["estado_nombre"]]

                cursor.execute("""
                    INSERT INTO animales 
                    (nombre_comun, nombre_cientifico, descripcion, ruta_modelo_3d, ruta_img, estado_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    animal["nombre_comun"],
                    animal["nombre_cientifico"],
                    animal["descripcion"],
                    animal["ruta_modelo_3d"],
                    animal["ruta_img"],
                    estado_id
                ))
                print(f"  Éxito: Se agregó '{animal['nombre_comun']}' a la base de datos.")
                total_agregados += 1
            
            except sqlite3.Error as e:
                # Captura por si acaso, aunque la validación debería prevenir la mayoría
                print(f"  Error de SQLite al insertar '{animal['nombre_comun']}': {e}")
        
        # 5. Guardar cambios (commit) y cerrar
        if total_agregados > 0:
            conn.commit()
            print(f"\n¡Operación completada! Se guardaron {total_agregados} nuevos animales.")
        else:
            print("\nOperación completada. No se agregó ningún animal nuevo.")
            
    except sqlite3.Error as e:
        print(f"Error fatal al conectar con la base de datos: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':

# --- INSTRUCCIONES DE USO ---
#
# 1. PREPARA TUS ARCHIVOS:
#    - Modelo 3D: Coloca tu archivo .obj en la carpeta /models/ (ej. /models/mi_animal.obj)
#    - Imagen: Coloca tu archivo .jpg o .png en la carpeta /img/ (ej. /img/mi_animal.jpg)
#
# 2. EDITA ESTA LISTA:
#    - Añade un nuevo diccionario a la lista 'nuevos_animales' (abajo).
#    - 'nombre_modelo_3d': Debe ser solo el nombre del archivo con .obj
#    - 'ruta_img': Debe ser solo el nombre del archivo y DEBE SER PNG.
#    - 'estado_nombre': Debe ser el nombre exacto de un estado en la DB (Estado empezando por mayuscula).
# 3. EJECUTA EL SCRIPT:
#    - Guarda este archivo.
#    - En tu terminal, corre: python agregar_animal.py
#    - El script validará tus datos. Si todo es correcto, los añadirá.
# 4. NO HACER COMMIT NI PUSH DE ESTE ARCHIVO 
#   - Para no dar conflictos en el futuro solo editar el input de datos.
# --- FIN DE INSTRUCCIONES ---

    nombre_comun = ' '
    nombre_cientifico = ' '
    descripcion = ' '
    nombre_modelo_3d = ' '
    nombre_img = ' '
    estado = ' '

    nuevos_animales = [
        {
        
        "nombre_comun": nombre_comun,
        "nombre_cientifico": nombre_cientifico,
        "descripcion": descripcion,
        "ruta_modelo_3d": nombre_modelo_3d,      
        "ruta_img": nombre_img,            
        "estado_nombre": estado            
        }
    ]

    agregar_animales_a_db()