# Simulación de Robot de Limpieza Reactivo

Este repositorio contiene código para la simulación de movimientos de un agente y la implementación de los algoritmos de búsqueda BFS y DFS. A continuación se describen las instrucciones de uso.

## Archivos y Estructura

- **M1\_reactivo.py**: Este archivo contiene la simulación de los movimientos aleatorios del agente. Para ejecutar la simulación con movimientos random, utiliza este archivo.

- **Carpeta `graph`**: En esta carpeta se encuentra la implementación de los algoritmos de búsqueda BFS y DFS.

- **Archivo `run_server`**: En este archivo puedes configurar y cambiar el algoritmo de búsqueda que se usará en la simulación.

## Configuración de Algoritmos de Búsqueda

Para cambiar el algoritmo de búsqueda (BFS o DFS), edita la siguiente parte del archivo `run_server`:

```python
server = ModularServer(
    VacuumModel,
    [grid, chart],
    "Vacuum Cleaning Model",
    {"n_vacuums": 1, "n_trash": 20, "width": 10, "height": 10, "search_algorithm": 'dfs'}
)
```

- Modifica el valor de `"search_algorithm"` para cambiar entre 'dfs' (Depth-First Search) y 'bfs' (Breadth-First Search).

## Ejecución

- Ejecuta el archivo `M1_reactivo.py` para ver la simulación de los movimientos aleatorios.
- Usa el archivo `run_server` en la carpeta `graph` para ejecutar la simulación con el algoritmo de búsqueda configurado.

