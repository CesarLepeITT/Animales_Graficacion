import sqlite3
import os

nuevos_animales = []
DB_FILE = os.path.join(os.getcwd(), 'data', 'animales.db')

def validar_lista_animales(lista_animales, set_estados_db, set_animales_db):
    """
    Valida una lista de diccionarios de animales antes de la inserción/actualización.
    
    Comprueba:
    1. Campos requeridos.
    2. Existencia del estado en la DB.
    3. Existencia de los archivos de imagen y modelo.
    
    NOTA: Ya no marca error si existe el animal, pues se actualizará.
    
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
            if isinstance(animal[key], str) and animal[key].strip() == '':
                errores.append(f"  [ERROR] {id_animal_str}: El campo '{key}' está presente pero no puede estar vacío.")
                es_valido = False

        # 1. Validar campos requeridos
        campos_faltantes = campos_requeridos - set(animal.keys())
        if campos_faltantes:
            errores.append(f"  [ERROR] {id_animal_str}: Faltan campos: {', '.join(campos_faltantes)}")
            es_valido = False
            continue 
        
        # 2. Validar existencia de estado
        if animal['estado_nombre'] not in set_estados_db:
            errores.append(f"  [ERROR] {id_animal_str}: El estado '{animal['estado_nombre']}' no existe en la base de datos.")
            es_valido = False
            
        # 3. Validar existencia de archivos
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
    Se conecta a la base de datos, valida la lista de 'nuevos_animales'.
    Si el animal existe, lo ACTUALIZA. Si no existe, lo INSERTA.
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
        print("Cargando datos existentes...")
        
        cursor.execute("SELECT nombre FROM estados")
        set_estados_db = {row[0] for row in cursor.fetchall()}
        
        cursor.execute("SELECT nombre_comun FROM animales")
        set_animales_db = {row[0] for row in cursor.fetchall()}
        
        cursor.execute("SELECT nombre, id FROM estados")
        mapa_estados_id = {row[0]: row[1] for row in cursor.fetchall()}

        # --- 2. VALIDAR ---
        print(f"\nValidando {len(nuevos_animales)} animales de la lista...")
        animales_para_procesar, errores = validar_lista_animales(
            nuevos_animales, set_estados_db, set_animales_db
        )

        # --- 3. REPORTAR ERRORES ---
        if errores:
            print(f"\nSe encontraron {len(errores)} problemas. Estos animales NO se procesarán:")
            for error in errores:
                print(error)
        else:
            print("¡Todas las validaciones pasaron!")

        if not animales_para_procesar:
            print("\nNo hay animales válidos para procesar. Terminando.")
            return

        # --- 4. INSERTAR O ACTUALIZAR ANIMALES ---
        print(f"\nProcesando {len(animales_para_procesar)} animales...")
        total_agregados = 0
        total_actualizados = 0
        
        for animal in animales_para_procesar:
            try:
                estado_id = mapa_estados_id[animal["estado_nombre"]]
                
                # VERIFICAR SI YA EXISTE PARA DECIDIR ACCIÓN
                if animal["nombre_comun"] in set_animales_db:
                    # --- ACTUALIZAR (UPDATE) ---
                    cursor.execute("""
                        UPDATE animales 
                        SET nombre_cientifico = ?, 
                            descripcion = ?, 
                            ruta_modelo_3d = ?, 
                            ruta_img = ?, 
                            estado_id = ?
                        WHERE nombre_comun = ?
                    """, (
                        animal["nombre_cientifico"],
                        animal["descripcion"],
                        animal["ruta_modelo_3d"],
                        animal["ruta_img"],
                        estado_id,
                        animal["nombre_comun"] # WHERE clause
                    ))
                    print(f"  [MODIFICADO]: Se actualizaron los datos de '{animal['nombre_comun']}'.")
                    total_actualizados += 1
                
                else:
                    # --- INSERTAR (INSERT) ---
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
                    print(f"  [NUEVO]: Se agregó '{animal['nombre_comun']}' a la base de datos.")
                    total_agregados += 1
            
            except sqlite3.Error as e:
                print(f"  Error de SQLite al procesar '{animal['nombre_comun']}': {e}")
        
        # 5. Guardar cambios (commit) y cerrar
        if total_agregados > 0 or total_actualizados > 0:
            conn.commit()
            print(f"\n¡Operación completada! Nuevos: {total_agregados}, Actualizados: {total_actualizados}.")
        else:
            print("\nOperación completada. No hubo cambios en la base de datos.")
            
    except sqlite3.Error as e:
        print(f"Error fatal al conectar con la base de datos: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':

# --- INSTRUCCIONES DE USO ---
#
# 1. PREPARA TUS ARCHIVOS:
#    - Modelo 3D: Coloca tu archivo .obj en la carpeta /models/
#    - Imagen: Coloca tu archivo .jpg o .png en la carpeta /img/
#
# 2. EDITA ESTA LISTA:
#    - Si el 'nombre_comun' YA EXISTE en la DB, se actualizarán sus datos.
#    - Si NO EXISTE, se creará uno nuevo.
#
# 3. EJECUTA EL SCRIPT:
#    python agregar_animal.py
# --- FIN DE INSTRUCCIONES ---

    nombre_comun = 'Halcón Cola Roja'
    nombre_cientifico = 'Buteo Jamaicensis'
    descripcion = 'El Busardo Colirrojo (Buteo jamaicensis) es una especie de ave rapaz grande de la familia Accipitridae. Es uno de los halcones más grandes del género Buteo, pudiendo alcanzar hasta 65 cm y 1,6 kg de peso. Su distribución es muy amplia, extendiéndose desde Alaska en el norte hasta las Antillas. Vive en una gran variedad de hábitats y altitudes, desde desiertos y pastizales hasta zonas urban'
    nombre_modelo_3d = 'models/HalconColaRoja/tripo_convert_d61732e8-bde4-4450-9754-4f9613eec11c.obj'
    nombre_img = 'img/HalconColaRoja.jpg'
    estado = 'Zacatecas'

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