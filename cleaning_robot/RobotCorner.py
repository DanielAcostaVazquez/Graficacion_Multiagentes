from mesa import Agent
from Incinerator import Incinerator
from GarbageCell import GarbageCell


class RobotCorner(Agent):
    def __init__(self, model, grid_size, c_coords, section, pos):
        super().__init__(model.next_id(), model)
        self.model = model
        self.loaded = (
            False  # Variable para identificar si el robot está cargando basura
        )
        self.currGarbage = False
        self.returning = False  # Variable para identificar si el robot está regresando
        self.delivering = False
        self.lastPos = (0, 0)
        self.grid_size = grid_size  # Tamaño de la malla
        self.direction = (
            1 if section == 0 or section == 3 else -1
        )  # Dirección del robot en el eje Y
        self.dropDirection = (
            1 if section == 0 or section == 3 else -1
        )  # Dirección del robot en el eje Y en cuadro central
        self.pos = pos  # posición actual

        # limits representa los 4 límites del área de dicho robot, hay 2 conjuntos de límites, x1,y1 & x2,y2
        # por cada sección se definen sus límites de malla original y malla central
        if section == 0:
            self.limits = (grid_size // 2 - 1, grid_size // 2 - 1, 0, 0)
            self.c_coords = c_coords[0]
            self.c_coordsLimit = c_coords[1]
        elif section == 1:
            self.limits = (grid_size // 2, grid_size // 2, 0, grid_size - 1)
            self.c_coords = c_coords[1]
            self.c_coordsLimit = c_coords[0]
        elif section == 2:
            self.limits = (
                grid_size // 2 + 1,
                grid_size // 2 + 1,
                grid_size - 1,
                grid_size - 1,
            )
            self.c_coords = c_coords[2]
            self.c_coordsLimit = c_coords[3]
        else:
            self.limits = (grid_size // 2, grid_size // 2, grid_size - 1, 0)
            self.c_coords = c_coords[3]
            self.c_coordsLimit = c_coords[2]

        # section indica en que sección de la malla está el robot:
        # 0: inferior izquierda
        # 1: superior izquierda
        # 2: superior derecha
        # 3: inferior derecha
        self.section = section


    # Regresa a la posición de búsqueda
    # Regresa una lista next_move
    def ret(self):
        # Alinear en x
        next_move = list(self.pos)
        if self.pos[0] != self.lastPos[0]:
            if self.pos[0] < self.lastPos[0]:
                next_move[0] += 1
            else:
                next_move[0] -= 1
        else:
            self.pos
        # Alinear en y
        if self.pos[1] != self.lastPos[1]:
            if self.pos[1] < self.lastPos[1]:
                next_move[1] += 1
            else:
                next_move[1] -= 1
        if tuple(next_move) == self.lastPos:
            self.returning = False
        return next_move

    # Busca un lugar vacío para dejar la basura en el centro
    # Regresa una lista next_move
    def drop(self):
        curCell = self.model.grid.get_neighbors(
            (self.pos), include_center=True, radius=0, moore=False
        )
        curGarbage = 0
        for agent in curCell:
            if isinstance(agent, GarbageCell):
                curGarbage = agent
        next_move = list(self.pos)
        if not curGarbage or not curGarbage.dirty:
            self.currGarbage.drop(self.pos)
            self.currGarbage = 0
            self.returning = True
            self.loaded = False
        else:
            if (
                self.pos[1] + self.dropDirection == self.c_coordsLimit[1]
                or self.pos[1] + self.dropDirection == self.c_coords[1]
            ):
                self.dropDirection *= -1
            next_move[1] += self.dropDirection
        return next_move

    # Entrega de basura en el centro
    # Regresa una lista next_move
    def deliver(self):
        # Alinear en x
        next_move = list(self.pos)
        if self.pos[0] != self.c_coords[0]:
            if self.pos[0] < self.c_coords[0]:
                next_move[0] += 1
            else:
                next_move[0] -= 1
        else:
            self.pos
        # Alinear en y
        if self.pos[1] != self.c_coords[1]:
            if self.pos[1] < self.c_coords[1]:
                next_move[1] += 1
            else:
                next_move[1] -= 1
        if tuple(next_move) == self.c_coords:
            self.delivering = False
        return next_move

    # Barrido de los cuadrantes externos
    # Regresa una lista next_move
    def search(self):
        curCell = self.model.grid.get_neighbors(
            (self.pos), include_center=True, radius=0, moore=False
        )
        for agent in curCell:
            if isinstance(agent, GarbageCell):
                self.currGarbage = agent
        # Se verifica si el robot encontró basura
        if self.currGarbage:
            print("Se encontró basura")
            self.currGarbage.pickUp()
            self.loaded = True
            self.delivering = True
            self.lastPos = self.pos
        # Se checa si el robot ha llegado a un borde de la malla central
        if self.pos[0] == self.c_coords[0]:
            # Se intercambian los límites del eje Y al robot para tomar en cuenta el borde de la malla central
            limits = list(self.limits)
            limits[1] = (
                self.c_coords[1] - 1
                if self.section == 0 or self.section == 3
                else self.c_coords[1] + 1
            )
            self.limits = tuple(limits)

        dir, sect = self.direction, self.section
        # Se checa si el robot ha barrido su sección por completo
        if sect == 0 or sect == 2:
            i = 1 if abs(self.limits[0] - self.limits[2]) % 2 == 0 else 3
            if self.pos == (self.limits[0], self.limits[i]):
                return self.pos
        else:
            i = 1 if abs(self.limits[0] - self.limits[2]) % 2 == 0 else 3
            if self.pos == (self.limits[0], self.limits[i]):
                return self.pos

        # Se posicionan incineradoes como ejemplo visual del recorrido de los robots
        # self.model.grid.place_agent(Incinerator(self.model), self.pos)

        # Se escoge el límite del eje Y a utilizar del atributo limits conforme a la sección a la que pertenezca
        if sect == 1 or sect == 2:
            limitY = 1 if dir == -1 else 3
        else:
            limitY = 1 if dir == 1 else 3

        aux = 0  # variable auxiliar para el movimiento en el eje x del robot
        next_move = list(self.pos)  # Almacena el siguiente movimiento del robot

        # Si el robot llega a un límite del eje Y, se mueve 1 celda en el eje X y continua su movimiento en dirección opuesta
        if self.pos[1] == self.limits[limitY]:
            self.direction *= -1
            if sect == 0 or sect == 1:
                next_move[0] += 1
            else:
                next_move[0] -= 1
            aux = -1 * self.direction

        next_move[1] += self.direction + aux
        return next_move

    # Definir el comportamiento del agente robotCorner en cada paso de la simulación
    def step(self):
        if self.loaded:
            if self.delivering:
                next_move = self.deliver()
            else:
                next_move = self.drop()
        elif self.returning:
            next_move = self.ret()
        else:
            next_move = self.search()
        self.model.grid.move_agent(self, tuple(next_move))
