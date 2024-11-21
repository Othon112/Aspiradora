from mesa import Agent, Model
from mesa.time import SimultaneousActivation
from mesa.space import MultiGrid
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
import random
import matplotlib.pyplot as plt




# Agente base para diferentes tipos de vehículos
class VehicleAgent(Agent):
    def __init__(self, unique_id, model, start_pos, direction, step_size=1):
        super().__init__(unique_id, model)
        self.start_pos = start_pos
        self.direction = direction
        self.step_size = step_size

    def move_and_wrap(self):
        x, y = self.pos
        if self.direction == "horizontal":
            next_x = (x + self.step_size) % self.model.grid.width
            next_pos = (next_x, y)
        else:
            next_y = (y + self.step_size) % self.model.grid.height
            next_pos = (x, next_y)
        self.model.grid.move_agent(self, next_pos)

# Agente para representar edificios, estacionamientos y otras estructuras estáticas
class BoundaryAgent(Agent):
    def __init__(self, unique_id, model, type):
        super().__init__(unique_id, model)
        self.type = type  # Tipo de elemento (e.g., "building", "parking", etc.)


# Agente de automóvil regular
class CarAgent(VehicleAgent):
    def __init__(self, unique_id, model, start_pos, direction):
        super().__init__(unique_id, model, start_pos, direction)

    def step(self):
        # Detenerse en semáforos rojos
        if not self.model.is_light_green(self.direction):
            for light_pos in self.model.traffic_light_positions:
                if self.pos == (light_pos[0] - 1, light_pos[1]) and self.direction == "horizontal":
                    return
                if self.pos == (light_pos[0], light_pos[1] - 1) and self.direction == "vertical":
                    return
        self.move_and_wrap()


# Agente de vehículo de emergencia
class EmergencyVehicleAgent(VehicleAgent):
    def __init__(self, unique_id, model, start_pos, direction):
        super().__init__(unique_id, model, start_pos, direction, step_size=2)

    def step(self):
        # Los vehículos de emergencia no respetan semáforos
        self.move_and_wrap()


# Agente de transporte público
class BusAgent(VehicleAgent):
    def __init__(self, unique_id, model, start_pos, direction, bus_stops):
        super().__init__(unique_id, model, start_pos, direction)
        self.bus_stops = bus_stops
        self.stop_counter = 0

    def step(self):
        if self.pos in self.bus_stops:
            if self.stop_counter < 3:  # Espera 3 pasos en cada parada
                self.stop_counter += 1
                return
            else:
                self.stop_counter = 0
        self.move_and_wrap()


# Agente de conductor agresivo
class AggressiveDriverAgent(VehicleAgent):
    def __init__(self, unique_id, model, start_pos, direction):
        super().__init__(unique_id, model, start_pos, direction)

    def step(self):
        # Ignorar semáforos con una probabilidad del 80%
        if not self.model.is_light_green(self.direction) and random.random() < 0.8:
            return
        self.move_and_wrap()


# Agente de semáforo
class TrafficLightAgent(Agent):
    def __init__(self, unique_id, model, pos, orientation):
        super().__init__(unique_id, model)
        self.pos = pos
        self.state = "red"
        self.orientation = orientation

    def turn_green(self):
        self.state = "green"

    def turn_red(self):
        self.state = "red"


class TrafficModel(Model):
    def __init__(self, M, N, light_interval):
        self.grid = MultiGrid(M, N, True)
        self.schedule = SimultaneousActivation(self)
        self.running = True
        self.light_interval = light_interval
        self.step_count = 0

        # Definir posiciones de semáforos (actualizadas según el mapa)
        self.traffic_light_positions = [
    (8, 6), (8, 9),  # Semáforos norte
    (20, 6), (20, 9),  # Semáforos sur
    (13, 11), (13, 14),  # Semáforos este
    (11, 13), (14, 13)  # Semáforos oeste
]

        self.traffic_lights = {}
        for i, pos in enumerate(self.traffic_light_positions):
            orientation = "horizontal" if i % 2 == 0 else "vertical"
            light = TrafficLightAgent(f"light_{i}", self, pos, orientation)
            self.traffic_lights[pos] = light
            self.grid.place_agent(light, pos)
            self.schedule.add(light)

        # Definir la glorieta (posiciones centrales)
        self.glorieta_positions = [
            (12, 12), (13, 12), (12, 13), (13, 13)  # Posiciones centrales para la glorieta
        ]
        for pos in self.glorieta_positions:
            glorieta = BoundaryAgent(f"glorieta_{pos}", self, "glorieta")
            self.grid.place_agent(glorieta, pos)

        # Definir edificios (posiciones específicas)
        self.building_positions = [
            (2, 2), (3, 2), (4, 2), (2, 3), (3, 3), (4, 3),  # Edificio 1
            (2, 12), (3, 12), (4, 12), (2, 13), (3, 13), (4, 13),  # Edificio 2
            (16, 2), (17, 2), (18, 2), (16, 3), (17, 3), (18, 3),  # Edificio 3
            (16, 16), (17, 16), (18, 16), (16, 17), (17, 17), (18, 17)  # Edificio 4
        ]

        for pos in self.building_positions:
            building = BoundaryAgent(f"building_{pos}", self, "building")
            self.grid.place_agent(building, pos)

        # Agregar vehículos
        self.add_vehicles()

    def add_vehicles(self):
        # Autos regulares
        car_start_pos = (0, 9)
        car = CarAgent("car", self, car_start_pos, "horizontal")
        self.grid.place_agent(car, car_start_pos)
        self.schedule.add(car)

        # Vehículo de emergencia
        emergency_start_pos = (0, 8)
        emergency_vehicle = EmergencyVehicleAgent("emergency", self, emergency_start_pos, "horizontal")
        self.grid.place_agent(emergency_vehicle, emergency_start_pos)
        self.schedule.add(emergency_vehicle)

        # Autobús
        bus_start_pos = (6, 0)
        bus_stops = [(6, 6), (6, 14)]
        bus = BusAgent("bus", self, bus_start_pos, "vertical", bus_stops)
        self.grid.place_agent(bus, bus_start_pos)
        self.schedule.add(bus)

        # Conductor agresivo
        aggressive_start_pos = (0, 10)
        aggressive_driver = AggressiveDriverAgent("aggressive", self, aggressive_start_pos, "horizontal")
        self.grid.place_agent(aggressive_driver, aggressive_start_pos)
        self.schedule.add(aggressive_driver)

    def is_light_green(self, direction):
        for light in self.traffic_lights.values():
            if light.state == "green" and light.orientation == direction:
                return True
        return False

    def step(self):
        # Alternar semáforos
        if self.step_count % (2 * self.light_interval) < self.light_interval:
            for light in self.traffic_lights.values():
                if light.orientation == "horizontal":
                    light.turn_green()
                else:
                    light.turn_red()
        else:
            for light in self.traffic_lights.values():
                if light.orientation == "vertical":
                    light.turn_green()
                else:
                    light.turn_red()

        self.step_count += 1
        self.schedule.step()


# Visualización
def agent_portrayal(agent):
    portrayal = {"Shape": "rect", "Filled": "true", "w": 1, "h": 1}
    if isinstance(agent, BoundaryAgent) and agent.type == "building":
        portrayal.update({"Color": "blue", "Layer": 0})  # Representar edificios en azul
    elif isinstance(agent, CarAgent):
        portrayal.update({"Color": "blue", "Shape": "circle", "r": 0.5, "Layer": 1})
    elif isinstance(agent, EmergencyVehicleAgent):
        portrayal.update({"Color": "red", "Shape": "circle", "r": 0.7, "Layer": 2})
    elif isinstance(agent, BusAgent):
        portrayal.update({"Color": "orange", "Shape": "rect", "w": 1, "h": 2, "Layer": 1})
    elif isinstance(agent, AggressiveDriverAgent):
        portrayal.update({"Color": "darkred", "Shape": "circle", "r": 0.5, "Layer": 2})
    elif isinstance(agent, TrafficLightAgent):
        portrayal.update({"Color": "green" if agent.state == "green" else "red", "Shape": "circle", "r": 0.5, "Layer": 3})
    elif isinstance(agent, BoundaryAgent) and agent.type == "glorieta":
        portrayal.update({"Color": "brown", "Layer": 0})  # Representar glorieta en marrón

    return portrayal



# Parámetros de simulación
M, N = 24, 24
light_interval = 10
grid = CanvasGrid(agent_portrayal, M, N, 600, 600)
server = ModularServer(TrafficModel, [grid], "Simulación de Tráfico con Tipos de Vehículos", {"M": M, "N": N, "light_interval": light_interval})
server.port = 8521

if __name__ == "__main__":
    server.launch()
