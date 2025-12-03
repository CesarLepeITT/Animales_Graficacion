```mermaid
graph TD
    User((Usuario))
    subgraph "Aplicación Catálogo 3D"
        Browse[Navegar Lista por Estados]
        Search[Buscar por Nombre/Estado]
        ViewDetail[Ver Detalles del Animal]
        View3D[Abrir Visor 3D Interactivo]
        
        DBQuery(Consultar Controlador/BD Local)
        LoadMesh(Cargar y Previsualizar Malla 3D)

        User --> Browse
        User --> Search
        User --> ViewDetail
        
        %% Relaciones corregidas
        Browse -.->|include| DBQuery
        Search -.->|include| DBQuery
        ViewDetail -.->|include| LoadMesh
        View3D -.->|extend| ViewDetail
    end

    style DBQuery fill:#ffecb3,stroke:#333,stroke-width:1px,color:black
    style LoadMesh fill:#c8e6c9,stroke:#333,stroke-width:1px,color:black
