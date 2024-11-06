from mesa import Agent, Model
from mesa.time import SimultaneousActivation
from mesa.space import MultiGrid
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
import random

class VacuumAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.movements = 0
    
    def step(self):
        # Check if there is dirt in the current cell and clean it
        cell_contents = self.model.grid.get_cell_list_contents([self.pos])
        for obj in cell_contents:
            if isinstance(obj, DirtAgent):
                self.model.grid.remove_agent(obj)
                self.model.clean_cell(self.pos)
        
        # Move randomly to a neighboring cell
        self.random_move()
    
    def random_move(self):
        possible_steps = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
        new_position = self.random.choice(possible_steps)
        
        # Move to the new position without checking if the cell is empty
        self.model.grid.move_agent(self, new_position)
        self.movements += 

class DirtAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

class VacuumModel(Model):
    def __init__(self, M, N, num_agents, dirty_percentage):
        self.num_agents = num_agents
        self.grid = MultiGrid(M, N, True)
        self.schedule = SimultaneousActivation(self)
        self.running = True
        
        # Add vacuum agents
        for i in range(self.num_agents):
            agent = VacuumAgent(i, self)
            self.grid.place_agent(agent, (1, 1))
            self.schedule.add(agent)
        
        # Add dirt agents (representing dirty cells)
        self.dirty_cells = set()
        num_dirty_cells = int(M * N * dirty_percentage)
        for i in range(num_dirty_cells):
            x, y = random.randint(0, M-1), random.randint(0, N-1)
            if (x, y) not in self.dirty_cells:
                dirt = DirtAgent(i + num_agents, self)
                self.grid.place_agent(dirt, (x, y))
                self.dirty_cells.add((x, y))

    def step(self):
        self.schedule.step()

    def clean_cell(self, pos):
        if pos in self.dirty_cells:
            self.dirty_cells.remove(pos)

    def is_cell_dirty(self, pos):
        return pos in self.dirty_cells

def agent_portrayal(agent):
    portrayal = {"Shape": "circle", "Filled": "true", "r": 0.5}
    if isinstance(agent, VacuumAgent):
        portrayal["Color"] = "red"
        portrayal["Layer"] = 1
    elif isinstance(agent, DirtAgent):
        portrayal["Color"] = "grey"
        portrayal["r"] = 0.2
        portrayal["Layer"] = 0
    return portrayal

# Parameters for the model
M, N = 10, 10
num_agents = 1
dirty_percentage = 0.3

# Set up the visualization
grid = CanvasGrid(agent_portrayal, M, N, 500, 500)
server = ModularServer(
    VacuumModel,
    [grid],
    "Vacuum Model",
    {"M": M, "N": N, "num_agents": num_agents, "dirty_percentage": dirty_percentage}
)

server.port = 8521
server.launch()
