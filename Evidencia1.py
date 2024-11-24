from mesa import Agent, Model
from mesa.time import SimultaneousActivation
from mesa.space import MultiGrid
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
import random

# Boundary agent class for visualizing grid boundaries and map elements
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
        self.state = "happy"

    def step(self):
        if self.happiness > 80:
            self.state = "happy"
        elif self.happiness < 50:
            self.state = "angry"

        # Behavior based on state
        if self.state == "happy":
            self.happiness += 0.2  # Gain happiness slightly
        elif self.state == "angry":
            self.happiness -= 0.5  # Lose happiness more rapidly

        # Stop at red light
        light_green = self.model.is_light_green(self.direction)
        if self.at_traffic_light() and not light_green:
            self.happiness -= 1 if self.state == "happy" else 2
            return  # Stop if the light is red for this direction

        # Move and wrap
        self.move_and_wrap()
        self.happiness += 0.1

    def at_traffic_light(self):
        return self.pos in self.model.traffic_light_positions

    def move_and_wrap(self):
        x, y = self.pos
        step_size = 1 if self.state == "happy" else 2  # Angry drivers move faster
        if self.direction == "horizontal":
            next_x = (x + step_size) % self.model.grid.width
            next_pos = (next_x, y)
        else:
            next_y = (y + step_size) % self.model.grid.height
            next_pos = (x, next_y)
        # Check if next position is not a boundary
        if not self.model.grid.is_cell_empty(next_pos):
            contents = self.model.grid.get_cell_list_contents([next_pos])
            for obj in contents:
                if isinstance(obj, BoundaryAgent):
                    return  # Can't move into boundaries
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
            next_x = (x + step_size) % self.model.grid.width
            next_pos = (next_x, y)
        else:
            next_y = (y + step_size) % self.model.grid.height
            next_pos = (x, next_y)
        # Emergency vehicles ignore boundaries
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
            next_x = (x + step_size) % self.model.grid.width
            next_pos = (next_x, y)
        else:
            next_y = (y + step_size) % self.model.grid.height
            next_pos = (x, next_y)
        # Check for boundaries
        if not self.model.grid.is_cell_empty(next_pos):
            contents = self.model.grid.get_cell_list_contents([next_pos])
            for obj in contents:
                if isinstance(obj, BoundaryAgent):
                    return  # Can't move into boundaries
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
        # Tends to ignore red lights
        if self.at_traffic_light() and random.random() < 0.8:
            self.happiness += 1
            return  # 80% chance to ignore the red light

        # Move towards the opposite edge and reappear if at the edge
        self.move_and_wrap()
        self.happiness -= 0.5

    def at_traffic_light(self):
        return self.pos in self.model.traffic_light_positions

    def move_and_wrap(self):
        x, y = self.pos
        step_size = 2  # Aggressive drivers move faster
        if self.direction == "horizontal":
            next_x = (x + step_size) % self.model.grid.width
            next_pos = (next_x, y)
        else:
            next_y = (y + step_size) % self.model.grid.height
            next_pos = (x, next_y)
        # Check for boundaries
        if not self.model.grid.is_cell_empty(next_pos):
            contents = self.model.grid.get_cell_list_contents([next_pos])
            for obj in contents:
                if isinstance(obj, BoundaryAgent):
                    return  # Can't move into boundaries
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

    def step(self):
        pass  # Traffic lights are controlled by the model's step

# Main traffic model
class TrafficModel(Model):
    def __init__(self, M, N, light_interval):
        self.grid = MultiGrid(M, N, torus=False)  # Set torus to False to prevent wrapping
        self.schedule = SimultaneousActivation(self)
        self.running = True
        self.light_interval = light_interval
        self.step_count = 0

        # Define traffic light positions (according to the image)
        self.traffic_light_positions = [
            (5, 0), (5, 1), #horizontal
            (6, 2), (7, 2), #vertical

            (0, 6), (1,6), #vertical
            (2, 4), (2,5), #horizontal

            (18, 7), (19,7), #vertical
            (17, 8), (17, 9), #horizontal

            (6, 16), (7, 16), #horizontal
            (8, 17), (8, 18), #vertical

            (6, 21), (7, 21), #vertical
            (8, 22), (8, 23), #horizontal

        ]
        self.traffic_lights = {}

        # Create traffic lights
        for i, pos in enumerate(self.traffic_light_positions):
            # Define the orientation based on specific positions
            if pos in [(5, 0), (5, 1), (2, 4), (2, 5), (8, 22), (8, 23), (17, 8), (17, 9), (8, 17), (8, 18)]:
                orientation = "horizontal"
            elif pos in [(6, 2), (7, 2), (0, 6), (1, 6), (18, 7), (19, 7), (6, 21), (7, 21), (8, 17), (8, 18), (6, 16), (7, 16)]:
                orientation = "vertical"
            else:
                raise ValueError(f"Position {pos} does not have a defined orientation.")
            
            # Create and add the traffic light agent
            light = TrafficLightAgent(f"light_{i}", self, pos, orientation)
            self.traffic_lights[pos] = light
            self.grid.place_agent(light, pos)
            self.schedule.add(light)

        # Add boundary agents for buildings, parking lots, medians, and roundabout

        # Buildings (blue areas)
        building_positions = [
            [(x, y) for x in range(2, 6) for y in range(2, 3)],
            [(x, y) for x in range(2, 4) for y in range(3, 4)],
            [(x, y) for x in range(5, 6) for y in range(3, 4)],

            [(x, y) for x in range(2, 3) for y in range(6, 8)],
            [(x, y) for x in range(3, 6) for y in range(7, 8)],
            [(x, y) for x in range(4, 6) for y in range(6, 7)],

            [(x, y) for x in range(8, 9) for y in range(2, 4)],
            [(x, y) for x in range(9, 12) for y in range(3, 4)],
            [(x, y) for x in range(10, 12) for y in range(2, 3)],

            [(x, y) for x in range(8, 12) for y in range(6, 7)],
            [(x, y) for x in range(8, 10) for y in range(7, 8)],
            [(x, y) for x in range(11, 12) for y in range(7, 8)],

            [(x, y) for x in range(16, 18) for y in range(2, 4)],
            [(x, y) for x in range(16, 17) for y in range(4, 8)],
            [(x, y) for x in range(17, 18) for y in range(5, 6)],
            [(x, y) for x in range(17, 18) for y in range(7, 8)],

            [(x, y) for x in range(20, 22) for y in range(2, 4)],
            [(x, y) for x in range(21, 22) for y in range(4, 5)],
            [(x, y) for x in range(20, 22) for y in range(5, 8)],

            [(x, y) for x in range(2, 4) for y in range(12, 14)],
            [(x, y) for x in range(5, 6) for y in range(12, 13)],
            [(x, y) for x in range(4,6) for y in range(13, 17)],
            [(x, y) for x in range(2,4) for y in range(15, 21)],
            [(x, y) for x in range(2,3 ) for y in range(21,22)],
            [(x, y) for x in range(4,6 ) for y in range(18, 22)],
            [(x, y) for x in range(3, 4) for y in range(14, 15)],
            [(x, y) for x in range(4,5 ) for y in range(17,18 )],

            [(x, y) for x in range(8, 10) for y in range(12, 15)],
            [(x, y) for x in range(10, 12) for y in range(13, 17)],
            [(x, y) for x in range(11, 12) for y in range(12, 13)],
            [(x, y) for x in range(9, 10) for y in range(15, 17)],
            [(x, y) for x in range(8, 9) for y in range(16, 17)],

            [(x, y) for x in range(8, 10) for y in range(19, 22)],
            [(x, y) for x in range(10, 12) for y in range(20, 22)],
            [(x, y) for x in range(11, 12) for y in range(19, 20)],

            [(x, y) for x in range(16, 20) for y in range(18, 21)],
            [(x, y) for x in range(16,17 ) for y in range(21, 22)],
            [(x, y) for x in range(18, 22) for y in range(21, 22)],
            [(x, y) for x in range(21, 22 ) for y in range(18, 21)],
            [(x, y) for x in range(20, 21 ) for y in range(19, 21)],

            [(x, y) for x in range(16, 20 ) for y in range(12, 16)],
            [(x, y) for x in range(21, 22) for y in range(12, 16 )],
            [(x, y) for x in range(20, 21 ) for y in range(12, 15)],
        ]
        for idx, positions in enumerate(building_positions):
            for pos in positions:
                boundary = BoundaryAgent(f"building_{idx}_{pos[0]}_{pos[1]}", self)
                self.grid.place_agent(boundary, pos)

        # Parking lots (yellow areas)
        parking_lots = [
            (2,14), (3,21), (3, 6), (4,12), (4,3), (5,17), (8, 15), (9,2), (10, 19), (10,12),  (10,7), (17, 21), (17,6), (17, 4), (20,18), (20,15), (20,4)
        ]
        for idx, lot in enumerate(parking_lots):
            boundary = BoundaryAgent(f"parking_{idx}_{lot[0]}_{lot[1]}", self)
            self.grid.place_agent(boundary, lot)

        # Roundabout (brown area at center)
        roundabout_positions = [
            (14, 10), (13,10),
            (14,9), (13,9),
        ]
        for idx, pos in enumerate(roundabout_positions):
            boundary = BoundaryAgent(f"roundabout_{idx}_{pos[0]}_{pos[1]}", self)
            self.grid.place_agent(boundary, pos)

        # Add multiple regular cars
        car_start_positions = [
            (0, 1)  # Left to right and right to left
              # Top to bottom and bottom to top
        ]
        for i, start_pos in enumerate(car_start_positions):
            direction = "horizontal" if start_pos[1] in [11, 12] else "vertical"
            car = CarAgent(f"car_{i}", self, start_pos, direction)
            self.grid.place_agent(car, start_pos)
            self.schedule.add(car)

        # Add emergency vehicles
        emergency_start_positions = [
            
        ]
        for i, start_pos in enumerate(emergency_start_positions):
            direction = "horizontal" if start_pos[1] in [10, 13] else "vertical"
            emergency_vehicle = EmergencyVehicleAgent(f"emergency_vehicle_{i}", self, start_pos, direction)
            self.grid.place_agent(emergency_vehicle, start_pos)
            self.schedule.add(emergency_vehicle)

        # Add public buses
        bus_stops = [(9, 5), (14, 5), (9, 18), (14, 18)]
        bus_start_positions = [
           
        ]
        for i, start_pos in enumerate(bus_start_positions):
            direction = "vertical"
            bus = BusAgent(f"bus_{i}", self, start_pos, direction, bus_stops)
            self.grid.place_agent(bus, start_pos)
            self.schedule.add(bus)

        # Add aggressive drivers
        aggressive_start_positions = [
            
        ]
        for i, start_pos in enumerate(aggressive_start_positions):
            direction = "horizontal" if start_pos[1] in [11, 12] else "vertical"
            aggressive_driver = AggressiveDriverAgent(f"aggressive_driver_{i}", self, start_pos, direction)
            self.grid.place_agent(aggressive_driver, start_pos)
            self.schedule.add(aggressive_driver)

    def is_light_green(self, direction):
        for light in self.traffic_lights.values():
            if light.state == "green" and light.orientation == direction:
                return True
        return False

    def step(self):
        # Control traffic lights
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

# Visualization function
def agent_portrayal(agent):
    portrayal = {}
    if isinstance(agent, BoundaryAgent):
        if "building" in agent.unique_id:
            portrayal = {
                "Shape": "rect",
                "Filled": "true",
                "Layer": 0,
                "Color": "blue",  
                "w": 1,
                "h": 1,
            }
        elif "roundabout" in agent.unique_id:
            portrayal = {
                "Shape": "rect",
                "Filled": "true",
                "Layer": 0,
                "Color": "brown",  
                "w": 1,
                "h": 1,
            }
        elif "parking" in agent.unique_id:
            portrayal = {
                "Shape": "rect",
                "Filled": "true",
                "Layer": 0,
                "Color": "yellow",  
                "w": 1,
                "h": 1,
            }

        else:
            portrayal = {
                "Shape": "rect",
                "Filled": "true",
                "Layer": 0,
                "Color": "gray",  # Color for other boundaries
                "w": 1,
                "h": 1,
            }
    elif isinstance(agent, CarAgent):
        portrayal = {
            "Shape": "circle",
            "Filled": "true",
            "Layer": 1,
            "Color": "blue" if agent.state == "happy" else "red",
            "r": 0.5,
            "text": f"{int(agent.happiness)}",
            "text_color": "white",
        }
    elif isinstance(agent, EmergencyVehicleAgent):
        portrayal = {
            "Shape": "circle",
            "Filled": "true",
            "Layer": 2,
            "Color": "red",
            "r": 0.7,
            "text": f"{int(agent.happiness)}",
            "text_color": "white",
        }
    elif isinstance(agent, BusAgent):
        portrayal = {
            "Shape": "rect",
            "Filled": "true",
            "Layer": 1,
            "Color": "orange",
            "w": 1,
            "h": 1,
            "text": f"{int(agent.happiness)}",
            "text_color": "white",
        }
    elif isinstance(agent, AggressiveDriverAgent):
        portrayal = {
            "Shape": "circle",
            "Filled": "true",
            "Layer": 2,
            "Color": "darkred",
            "r": 0.5,
            "text": f"{int(agent.happiness)}",
            "text_color": "white",
        }
    elif isinstance(agent, TrafficLightAgent):
        portrayal = {
            "Shape": "circle",
            "Filled": "true",
            "Layer": 1,
            "Color": "green" if agent.state == "green" else "red",
            "r": 0.5,
        }
    return portrayal

# Simulation parameters
M, N = 24, 24
light_interval = 10

grid = CanvasGrid(agent_portrayal, M, N, 600, 600)
server = ModularServer(
    TrafficModel,
    [grid],
    "Traffic Simulation with Various Vehicles",
    {
        "M": M,
        "N": N,
        "light_interval": light_interval,
    },
)

server.port = 8521

if __name__ == "__main__":
    server.launch()
