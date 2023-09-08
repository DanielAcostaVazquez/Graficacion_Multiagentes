# Se importan los componentes necesarios para la simulación
from mesa import Agent, Model
from mesa.space import MultiGrid
from mesa.time import RandomActivation
from mesa.visualization.UserParam import Slider
from mesa.visualization.UserParam import Checkbox
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
from mesa.datacollection import DataCollector
from mesa.visualization.modules import ChartModule


# Clase para representar los árboles en la simulación
class Tree(Agent):
    # Definir las posibles condiciones para un árbol
    FINE = 0
    BURNING = 1
    BURNED_OUT = 2

    # Inicializar el agente Árbol
    def __init__(
        self,
        model: Model,
        probability_of_spread,
        south_wind_speed,
        west_wind_speed,
        big_jumps,
    ):
        super().__init__(model.next_id(), model)
        self.condition = self.FINE
        self.probability_of_spread = probability_of_spread
        self.south_wind_speed = south_wind_speed
        self.west_wind_speed = west_wind_speed
        self.big_jumps = big_jumps

    # Definir el comportamiento del agente Árbol en cada paso de la simulación
    def step(self):
        if self.condition == self.BURNING:
            # Se propaga el fuego a los árboles cercanos que estén bien y en donde el valor random sea menor que probability_of_spread
            for neighbor in self.model.grid.iter_neighbors(
                self.pos, moore=False
            ):
                # árbol izquierdo

                if self.pos[0] > neighbor.pos[0]:
                    if self.west_wind_speed <= 0:
                        total_probability = self.probability_of_spread + abs(
                            self.west_wind_speed
                        )
                    else:
                        total_probability = 0
                # árbol derecho
                elif self.pos[0] < neighbor.pos[0]:
                    if self.west_wind_speed >= 0:
                        total_probability = self.probability_of_spread + abs(
                            self.west_wind_speed
                        )
                    else:
                        total_probability = 0
                # árbol norte
                elif self.pos[1] < neighbor.pos[1]:
                    if self.south_wind_speed >= 0:
                        total_probability = self.probability_of_spread + abs(
                            self.south_wind_speed
                        )
                    else:
                        total_probability = 0
                # árbol sur
                elif self.pos[1] > neighbor.pos[1]:
                    if self.south_wind_speed <= 0:
                        total_probability = self.probability_of_spread + abs(
                            self.south_wind_speed
                        )
                    else:
                        total_probability = 0

                if (
                    neighbor.condition == self.FINE
                    and self.random.randint(0, 100) < total_probability
                ):
                    neighbor.condition = self.BURNING
            if self.big_jumps:
                x = self.pos[0] + self.west_wind_speed // 8
                y = self.pos[1] + self.south_wind_speed // 8
                if not (self.model.grid.out_of_bounds((x, y))) and not (
                    self.model.grid.is_cell_empty((x, y))
                ):
                    big_jump_tree = self.model.grid.get_neighbors(
                        (x, y), include_center=True, radius=0, moore=False
                    )[0]
                    if (
                        big_jump_tree.condition == self.FINE
                        and self.random.randint(0, 100) < self.probability_of_spread
                    ):
                        big_jump_tree.condition = self.BURNING

            # Establecer el estado del árbol actual como quemado después de propagar el fuego
            self.condition = self.BURNED_OUT


# Clase para representar el ambiente de la simulación (bosque)
class Forest(Model):
    # Inicializar el modelo Bosque con los parámetros dados
    def __init__(
        self,
        height=50,
        width=50,
        density=0.60,
        probability_of_spread=69,
        south_wind_speed=0,
        west_wind_speed=0,
        big_jumps=True,
    ):
        super().__init__()
        self.schedule = RandomActivation(self)
        self.grid = MultiGrid(height, width, torus=False)
        # Se crean árboles según la densidad especificada
        for _, pos in self.grid.coord_iter():
            x, y = pos
            # Se crean árboles según la densidad
            if self.random.random() < density:
                tree = Tree(
                    self,
                    probability_of_spread,
                    south_wind_speed,
                    west_wind_speed,
                    big_jumps,
                )
                # Se comienza el incendio con los árboles del extremo izquierdo
                if x == 0:
                    tree.condition = Tree.BURNING
                self.grid.place_agent(tree, (x, y))
                self.schedule.add(tree)
        self.datacollector = DataCollector(
            {
                "Percent burned": lambda m: self.count_type(m, Tree.BURNED_OUT)
                / len(self.schedule.agents)
            }
        )

    def step(self):
        self.schedule.step()
        self.datacollector.collect(self)
        if self.schedule.steps == 50:
            self.running = False

    def count_type(_, model, condition):
        count = 0
        for tree in model.schedule.agents:
            if tree.condition == condition:
                count += 1
        return count


# Se definen los posibles estados de los árboles, dando a cada estado un color diferente
def agent_portrayal(agent):
    if agent.condition == Tree.FINE:
        portrayal = {
            "Shape": "circle",
            "Filled": "true",
            "Color": "Green",
            "r": 0.75,
            "Layer": 0,
        }
    elif agent.condition == Tree.BURNING:
        portrayal = {
            "Shape": "circle",
            "Filled": "true",
            "Color": "Red",
            "r": 0.75,
            "Layer": 0,
        }
    elif agent.condition == Tree.BURNED_OUT:
        portrayal = {
            "Shape": "circle",
            "Filled": "true",
            "Color": "Gray",
            "r": 0.75,
            "Layer": 0,
        }
    else:
        portrayal = {}

    return portrayal


# Se crea la malla
grid = CanvasGrid(agent_portrayal, 50, 50, 450, 450)
# Se crea la Gráfica
chart = ChartModule(
    [{"Label": "Percent burned", "Color": "Black"}], data_collector_name="datacollector"
)
# Se define el servidor junto a 2 Sliders para controlar la densidad y probability_of_spread
server = ModularServer(
    Forest,
    [grid, chart],
    "Forest",
    {
        "density": Slider("Tree density", 0.45, 0.01, 1.0, 0.01),
        "probability_of_spread": Slider("Probability of Spread", 69, 0, 100, 1),
        "south_wind_speed": Slider("South Wind Speed", 0, -25, 25, 1),
        "west_wind_speed": Slider("West Wind Speed", 0, -25, 25, 1),
        "big_jumps": Checkbox("Big Jump", False),
        "width": 50,
        "height": 50,
    },
)

server.port = 8522
server.launch()
