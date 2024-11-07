import mesa
from collections import deque
import matplotlib.pyplot as plt
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
from mesa.datacollection import DataCollector
import numpy as np

class TrashAgent(mesa.Agent):
    """An agent representing trash that can be cleaned."""

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.cleaned = False  
class VacuumAgent(mesa.Agent):
    """An agent representing a vacuum cleaner."""

    def __init__(self, unique_id, model, search_algorithm='bfs'):
        super().__init__(unique_id, model)
        self.path = []  # Path to the target trash
        self.search_algorithm = search_algorithm 
        self.cleaned_count = 0
        self.steps_taken = 0  
    def bfs(self, start_pos):
        """Perform BFS to find the nearest uncleaned trash."""
        queue = deque([(start_pos, [])])
        visited = set()
        while queue:
            current_pos, path = queue.popleft()
            if current_pos in visited:
                continue
            visited.add(current_pos)
            cell_contents = self.model.grid.get_cell_list_contents([current_pos])
            for obj in cell_contents:
                if isinstance(obj, TrashAgent) and not obj.cleaned:
                    return path + [current_pos]  # Path to the trash
            neighbors = self.model.grid.get_neighborhood(
                current_pos, moore=True, include_center=False
            )
            for neighbor in neighbors:
                if neighbor not in visited:
                    queue.append((neighbor, path + [neighbor]))
        return []  # No uncleaned trash found

    def dfs(self, start_pos):
        """Perform DFS to find an uncleaned trash."""
        stack = [(start_pos, [])]
        visited = set()
        while stack:
            current_pos, path = stack.pop()
            if current_pos in visited:
                continue
            visited.add(current_pos)
            cell_contents = self.model.grid.get_cell_list_contents([current_pos])
            for obj in cell_contents:
                if isinstance(obj, TrashAgent) and not obj.cleaned:
                    return path + [current_pos]  # Path to the trash
            neighbors = self.model.grid.get_neighborhood(
                current_pos, moore=True, include_center=False
            )
            for neighbor in neighbors:
                if neighbor not in visited:
                    stack.append((neighbor, path + [neighbor]))
        return []  # No uncleaned trash found

    def move_along_path(self):
        """Move along the precomputed path."""
        if self.path:
            next_pos = self.path.pop(0)
            self.model.grid.move_agent(self, next_pos)
            self.steps_taken += 1

    def step(self):
        """Perform one step: find path to trash, move, and clean."""
        if not self.path:
            if self.search_algorithm == 'bfs':
                self.path = self.bfs(self.pos)
            elif self.search_algorithm == 'dfs':
                self.path = self.dfs(self.pos)
        if self.path:
            self.move_along_path()
            self.clean()

    def clean(self):
        """Clean trash if present in the current cell."""
        cell_contents = self.model.grid.get_cell_list_contents([self.pos])
        for obj in cell_contents:
            if isinstance(obj, TrashAgent) and not obj.cleaned:
                obj.cleaned = True
                self.model.cleaned_trash += 1  # Update cleaned trash count
                self.cleaned_count += 1  # Update agent's cleaned count

class VacuumModel(mesa.Model):
    """A model with vacuum agents and trash."""

    def __init__(self, n_vacuums=5, n_trash=20, width=10, height=10, seed=None, search_algorithm='bfs'):
        super().__init__(seed=seed)
        self.grid = mesa.space.MultiGrid(width, height, True)
        self.schedule = mesa.time.RandomActivation(self)
        self.cleaned_trash = 0  # Count of cleaned trash
        self.total_trash = n_trash  # Total number of trash items

        # Data collector for tracking cleaned trash count and agent performance
        self.datacollector = DataCollector(
            model_reporters={
                "CleanedTrash": lambda m: m.cleaned_trash,
                "RemainingTrash": lambda m: m.total_trash - m.cleaned_trash,
                "AveragePathLength": self.compute_average_path_length
            },
            agent_reporters={
                "CleanedCount": "cleaned_count",
                "StepsTaken": "steps_taken"
            }
        )

        # Create vacuum agents
        for i in range(n_vacuums):
            vacuum = VacuumAgent(i, self, search_algorithm)
            self.schedule.add(vacuum)
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(vacuum, (x, y))

        # Create trash agents
        for i in range(n_vacuums, n_vacuums + n_trash):
            trash = TrashAgent(i, self)
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(trash, (x, y))

    def compute_average_path_length(self):
        """Compute the average path length taken by agents to clean trash."""
        total_steps = sum(agent.steps_taken for agent in self.schedule.agents if isinstance(agent, VacuumAgent))
        total_cleaned = sum(agent.cleaned_count for agent in self.schedule.agents if isinstance(agent, VacuumAgent))
        return total_steps / total_cleaned if total_cleaned > 0 else 0

    def step(self):
        """Run one step of the model."""
        self.schedule.step()
        self.datacollector.collect(self)

    def run_model(self, step_count=100):
        """Run the model for a specified number of steps."""
        for _ in range(step_count):
            self.step()

def agent_portrayal(agent):
    if isinstance(agent, VacuumAgent):
        return {"Shape": "circle", "Color": "blue", "Filled": True, "Layer": 1, "r": 0.5}
    elif isinstance(agent, TrashAgent):
        color = "red" if not agent.cleaned else "green"
        return {"Shape": "rect", "Color": color, "Filled": True, "Layer": 0, "w": 0.5, "h": 0.5}

# Visualization setup (optional)
grid = CanvasGrid(agent_portrayal, 10, 10, 500, 500)
server = ModularServer(
    VacuumModel,
    [grid],
    "Vacuum Cleaning Model",
    {"n_vacuums": 3, "n_trash": 10, "width": 10, "height": 10, "search_algorithm": 'bfs'}
)


if __name__ == "__main__":
    # Run the model using BFS
    model_bfs = VacuumModel(n_vacuums=3, n_trash=20, width=10, height=10, search_algorithm='bfs')
    model_bfs.run_model(step_count=50)

    # Retrieve and plot data for BFS
    data_bfs = model_bfs.datacollector.get_model_vars_dataframe()

    # Run the model using DFS
    model_dfs = VacuumModel(n_vacuums=3, n_trash=20, width=10, height=10, search_algorithm='dfs')
    model_dfs.run_model(step_count=50)

    # Retrieve and plot data for DFS
    data_dfs = model_dfs.datacollector.get_model_vars_dataframe()

    # Plotting the results
    plt.figure(figsize=(10, 6))
    plt.plot(data_bfs.index, data_bfs['CleanedTrash'], label='BFS')
    plt.plot(data_dfs.index, data_dfs['CleanedTrash'], label='DFS')
    plt.xlabel('Step')
    plt.ylabel('Number of Cleaned Trash')
    plt.title('Performance of Vacuum Agents Over Time')
    plt.legend()
    plt.grid(True)
    plt.show()
