from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
from model import TrafficModel
from agents import (
    BoundaryAgent, CarAgent, EmergencyVehicleAgent, 
    BusAgent, AggressiveDriverAgent, TrafficLightAgent
)

def agent_portrayal(agent):
    portrayal = {"Shape": "rect", "Filled": "true", "w": 1, "h": 1}
    
    if isinstance(agent, BoundaryAgent):
        # Edificios
        portrayal["Color"] = "#87CEEB"  # Azul claro
        portrayal["Layer"] = 0
    elif isinstance(agent, CarAgent):
        # Carros
        portrayal["Color"] = "#0000FF"  # Azul
        portrayal["Shape"] = "circle"
        portrayal["r"] = 0.5
        portrayal["Layer"] = 1
    elif isinstance(agent, EmergencyVehicleAgent):
        # Vehículos de emergencia
        portrayal["Color"] = "#FF0000"  # Rojo
        portrayal["Shape"] = "circle"
        portrayal["r"] = 0.7
        portrayal["Layer"] = 2
    elif isinstance(agent, BusAgent):
        # Autobuses
        portrayal["Color"] = "#FFA500"  # Naranja
        portrayal["Shape"] = "rect"
        portrayal["w"] = 1
        portrayal["h"] = 2
        portrayal["Layer"] = 1
    elif isinstance(agent, AggressiveDriverAgent):
        # Conductores agresivos
        portrayal["Color"] = "#8B0000"  # Rojo oscuro
        portrayal["Shape"] = "circle"
        portrayal["r"] = 0.5
        portrayal["Layer"] = 2
    elif isinstance(agent, TrafficLightAgent):
        # Semáforos
        portrayal["Color"] = "#00FF00" if agent.state == "green" else "#FF0000"  # Verde o rojo
        portrayal["Shape"] = "circle"
        portrayal["r"] = 0.5
        portrayal["Layer"] = 1
    elif agent.pos[1] in [3, 6, 9, 12, 15, 18, 21]:
        # Estacionamientos
        portrayal["Color"] = "#FFFF00"  # Amarillo
        portrayal["Layer"] = 1
    elif agent.pos[0] in [1, 5, 9, 13, 17, 21]:
        # Glorietas
        portrayal["Color"] = "#8B4513"  # Marrón
        portrayal["Layer"] = 1
    elif agent.pos[0] in [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24] and \
         agent.pos[1] in [2, 4, 7, 10, 13, 16, 19, 22]:
        # Líneas peatonales
        portrayal["Color"] = "#000000"  # Negro
        portrayal["Layer"] = 0
    else:
        # Calles
        portrayal["Color"] = "#DCDCDC"  # Gris claro
        portrayal["Layer"] = 0
    
    return portrayal

# Parámetros de simulación
M, N = 24, 24
light_interval = 10
grid = CanvasGrid(agent_portrayal, M, N, 800, 800)
server = ModularServer(TrafficModel, [grid], "Traffic Simulation with Various Vehicles", {"M": M, "N": N, "light_interval": light_interval})
server.port = 8521
if __name__ == "__main__":
    server.launch()