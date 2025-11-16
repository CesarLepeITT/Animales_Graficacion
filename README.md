# **Catálogo de Fauna Mexicana 3D**

Este proyecto es una aplicación de escritorio desarrollada con Python y Tkinter que muestra un catálogo interactivo de la fauna de México, con la capacidad de visualizar modelos 3D de diferentes especies.

## **Características**

* Visualización de animales filtrados por estado.  
* Búsqueda en tiempo real por nombre común, nombre científico o estado.  
* Visor de modelos 3D (.obj) interactivo.  
* Base de datos SQLite para un manejo eficiente de la información.

## Tecnologías
- Python
- Tkinter
- SQLite

## **Requisitos**

Para ejecutar este proyecto, necesitas tener Python 3 instalado y las siguientes bibliotecas.

```
matplotlib==3.10.7
meshio==5.3.5
numpy==2.3.4
Pillow==12.0.0

```


Puedes instalarlas todas a la vez ejecutando el siguiente comando en tu terminal (asegúrate de que el archivo requirements.txt esté en la misma carpeta):
```
pip install \-r requirements.txt
```
## **Cómo Ejecutar la Aplicación**

1. Asegúrate de tener todas las dependencias listadas arriba.  
2. Ejecuta el script principal main.py desde tu terminal:  ```python main.py```
3. La primera vez que lo ejecutes, main.py puede detectar que la base de datos no existe y llamará automáticamente al script ```create_db.py``` para generar el archivo animales.db con datos de relleno.  
4. La aplicación se iniciará y podrás explorarla.

## **Cómo Añadir un Nuevo Animal**

Para agregar nuevos animales al catálogo, sigue este proceso de 4 pasos.

### **Paso 1: Prepara tus Archivos**

Prepara los dos archivos que vas a necesitar para tu animal:

* **Modelo 3D:** Un archivo en formato .obj. Colócalo dentro de la carpeta models/.  
  * Ejemplo: models/nuevo\_animal.obj  
* **Imagen:** Un archivo .jpg o .png que sirva como ícono. Colócalo dentro de la carpeta img/.  
  * Ejemplo: img/nuevo\_animal.jpg

*(Nota: Las carpetas models/ e img/ deben estar en la raíz de tu proyecto, al mismo nivel que main.py).*

### **Paso 2: Edita el Script de Inserción**

Abre el archivo ```agregar_animal.py``` en tu editor de código.

Localiza la lista llamada nuevos\_animales cerca de la parte inferior del archivo. Añade la información de tu animal siguiendo el formato indicado en el archivo.


**¡Importante\!** El estado debe coincidir **exactamente** con un nombre de la base de datos (ej. "Ciudad de México", "Chihuahua", "Yucatán").

### **Paso 3: Ejecuta el Script de Validación**

Guarda el archivo ```agregar_animal.py``` y ejecútalo desde tu terminal:

```python agregar_animal.py```

El script se conectará a animales.db y validará cada animal que añadiste. Comprobará automáticamente:

* Que todos los campos existan y no estén vacíos.  
* Que el estado\_nombre exista en la base de datos.  
* Que el nombre\_comun no esté duplicado.  
* Que los archivos .obj e .jpg que especificaste **existan realmente** en las carpetas.

Si un animal falla alguna validación, el script te informará del error y no lo agregará. Solo los animales que pasen todas las pruebas se guardarán en la base de datos.

### **Paso 4: Verifica en la Aplicación**

¡Listo\! Vuelve a ejecutar la aplicación principal:

python main.py

Busca tu nuevo animal en la lista o usando la barra de búsqueda. Debería aparecer y ser totalmente funcional.