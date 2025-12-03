```mermaid
sequenceDiagram
    autonumber
    actor Usuario
    participant MainView as Vista Principal (UI)
    participant Controller as AppController (Lógica)
    participant DB as SQLite DB (Datos)
    participant DetailPanel as Panel de Detalles (UI)
    participant PyVista as Motor 3D (PyVista)

    Note over Usuario, DB: --- Flujo de Búsqueda ---
    Usuario->>MainView: Escribe en buscador (ej. "Ajolote")
    MainView->>Controller: get_filtered_data("Ajolote")
    Controller->>DB: EXECUTE SELECT ... WHERE nombre LIKE '%Ajolote%'...
    DB-->>Controller: Retorna filas (lista de tuplas/dicts)
    Controller->>Controller: Agrupar resultados por Estado
    Controller-->>MainView: Retorna diccionario de datos agrupados
    MainView->>MainView: Regenerar tarjetas de animales (AnimalCard)

    Note over Usuario, PyVista: --- Flujo de Selección y Visualización 3D ---
    Usuario->>MainView: Clic en Tarjeta de Animal
    MainView->>DetailPanel: show_detail_view(datos_animal)
    DetailPanel->>DetailPanel: Actualizar Labels (Nombre, Descripción)
    
    par Carga de Recursos Gráficos
        DetailPanel->>PyVista: pv.read(ruta_modelo_obj)
        PyVista-->>DetailPanel: Retorna objeto Malla (Mesh)
        DetailPanel->>PyVista: Generar screenshot off-screen (Preview)
        PyVista-->>DetailPanel: Retorna Imagen Estática
    end
    
    DetailPanel->>DetailPanel: Mostrar Imagen Preview en UI

    Usuario->>DetailPanel: Clic botón "ABRIR VISOR 3D"
    DetailPanel->>PyVista: Crear e iniciar Plotter Interactivo (show)
    PyVista-->>Usuario: Abre Ventana 3D Interactiva```
