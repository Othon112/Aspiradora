from mesa import Agent, Model
from mesa.time import SimultaneousActivation
from mesa.space import MultiGrid
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
from mesa.datacollection import DataCollector
import random

# Boundary agent class for visualizing grid boundaries
class BoundaryAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

# Car agent class
class CarAgent(Agent):
    def __init__(self, unique_id, model, start_pos, direction):
        super().__init__(unique_id, model)
        self.direction = direction
        self.start_pos = start_pos
        self.happiness = 100  # Initial happiness (0-100 scale)

    def step(self):
        # Determine the position one cell before the traffic light
        if self.direction == "horizontal":
            stop_pos = (self.model.traffic_light_positions[0][0] - 1, self.start_pos[1])
        else:
            stop_pos = (self.start_pos[0], self.model.traffic_light_positions[2][1] - 1)

        # Stop at red light
        light_green = self.model.is_light_green(self.direction)
        if self.pos == stop_pos and not light_green:
            self.happiness -= 1
            return  # Stop if the light is red for this direction
        

        # Move towards the opposite edge and reappear if at the edge
        self.move_and_wrap()
        self.happiness += 0.1

    def move_and_wrap(self):
        x, y = self.pos
        step_size = 1
        if self.direction == "horizontal":
            next_x = x + step_size if x + step_size < self.model.grid.width else (x + step_size) % self.model.grid.width
            next_pos = (next_x, y)
        else:
            next_y = y + step_size if y + step_size < self.model.grid.height else (y + step_size) % self.model.grid.height
            next_pos = (x, next_y)

        # Move to the next position
        self.model.grid.move_agent(self, next_pos)

# Emergency Vehicle agent
class EmergencyVehicleAgent(Agent):
    def __init__(self, unique_id, model, start_pos, direction):
        super().__init__(unique_id, model)
        self.direction = direction
        self.start_pos = start_pos
        self.happiness = 100

    def step(self):
        self.move_and_wrap()
        self.happiness += 0.5

    def move_and_wrap(self):
        x, y = self.pos
        step_size = 2  # Higher speed for emergency vehicles
        if self.direction == "horizontal":
            next_x = x + step_size if x + step_size < self.model.grid.width else (x + step_size) % self.model.grid.width
            next_pos = (next_x, y)
        else:
            next_y = y + step_size if y + step_size < self.model.grid.height else (y + step_size) % self.model.grid.height
            next_pos = (x, next_y)

        # Move regardless of traffic lights
        self.model.grid.move_agent(self, next_pos)

# Public Transport (Bus) agent
class BusAgent(Agent):
    def __init__(self, unique_id, model, start_pos, direction, bus_stops):
        super().__init__(unique_id, model)
        self.direction = direction
        self.start_pos = start_pos
        self.bus_stops = bus_stops  # List of positions where the bus will stop
        self.stop_counter = 0  # Counts steps to simulate a full stop for dropping off/picking up
        self.happiness = 100

    def step(self):
        if self.pos in self.bus_stops:
            # Stop at bus stops for several steps to simulate a full stop for passengers
            if self.stop_counter < 5:
                self.stop_counter += 1
                self.happiness += 1
                return
            else:
                self.stop_counter = 0  # Reset counter after the stop
                self.happiness -= 2

        # Move towards the opposite edge and reappear if at the edge
        self.move_and_wrap()

    def move_and_wrap(self):
        x, y = self.pos
        step_size = 1
        if self.direction == "horizontal":
            next_x = x + step_size if x + step_size < self.model.grid.width else (x + step_size) % self.model.grid.width
            next_pos = (next_x, y)
        else:
            next_y = y + step_size if y + step_size < self.model.grid.height else (y + step_size) % self.model.grid.height
            next_pos = (x, next_y)

        # Move to the next position
        self.model.grid.move_agent(self, next_pos)

# Aggressive Driver agent
class AggressiveDriverAgent(Agent):
    def __init__(self, unique_id, model, start_pos, direction):
        super().__init__(unique_id, model)
        self.direction = direction
        self.start_pos = start_pos
        self.happiness = 100

    def step(self):
        # Determine the position one cell before the traffic light
        if self.direction == "horizontal":
            stop_pos = (self.model.traffic_light_positions[0][0] - 1, self.start_pos[1])
        else:
            stop_pos = (self.start_pos[0], self.model.traffic_light_positions[2][1] - 1)

        # Tends to ignore yellow lights or proceed just as the light turns red
        light_green = self.model.is_light_green(self.direction)
        if self.pos == stop_pos and not light_green and random.random() < 0.8:
            self.happiness +=1
            return  # 80% chance to ignore yellow or proceed quickly


        # Move towards the opposite edge and reappear if at the edge
        self.move_and_wrap()
        self.happiness -= 0.5

    def move_and_wrap(self):
        x, y = self.pos
        step_size = 1
        if self.direction == "horizontal":
            next_x = x + step_size if x + step_size < self.model.grid.width else (x + step_size) % self.model.grid.width
            next_pos = (next_x, y)
        else:
            next_y = y + step_size if y + step_size < self.model.grid.height else (y + step_size) % self.model.grid.height
            next_pos = (x, next_y)

        # Move to the next position
        self.model.grid.move_agent(self, next_pos)

# Traffic light agent class
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

# Main traffic model
class TrafficModel(Model):
    def __init__(self, M, N, light_interval):
        self.grid = MultiGrid(M, N, True)
        self.schedule = SimultaneousActivation(self)
        self.running = True
        self.light_interval = light_interval
        self.step_count = 0

        self.datacollector = DataCollector(
            agent_reporters={"Happiness": lambda a: a.happiness if hasattr(a, "happiness") else None}
        )

        # Define traffic light positions
        self.traffic_light_positions = [
            (M // 2 - 1, N // 2),
            (M // 2 + 1, N // 2),
            (M // 2, N // 2 - 1),
            (M // 2, N // 2 + 1),
        ]
        self.traffic_lights = {}

        # Create traffic lights
        for i, pos in enumerate(self.traffic_light_positions):
            orientation = "horizontal" if i < 2 else "vertical"
            light = TrafficLightAgent(f"light_{i}", self, pos, orientation)
            self.traffic_lights[pos] = light
            self.grid.place_agent(light, pos)
            self.schedule.add(light)

        # Add boundary agents to fill the grid with yellow rectangles
        for x in range(M):
            for y in range(N):
                if (y in range(N // 2 - 2, N // 2 + 3) or x in range(M // 2 - 2, M // 2 + 3)) and (x, y) not in self.traffic_light_positions:
                    continue
                boundary = BoundaryAgent(f"boundary_{x}_{y}", self)
                self.grid.place_agent(boundary, (x, y))

        # Add a regular car
        car_start_pos = (0, N // 2 - 1)
        car = CarAgent("car", self, car_start_pos, "horizontal")
        self.grid.place_agent(car, car_start_pos)
        self.schedule.add(car)

        # Add an emergency vehicle
        emergency_start_pos = (0, N // 2)
        emergency_vehicle = EmergencyVehicleAgent("emergency_vehicle", self, emergency_start_pos, "horizontal")
        self.grid.place_agent(emergency_vehicle, emergency_start_pos)
        self.schedule.add(emergency_vehicle)

        # Add a public transport bus with bus stops
        bus_start_pos = (M // 2, 0)
        bus_stops = [(M // 2, N // 4), (M // 2, 3 * N // 4)]
        bus = BusAgent("bus", self, bus_start_pos, "vertical", bus_stops)
        self.grid.place_agent(bus, bus_start_pos)
        self.schedule.add(bus)

        # Add an aggressive driver
        aggressive_start_pos = (0, N // 2 + 1)
        aggressive_driver = AggressiveDriverAgent("aggressive_driver", self, aggressive_start_pos, "horizontal")
        self.grid.place_agent(aggressive_driver, aggressive_start_pos)
        self.schedule.add(aggressive_driver)

    def is_light_green(self, direction):
        for light in self.traffic_lights.values():
            if light.state == "green" and light.orientation == direction:
                return True
        return False

    def step(self):
        if self.step_count % (2 * self.light_interval) < self.light_interval:
            for pos, light in self.traffic_lights.items():
                if light.orientation == "horizontal":
                    light.turn_green()
                else:
                    light.turn_red()
        else:
            for pos, light in self.traffic_lights.items():
                if light.orientation == "vertical":
                    light.turn_green()
                else:
                    light.turn_red()

        self.step_count += 1
        self.schedule.step()
        # Collect data at each step
        self.datacollector.collect(self)



# Visualization function
def agent_portrayal(agent):
    portrayal = {"Shape": "rect", "Filled": "true", "w": 1, "h": 1}
    if isinstance(agent, BoundaryAgent):
        portrayal["Color"] = "yellow"
        portrayal["Layer"] = 0
    elif isinstance(agent, CarAgent):
        portrayal["Color"] = "blue"
        portrayal["Shape"] = "circle"
        portrayal["r"] = 0.5
        portrayal["Layer"] = 1
        portrayal["text"] = f"{int(agent.happiness)}"
        portrayal["text_color"] = "white"
    elif isinstance(agent, EmergencyVehicleAgent):
        portrayal["Color"] = "red"
        portrayal["Shape"] = "circle"
        portrayal["r"] = 0.7
        portrayal["Layer"] = 2
        portrayal["text"] = f"{int(agent.happiness)}"
        portrayal["text_color"] = "white"
    elif isinstance(agent, BusAgent):
        portrayal["Color"] = "orange"
        portrayal["Shape"] = "rect"
        portrayal["w"] = 1
        portrayal["h"] = 2
        portrayal["Layer"] = 1
        portrayal["text"] = f"{int(agent.happiness)}"
        portrayal["text_color"] = "white"
    elif isinstance(agent, AggressiveDriverAgent):
        portrayal["Color"] = "darkred"
        portrayal["Shape"] = "circle"
        portrayal["r"] = 0.5
        portrayal["Layer"] = 2
        portrayal["text"] = f"{int(agent.happiness)}"
        portrayal["text_color"] = "white"
    elif isinstance(agent, TrafficLightAgent):
        portrayal["Color"] = "green" if agent.state == "green" else "red"
        portrayal["Shape"] = "circle"
        portrayal["r"] = 0.5
        portrayal["Layer"] = 1
    return portrayal

# Simulation parameters
M, N = 15, 15
light_interval = 10
grid = CanvasGrid(agent_portrayal, M, N, 600, 600)
server = ModularServer(TrafficModel, [grid], "Traffic Simulation with Various Vehicles", {"M": M, "N": N, "light_interval": light_interval})
server.port = 8521

if __name__ == "__main__":

    server.launch()
