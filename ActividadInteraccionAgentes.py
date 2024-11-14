from mesa import Agent, Model
from mesa.time import SimultaneousActivation
from mesa.space import MultiGrid
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
import random
import plotly.graph_objects as go

# Clase del agente Vehículo
class VehicleAgent(Agent):
    def __init__(self, unique_id, model, arrival_time, direction):
        super().__init__(unique_id, model)
        self.arrival_time = arrival_time
        self.direction = direction
        self.target_light = model.traffic_lights[direction]
        self.malicious = random.random() < 0.3  # Asigna un 30% de probabilidad de que el vehículo sea malicioso

    def step(self):
        if self.pos == self.model.base_location:
            self.model.vehicles_at_base += 1
            self.reappear()
        elif self.pos == self.target_light.pos:
            if self.target_light.state == "green" or (self.malicious and random.random() < 0.5):
                self.model.grid.move_agent(self, self.model.base_location)
            else:
                self.model.record_collision(self.pos)
        else:
            next_move = self.move_towards_light()
            if self.model.grid.is_cell_empty(next_move) or (next_move == self.target_light.pos and self.target_light.state == "green"):
                self.model.grid.move_agent(self, next_move)

    def reappear(self):
        new_pos, new_direction = self.model.get_near_light_spawn_location()
        self.direction = new_direction
        self.target_light = self.model.traffic_lights[new_direction]
        self.model.grid.place_agent(self, new_pos)

    def move_towards_light(self):
        x, y = self.pos
        target_x, target_y = self.target_light.pos
        if x < target_x:
            x += 1
        elif x > target_x:
            x -= 1
        if y < target_y:
            y += 1
        elif y > target_y:
            y -= 1
        return (x, y)

# Clase del agente Semáforo
class TrafficLightAgent(Agent):
    def __init__(self, unique_id, model, pos):
        super().__init__(unique_id, model)
        self.pos = pos
        self.state = "red"

    def step(self):
        pass

# Clase del agente Base
class BaseAgent(Agent):
    def __init__(self, unique_id, model, pos):
        super().__init__(unique_id, model)
        self.pos = pos

# Clase de agente para registrar colisiones
class CollisionAgent(Agent):
    def __init__(self, unique_id, model, pos):
        super().__init__(unique_id, model)
        self.pos = pos

# Modelo principal
class TrafficIntersectionModel(Model):
    def __init__(self, M, N, num_vehicles):
        self.grid = MultiGrid(M, N, True)
        self.schedule = SimultaneousActivation(self)
        self.num_vehicles = num_vehicles
        self.running = True
        self.current_green = "north"
        self.base_location = (M // 2, N - 1)
        self.vehicles_at_base = 0
        self.collisions = 0
        self.steps = []
        self.vehicles_data = []
        self.collisions_data = []

        # Inicializar el diccionario de feromonas correctamente
        self.pheromones = {(x, y): 0 for x in range(M) for y in range(N)}

        # Configurar semáforos
        light_positions = {
            "north": (M // 2, N // 2 - 1),
            "south": (M // 2, N // 2 + 1),
            "east": (M // 2 + 1, N // 2),
            "west": (M // 2 - 1, N // 2)
        }
        self.traffic_lights = {}
        for direction, pos in light_positions.items():
            light = TrafficLightAgent(f"light_{direction}", self, pos)
            self.traffic_lights[direction] = light
            self.grid.place_agent(light, pos)
            self.schedule.add(light)

        # Crear la base y añadirla a la cuadrícula
        self.base = BaseAgent("base", self, self.base_location)
        self.grid.place_agent(self.base, self.base_location)
        self.schedule.add(self.base)

        # Añadir vehículos
        directions = ["north", "east", "west"]
        for i in range(self.num_vehicles):
            direction = random.choice(directions)
            initial_pos = self.get_near_light_spawn_location()[0]
            vehicle = VehicleAgent(f"vehicle_{i}", self, random.randint(1, 10), direction)
            self.grid.place_agent(vehicle, initial_pos)
            self.schedule.add(vehicle)

    def step(self):
        self.update_traffic_lights()
        self.evaporate_pheromones()
        self.schedule.step()
        self.collect_data()

    def update_traffic_lights(self):
        for direction, light in self.traffic_lights.items():
            light.state = "green" if direction == self.current_green else "red"
        self.current_green = {
            "north": "east",
            "east": "south",
            "south": "west",
            "west": "north"
        }[self.current_green]

    def evaporate_pheromones(self):
        evaporation_rate = 0.05
        if self.pheromones:
            for pos in self.pheromones.keys():
                self.pheromones[pos] = max(self.pheromones[pos] * (1 - evaporation_rate), 0)

    def get_near_light_spawn_location(self):
        directions = {
            "north": (self.grid.width // 2, self.grid.height // 2 - 2),
            "east": (self.grid.width // 2 + 2, self.grid.height // 2),
            "west": (self.grid.width // 2 - 2, self.grid.height // 2)
        }
        direction = random.choice(list(directions.keys()))
        return directions[direction], direction

    def record_collision(self, pos):
        if not any(isinstance(agent, CollisionAgent) for agent in self.grid.get_cell_list_contents(pos)):
            self.collisions += 1
            collision = CollisionAgent(f"collision_{pos}", self, pos)
            self.grid.place_agent(collision, pos)
            self.schedule.add(collision)

    def collect_data(self):
        self.steps.append(len(self.steps))
        self.vehicles_data.append(self.vehicles_at_base)
        self.collisions_data.append(self.collisions)

    def report_statistics(self):
        print(f"Vehículos en la base: {self.vehicles_at_base}")
        print(f"Colisiones: {self.collisions}")

# Función para graficar los resultados
def plot_results(steps, vehicles_data, collisions_data):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=steps, y=vehicles_data, mode='lines+markers', name='Vehículos en la Base'))
    fig.add_trace(go.Scatter(x=steps, y=collisions_data, mode='lines+markers', name='Colisiones'))
    fig.update_layout(title="Vehículos en la Base y Colisiones a lo Largo del Tiempo",
                      xaxis_title="Paso de Tiempo",
                      yaxis_title="Cantidad")
    fig.show()

# Configuración de visualización y simulación
def agent_portrayal(agent):
    portrayal = {"Shape": "circle", "Filled": "true", "r": 0.5}
    if isinstance(agent, VehicleAgent):
        portrayal["Color"] = "blue"
        portrayal["Layer"] = 1
    elif isinstance(agent, TrafficLightAgent):
        portrayal["Color"] = "green" if agent.state == "green" else "red"
        portrayal["Layer"] = 0
    elif isinstance(agent, BaseAgent):
        portrayal["Color"] = "purple"
        portrayal["Layer"] = 0
    elif isinstance(agent, CollisionAgent):
        portrayal["Color"] = "red"
        portrayal["Layer"] = 2
    return portrayal

# Parámetros de la simulación
M, N = 10, 10
num_vehicles = 10
grid = CanvasGrid(agent_portrayal, M, N, 500, 500)
server = ModularServer(
    TrafficIntersectionModel,
    [grid],
    "Modelo de Intersección de Tráfico con Comportamiento Malicioso Aleatorio y Seguimiento de Colisiones",
    {"M": M, "N": N, "num_vehicles": num_vehicles}
)

server.port = 8521

if __name__ == "__main__":
    try:
        server.launch()
    except KeyboardInterrupt:
        model = server.model
        plot_results(model.steps, model.vehicles_data, model.collisions_data)
        print("\nSimulación detenida por el usuario.")
