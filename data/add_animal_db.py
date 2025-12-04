import sqlite3
import os
import shutil
import wikipedia
import sys

# Configuración de rutas
BASE_DIR = os.getcwd()
DB_FILE = os.path.join(BASE_DIR, 'data', 'animales.db')
BUCKET_DIR = os.path.join(BASE_DIR, 'bucket')
IMG_DEST_DIR = os.path.join(BASE_DIR, 'img')
MODELS_DEST_DIR = os.path.join(BASE_DIR, 'models')

# Configurar idioma de wikipedia
wikipedia.set_lang("es")

def obtener_descripcion_automatica(termino_busqueda):
    """
    Busca el término en Wikipedia y retorna el resumen (2 oraciones).
    Si hay error o ambigüedad, retorna un string genérico.
    """
    print(f"   > Buscando descripción en Wikipedia para: '{termino_busqueda}'...")
    try:
        # auto_suggest=False evita que busque cosas raras si no encuentra el exacto
        descripcion = wikipedia.summary(termino_busqueda, sentences=3, auto_suggest=False)
        return descripcion
    except wikipedia.exceptions.DisambiguationError as e:
        print(f"   [AVISO] Ambigüedad en Wikipedia. Opciones: {e.options[:3]}")
        return f"Descripción pendiente. (Ambigüedad: {termino_busqueda})"
    except wikipedia.exceptions.PageError:
        print(f"   [AVISO] No se encontró página en Wikipedia para '{termino_busqueda}'.")
        return "Descripción no disponible automáticamente."
    except Exception as e:
        print(f"   [ERROR] Error de conexión o parsing: {e}")
        return "Descripción no disponible."

def procesar_bucket(nombre_comun):
    """
    Escanea la carpeta 'bucket'.
    1. Busca una imagen (.jpg, .png), la renombra a 'nombre_comun' y la mueve a /img.
    2. Busca una carpeta, la renombra a 'nombre_comun', la mueve a /models.
    3. Dentro de esa carpeta, busca el .obj y lo renombra a 'nombre_comun.obj'.
    
    Retorna (ruta_relativa_img, ruta_relativa_modelo) o lanza Exception si falta algo.
    """
    print(f"   > Procesando archivos en '{BUCKET_DIR}'...")
    
    if not os.path.exists(BUCKET_DIR):
        os.makedirs(BUCKET_DIR)
        raise FileNotFoundError(f"La carpeta 'bucket' no existía (se acaba de crear). Por favor coloca los archivos ahí.")

    archivos_bucket = os.listdir(BUCKET_DIR)
    if not archivos_bucket:
        raise FileNotFoundError("La carpeta 'bucket' está vacía.")

    ruta_final_img = None
    ruta_final_model = None

    # --- 1. PROCESAR IMAGEN ---
    # Buscamos cualquier archivo que termine en extensión de imagen
    img_files = [f for f in archivos_bucket if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
    
    if len(img_files) == 0:
        raise FileNotFoundError("No hay imágenes en el bucket.")
    elif len(img_files) > 1:
        print(f"   [CUIDADO] Hay varias imágenes. Se usará: {img_files[0]}")

    archivo_img_origen = img_files[0]
    ext_img = os.path.splitext(archivo_img_origen)[1] # .png, .jpg, etc
    nombre_img_destino = f"{nombre_comun}{ext_img}" # Conejo Castellano.png
    
    # Mover y Renombrar Imagen
    src_img = os.path.join(BUCKET_DIR, archivo_img_origen)
    dst_img = os.path.join(IMG_DEST_DIR, nombre_img_destino)
    
    shutil.move(src_img, dst_img)
    ruta_final_img = os.path.join('img', nombre_img_destino) # Ruta relativa para la DB
    print(f"     -> Imagen movida a: {ruta_final_img}")

    # --- 2. PROCESAR CARPETA DEL MODELO ---
    # Buscamos directorios dentro del bucket
    folder_files = [f for f in archivos_bucket if os.path.isdir(os.path.join(BUCKET_DIR, f))]
    
    if len(folder_files) == 0:
        # Si no hay carpeta, quizas solo subieron imagen. Dejamos ruta modelo vacía o lanzamos error.
        # Asumiremos que es obligatorio según tu script anterior.
        raise FileNotFoundError("No se encontró la carpeta del modelo 3D en el bucket.")
    
    carpeta_origen = folder_files[0] # Tomamos la primera carpeta que encontremos
    
    # Ruta destino de la carpeta: models/Conejo Castellano
    src_folder = os.path.join(BUCKET_DIR, carpeta_origen)
    dst_folder = os.path.join(MODELS_DEST_DIR, nombre_comun)
    
    # Si la carpeta destino ya existe, hay que decidir si borrarla o error. 
    # Para actualizar, la borramos y ponemos la nueva.
    if os.path.exists(dst_folder):
        shutil.rmtree(dst_folder)
    
    shutil.move(src_folder, dst_folder)
    
    # --- 3. RENOMBRAR .OBJ DENTRO DE LA CARPETA ---
    archivos_en_modelo = os.listdir(dst_folder)
    obj_files = [f for f in archivos_en_modelo if f.lower().endswith('.obj')]
    
    nombre_obj_final = f"{nombre_comun}.obj"
    
    if obj_files:
        src_obj = os.path.join(dst_folder, obj_files[0])
        dst_obj = os.path.join(dst_folder, nombre_obj_final)
        os.rename(src_obj, dst_obj)
        # La ruta que guardamos en DB es hasta el archivo .obj
        ruta_final_model = os.path.join('models', nombre_comun, nombre_obj_final)
        print(f"     -> Modelo procesado: {ruta_final_model}")
    else:
        print("     [ADVERTENCIA] Se movió la carpeta pero no contenía un archivo .obj para renombrar.")
        # Asumimos ruta genérica si no hay obj, o dejamos la carpeta
        ruta_final_model = os.path.join('models', nombre_comun)

    return ruta_final_img, ruta_final_model

def validar_lista_animales(lista_animales, set_estados_db, set_animales_db):
    # ... (TU CÓDIGO ORIGINAL DE VALIDACIÓN SIN CAMBIOS) ...
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

        campos_faltantes = campos_requeridos - set(animal.keys())
        if campos_faltantes:
            errores.append(f"  [ERROR] {id_animal_str}: Faltan campos: {', '.join(campos_faltantes)}")
            es_valido = False
            continue 
        
        if animal['estado_nombre'] not in set_estados_db:
            errores.append(f"  [ERROR] {id_animal_str}: El estado '{animal['estado_nombre']}' no existe en la base de datos.")
            es_valido = False
            
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

def agregar_animales_a_db(nuevos_animales):
    # ... (TU CÓDIGO ORIGINAL DE DB, LIGERAMENTE ADAPTADO PARA RECIBIR ARGUMENTO) ...
    if not os.path.exists(DB_FILE):
        print(f"Error: No se encontró la base de datos '{DB_FILE}'.")
        return

    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        print(f"Conectado a '{DB_FILE}'.")

        cursor.execute("SELECT nombre FROM estados")
        set_estados_db = {row[0] for row in cursor.fetchall()}
        
        cursor.execute("SELECT nombre_comun FROM animales")
        set_animales_db = {row[0] for row in cursor.fetchall()}
        
        cursor.execute("SELECT nombre, id FROM estados")
        mapa_estados_id = {row[0]: row[1] for row in cursor.fetchall()}

        print(f"\nValidando {len(nuevos_animales)} animales de la lista...")
        animales_para_procesar, errores = validar_lista_animales(
            nuevos_animales, set_estados_db, set_animales_db
        )

        if errores:
            print(f"\nSe encontraron {len(errores)} problemas:")
            for error in errores:
                print(error)
        else:
            print("¡Todas las validaciones pasaron!")

        if not animales_para_procesar:
            print("\nNo hay animales válidos para procesar. Terminando.")
            return

        total_agregados = 0
        total_actualizados = 0
        
        for animal in animales_para_procesar:
            try:
                estado_id = mapa_estados_id[animal["estado_nombre"]]
                if animal["nombre_comun"] in set_animales_db:
                    cursor.execute("""
                        UPDATE animales 
                        SET nombre_cientifico = ?, descripcion = ?, ruta_modelo_3d = ?, ruta_img = ?, estado_id = ?
                        WHERE nombre_comun = ?
                    """, (animal["nombre_cientifico"], animal["descripcion"], animal["ruta_modelo_3d"], animal["ruta_img"], estado_id, animal["nombre_comun"]))
                    print(f"  [MODIFICADO]: Se actualizaron los datos de '{animal['nombre_comun']}'.")
                    total_actualizados += 1
                else:
                    cursor.execute("""
                        INSERT INTO animales (nombre_comun, nombre_cientifico, descripcion, ruta_modelo_3d, ruta_img, estado_id)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (animal["nombre_comun"], animal["nombre_cientifico"], animal["descripcion"], animal["ruta_modelo_3d"], animal["ruta_img"], estado_id))
                    print(f"  [NUEVO]: Se agregó '{animal['nombre_comun']}' a la base de datos.")
                    total_agregados += 1
            except sqlite3.Error as e:
                print(f"  Error de SQLite: {e}")
        
        if total_agregados > 0 or total_actualizados > 0:
            conn.commit()
            print(f"\n¡Operación completada! Nuevos: {total_agregados}, Actualizados: {total_actualizados}.")
            
    except sqlite3.Error as e:
        print(f"Error fatal DB: {e}")
    finally:
        if conn:
            conn.close()

# --- BLOQUE PRINCIPAL DE AUTOMATIZACIÓN ---
if __name__ == '__main__':
    
    # ---------------------------------------------------------
    # 1. DATOS DE ENTRADA MANUAL (Solo estos 3 datos)
    # ---------------------------------------------------------
    NOMBRE_COMUN_INPUT = 'Ajolote' 
    NOMBRE_CIENTIFICO_INPUT = 'Ambystoma mexicanum' 
    ESTADO_INPUT = 'Ciudad de México'
    # ---------------------------------------------------------

    print("--- INICIANDO AUTOMATIZACIÓN ---")

    try:
        # A. Procesar archivos (Mover y Renombrar)
        ruta_img, ruta_modelo = procesar_bucket(NOMBRE_COMUN_INPUT)

        # B. Obtener Descripción (Wikipedia)
        descripcion_auto = obtener_descripcion_automatica(NOMBRE_CIENTIFICO_INPUT)
        
        # C. Preparar objeto para DB
        nuevos_animales = [
            {
                "nombre_comun": NOMBRE_COMUN_INPUT,
                "nombre_cientifico": NOMBRE_CIENTIFICO_INPUT,
                "descripcion": descripcion_auto,
                "ruta_modelo_3d": ruta_modelo,      
                "ruta_img": ruta_img,            
                "estado_nombre": ESTADO_INPUT            
            }
        ]

        # D. Ejecutar Inserción
        agregar_animales_a_db(nuevos_animales)

    except Exception as e:
        print(f"\n[ERROR FATAL EN EL PROCESO]: {e}")
        print("No se realizaron cambios en la base de datos.")