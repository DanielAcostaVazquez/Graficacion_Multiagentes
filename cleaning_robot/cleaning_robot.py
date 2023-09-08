from mesa import Agent, Model
from mesa.space import MultiGrid
from mesa.time import RandomActivation
from mesa.visualization.UserParam import Slider, Checkbox
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
from RobotCorner import RobotCorner
from RobotCenter import RobotCenter
from Incinerator import Incinerator
from GarbageCell import GarbageCell
from mesa.datacollection import DataCollector
from mesa.visualization.modules import ChartModule


class Room(Model):
    def __init__(self, density=0.01, grid51=True, centerPercentage=0.21):
        super().__init__()
        self.schedule = RandomActivation(self)
        grid_size = 51 if grid51 else 21  # Se define el tamaño de la malla

        center_radius = int(
            grid_size * centerPercentage
        )  # Se define el radio de la malla central
        if (grid_size // 2 - center_radius) % 2 != 0:
            center_radius -= 1  # Se asegura que el tamaño de la malla central no obstruya el camino de los RobotCorner

        self.grid = MultiGrid(grid_size, grid_size, torus=False)
        self.count = 0
        # Se genera la basura conforme a la densidad
        for _, pos in self.grid.coord_iter():
            x, y = pos
            if self.random.random() < density:
                self.count += 1
                garbageCell = GarbageCell(self)
                self.grid.place_agent(garbageCell, (x, y))
                self.schedule.add(garbageCell)

        # Se calculan las coordenadas de las esquinas de la malla central para su uso posterior
        c_coords = [
            (grid_size // 2 - center_radius, grid_size // 2 - center_radius),  # I.I
            (grid_size // 2 - center_radius, grid_size // 2 + center_radius),  # S.I
            (grid_size // 2 + center_radius, grid_size // 2 + center_radius),  # S.D
            (grid_size // 2 + center_radius, grid_size // 2 - center_radius),  # I.D
        ]

        # Se dibujan los bordes de la malla central
        # self.drawCenter(center_radius, c_coords)

        # Se crea el incinerador en la mitad de la malla
        incinerator = Incinerator(self)
        self.grid.place_agent(incinerator, (grid_size // 2, grid_size // 2))
        self.schedule.add(incinerator)

        # Se crean los robots de las esquinas
        robots = []
        robots.append(RobotCorner(self, grid_size, c_coords, 0, (0, 0)))
        robots.append(RobotCorner(self, grid_size, c_coords, 1, (0, grid_size - 1)))
        robots.append(
            RobotCorner(self, grid_size, c_coords, 2, (grid_size - 1, grid_size - 1))
        )
        robots.append(RobotCorner(self, grid_size, c_coords, 3, (grid_size - 1, 0)))

        # Se crean los robots del centro
        robots.append(
            RobotCenter(self, grid_size, c_coords, 0, c_coords[1], incinerator)
        )
        robots.append(
            RobotCenter(self, grid_size, c_coords, 1, c_coords[3], incinerator)
        )

        # Ciclo para posicionar robots en malla
        for r in robots:
            self.grid.place_agent(r, r.pos)
            self.schedule.add(r)
            
        self.datacollector = DataCollector(
           {"Garbage Cleaned": lambda m: (self.count_type(m, True) / self.count)*100}
           )

    def step(self):
        self.schedule.step()
        self.datacollector.collect(self)
        
    def count_type(_, model, condition):
      count = 0
      for agent in model.schedule.agents:
         if isinstance(agent, GarbageCell):       
            if agent.burned == condition:
                  count += 1
         print(count)
      return count

    # Función de uso opcional, permite visualizar el borde de la malla central
    def drawCenter(self, center_radius, c_coords):
        for i in range(center_radius * 2):
            garbageCell = GarbageCell(self)
            coord = list(c_coords[0])
            coord[1] += i
            self.grid.place_agent(garbageCell, coord)

        for i in range(center_radius * 2):
            garbageCell = GarbageCell(self)
            coord = list(c_coords[1])
            coord[0] += i
            self.grid.place_agent(garbageCell, coord)

        for i in range(center_radius * 2):
            garbageCell = GarbageCell(self)
            coord = list(c_coords[2])
            coord[1] -= i
            self.grid.place_agent(garbageCell, coord)

        for i in range(center_radius * 2):
            garbageCell = GarbageCell(self)
            coord = list(c_coords[3])
            coord[0] -= i
            self.grid.place_agent(garbageCell, coord)


def agent_portrayal(agent):
    if type(agent) == RobotCorner:
        portrayal = {
            "Shape": "rect",
            "w": 1,
            "h": 1,
            "Filled": "true",
            "Color": "Blue",
            "Layer": 0,
        }
    elif type(agent) == RobotCenter:
        portrayal = {
            "Shape": "rect",
            "w": 1,
            "h": 1,
            "Filled": "true",
            "Color": "Purple",
            "Layer": 0,
        }
    elif type(agent) == Incinerator and not agent.on:
        portrayal = {
            "Shape": "rect",
            "w": 1,
            "h": 1,
            "Filled": "true",
            "Color": "Orange",
            "Layer": 0,
        }
    elif type(agent) == Incinerator and agent.on:
      portrayal = {
         "Shape": "rect",
         "w": 1,
         "h": 1,
         "Filled": "true",
         "Color": "Red",
         "Layer": 0,
      }
    elif type(agent) == GarbageCell and agent.dirty and not agent.burned:
        portrayal = {
            "Shape": "circle",
            "Filled": "true",
            "Color": "Black",
            "r": 0.75,
            "Layer": 0,
        }
    elif type(agent) == GarbageCell and not agent.dirty:
        portrayal = {
            "Shape": "circle",
            "Filled": "true",
            "Color": "white",
            "r": 0.75,
            "Layer": 0,
        }
    else:
        portrayal = {}
    return portrayal

chart = ChartModule(
    [{"Label": "Garbage Cleaned", "Color": "Black"}], data_collector_name="datacollector"
)
grid = CanvasGrid(agent_portrayal, 51, 51, 460, 460)


server = ModularServer(
    Room,
    [grid, chart],
    "Room",
    {
        "density": Slider("GarbageCell density", 0.01, 0.01, 1.0, 0.01),
        "centerPercentage": Slider("Center Grid Size", 0.20, 0.01, 0.50, 0.01),
        "grid51": Checkbox("51 x 51 grid", True),
    },
)
server.port = 8522
server.launch()
