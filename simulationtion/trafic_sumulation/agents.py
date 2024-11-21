# agents.py
from mesa import Agent
import random

class BoundaryAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

class CarAgent(Agent):
    def __init__(self, unique_id, model, start_pos, direction):
        super().__init__(unique_id, model)
        self.direction = direction
        self.start_pos = start_pos

    def step(self):
        # Determine the position one cell before the traffic light
        if self.direction == "horizontal":
            stop_pos = (self.model.traffic_light_positions[0][0] - 1, self.start_pos[1])
        else:
            stop_pos = (self.start_pos[0], self.model.traffic_light_positions[2][1] - 1)

        # Stop at red light
        light_green = self.model.is_light_green(self.direction)
        if self.pos == stop_pos and not light_green:
            return  # Stop if the light is red for this direction

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

class EmergencyVehicleAgent(Agent):
    def __init__(self, unique_id, model, start_pos, direction):
        super().__init__(unique_id, model)
        self.direction = direction
        self.start_pos = start_pos

    def step(self):
        self.move_and_wrap()

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

class BusAgent(Agent):
    def __init__(self, unique_id, model, start_pos, direction, bus_stops):
        super().__init__(unique_id, model)
        self.direction = direction
        self.start_pos = start_pos
        self.bus_stops = bus_stops  # List of positions where the bus will stop
        self.stop_counter = 0  # Counts steps to simulate a full stop for dropping off/picking up

    def step(self):
        if self.pos in self.bus_stops:
            # Stop at bus stops for several steps to simulate a full stop for passengers
            if self.stop_counter < 5:
                self.stop_counter += 1
                return
            else:
                self.stop_counter = 0  # Reset counter after the stop

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

class AggressiveDriverAgent(Agent):
    def __init__(self, unique_id, model, start_pos, direction):
        super().__init__(unique_id, model)
        self.direction = direction
        self.start_pos = start_pos

    def step(self):
        # Determine the position one cell before the traffic light
        if self.direction == "horizontal":
            stop_pos = (self.model.traffic_light_positions[0][0] - 1, self.start_pos[1])
        else:
            stop_pos = (self.start_pos[0], self.model.traffic_light_positions[2][1] - 1)

        # Tends to ignore yellow lights or proceed just as the light turns red
        light_green = self.model.is_light_green(self.direction)
        if self.pos == stop_pos and not light_green and random.random() < 0.8:
            return  # 80% chance to ignore yellow or proceed quickly

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
