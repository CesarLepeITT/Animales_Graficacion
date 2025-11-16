import tkinter as tk
import os
import subprocess # Para llamar al script de creación de DB

# Importar las clases de los otros archivos
from data.app_controller import AppController
from ui.main_view import MainView # Asumiendo que tu archivo se llama main_view.py


data_path = os.path.join(os.getcwd(), 'data')
DB_FILE = os.path.join(data_path, 'animales.db')
CREATE_DB_SCRIPT = os.path.join(data_path, 'create_db.py')

def setup_database():
    """
    Verifica si la base de datos existe.
    Si no existe, ejecuta el script crear_db.py para generarla.
    """
    if not os.path.exists(DB_FILE):
        print(f"No se encontró '{DB_FILE}'. Ejecutando {CREATE_DB_SCRIPT}...")
        try:
            # Ejecutar el script de creación de DB
            # Usamos 'python' para asegurarnos de que se use el intérprete correcto
            subprocess.run(['python', CREATE_DB_SCRIPT], check=True)
            print("Base de datos creada exitosamente.")
        except subprocess.CalledProcessError as e:
            print(f"Error al ejecutar {CREATE_DB_SCRIPT}: {e}")
            print("La aplicación no puede continuar sin una base de datos.")
            exit(1)
        except FileNotFoundError:
            print(f"Error: No se encontró el script '{CREATE_DB_SCRIPT}'.")
            print("Asegúrate de que esté en la misma carpeta que main.py")
            exit(1)
    else:
        print(f"Base de datos '{DB_FILE}' encontrada.")


def main():
    """
    Función principal de la aplicación.
    """
    # 1. Asegurarse de que la DB exista
    setup_database()
    
    # 2. Inicializar el Controlador
    #    (El controlador se conecta a la DB)
    try:
        controller = AppController(DB_FILE)
    except Exception as e:
        print(f"Error fatal al inicializar el controlador: {e}")
        return

    # 3. Inicializar la Vista Principal
    #    (La vista recibe el controlador para funcionar)
    app = MainView(controller)
    
    # 4. Darle al controlador una referencia a la vista
    #    (Esto es opcional pero bueno para la comunicación bidireccional)
    controller.set_view(app)
    
    # 5. Iniciar el bucle de la aplicación
    app.mainloop()

if __name__ == '__main__':
    # Asegúrate de tener las dependencias:
    print("Recordatorio: asegúrate de haber instalado 'meshio', 'matplotlib', 'numpy' y 'pillow'.")
    print("Ejecuta: pip install meshio matplotlib numpy pillow")
    main()