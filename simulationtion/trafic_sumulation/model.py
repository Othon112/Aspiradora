# model.py
from mesa import Model
from mesa.time import SimultaneousActivation
from mesa.space import MultiGrid
from agents import (
    BoundaryAgent, CarAgent, EmergencyVehicleAgent, 
    BusAgent, AggressiveDriverAgent, TrafficLightAgent
)

class TrafficModel(Model):
    def __init__(self, M, N, light_interval):
        self.grid = MultiGrid(M, N, True)
        self.schedule = SimultaneousActivation(self)
        self.running = True
        self.light_interval = light_interval
        self.step_count = 0

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