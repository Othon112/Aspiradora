import mesa
from mesa.visualization.modules import CanvasGrid, ChartModule
from mesa.visualization.ModularVisualization import ModularServer
from mesa.datacollection import DataCollector
from VacumModel import VacuumModel, agent_portrayal 

# Set up the grid visualization
grid = CanvasGrid(agent_portrayal, 10, 10, 500, 500)

# Set up the chart visualization for cleaned trash count
chart = ChartModule(
    [{"Label": "CleanedTrash", "Color": "Black"}],
    data_collector_name='datacollector'
)

# Set up the server
server = ModularServer(
    VacuumModel,
    [grid, chart],
    "Vacuum Cleaning Model",
    {"n_vacuums": 3, "n_trash": 10, "width": 10, "height": 10, "search_algorithm": 'bfs'}
)

server.port = 8521
server.launch()
