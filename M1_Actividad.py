from mesa import Agent, Model
from mesa.time import SimultaneousActivation
from mesa.space import MultiGrid
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
import random
from collections import deque

class VacuumAgent(Agent):
    def __init__(self, unique_id, model, behavior="random"):
        super().__init__(unique_id, model)
        self.movements = 0
        self.visited = set()
        self.path_stack = []  # Pila para DFS
        self.queue = deque()  # Cola para BFS
        self.path_stack.append((1, 1))
        self.queue.append((1, 1))
        self.behavior = behavior  # Comportamiento: "random", "DFS", "BFS cambiar en la linea 136"

    def step(self):
        if self.behavior == "random":
            self.random_move()
        elif self.behavior == "DFS":
            self.dfs_move()
        elif self.behavior == "BFS":
            self.bfs_move()

    def random_move(self):
        cell_contents = self.model.grid.get_cell_list_contents([self.pos])
        for obj in cell_contents:
            if isinstance(obj, DirtAgent):
                self.model.grid.remove_agent(obj)
                self.model.clean_cell(self.pos)

        possible_steps = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
        new_position = self.random.choice(possible_steps)
        self.model.grid.move_agent(self, new_position)
        self.movements += 1

    def dfs_move(self):
        if not self.path_stack:
            self.model.running = False
            return

        current_pos = self.path_stack.pop()
        if current_pos not in self.visited:
            self.model.grid.move_agent(self, current_pos)
            self.visited.add(current_pos)
            self.movements += 1

            cell_contents = self.model.grid.get_cell_list_contents([current_pos])
            for obj in cell_contents:
                if isinstance(obj, DirtAgent):
                    self.model.grid.remove_agent(obj)
                    self.model.clean_cell(current_pos)

            neighbors = self.model.grid.get_neighborhood(current_pos, moore=True, include_center=False)
            for neighbor in neighbors:
                if neighbor not in self.visited:
                    self.path_stack.append(neighbor)

    def bfs_move(self):
        if not self.queue:
            self.model.running = False
            return

        current_pos = self.queue.popleft()
        if current_pos not in self.visited:
            self.model.grid.move_agent(self, current_pos)
            self.visited.add(current_pos)
            self.movements += 1

            cell_contents = self.model.grid.get_cell_list_contents([current_pos])
            for obj in cell_contents:
                if isinstance(obj, DirtAgent):
                    self.model.grid.remove_agent(obj)
                    self.model.clean_cell(current_pos)

            neighbors = self.model.grid.get_neighborhood(current_pos, moore=True, include_center=False)
            for neighbor in neighbors:
                if neighbor not in self.visited and neighbor not in self.queue:
                    self.queue.append(neighbor)

class DirtAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

class VacuumModel(Model):
    def __init__(self, M, N, num_agents, dirty_percentage, behavior="random"):
        self.num_agents = num_agents
        self.grid = MultiGrid(M, N, True)
        self.schedule = SimultaneousActivation(self)
        self.running = True
        self.behavior = behavior  # Comportamiento seleccionado

        # Agregar agentes de limpieza
        for i in range(self.num_agents):
            agent = VacuumAgent(i, self, behavior=self.behavior)
            self.grid.place_agent(agent, (1, 1))
            self.schedule.add(agent)

        # Agregar agentes de suciedad
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

M, N = 10, 10
num_agents = 1
dirty_percentage = 0.3
behavior = "BFS"  # Cambiar a "random", "DFS" o "BFS" manualmente

grid = CanvasGrid(agent_portrayal, M, N, 500, 500)
server = ModularServer(
    VacuumModel,
    [grid],
    "Vacuum Model",
    {"M": M, "N": N, "num_agents": num_agents, "dirty_percentage": dirty_percentage, "behavior": behavior}
)

server.port = 8521
server.launch()
