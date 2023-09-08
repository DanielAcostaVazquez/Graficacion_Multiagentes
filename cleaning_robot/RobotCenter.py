from mesa import Agent
from Incinerator import Incinerator
from GarbageCell import GarbageCell


class RobotCenter(Agent):
    def __init__(self, model, grid_size, c_coords, section, pos, incinerator):
        super().__init__(model.next_id(), model)
        self.model = model
        self.loaded = (
            False  # Variable para identificar si el robot está cargando basura
        )
        self.c_coords = c_coords #Variable para saber los limites del centro
        self.currGarbage = False
        self.returning = False  # Variable para identificar si el robot está regresando
        self.delivering = False
        self.lastPos = (0, 0)
        self.grid_size = grid_size  # Tamaño de la malla
        self.direction = -1 if section == 0 else 1
        self.pos = pos  # posición actual
        self.aux = False  # flag auxiliar para el movimiento del robot
        self.iniReturn = (
            False  # flag para saber si el robot esta regresando a su posicion inicial
        )
        self.incinerator = incinerator
        self.incineratorPos = (grid_size // 2, (grid_size // 2))
        self.incineratorStop = [
            (grid_size // 2, (grid_size // 2) + 1),
            (grid_size // 2, (grid_size // 2) - 1),
        ]

        # Section 0 es el rbot central de la izquierda, cualquier otra section es el robot de la derecha
        if section == 0:
            self.iniPos = c_coords[1]
            self.c_coordsLimit = c_coords[0]
        else:
            self.iniPos = c_coords[3]
            self.c_coordsLimit = c_coords[2]

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
        if tuple(next_move) == self.iniPos:
            self.returning = False
            self.direction = -1 if self.section == 0 else 1
        elif tuple(next_move) == self.lastPos:
            self.returning = False
        return next_move

    # Espera su turno para dejar la basura en el incinerador
    def drop(self):
        if self.incinerator.garbage or self.incinerator.on:
            return self.pos
        else:
            self.currGarbage.drop(self.incineratorPos)
            self.incinerator.drop(self.currGarbage)
            self.returning = True
            self.loaded = False
            self.currGarbage = False
            return list(self.incineratorPos)

    # Entrega de basura en el centro
    # Regresa una lista next_move
    def deliver(self):
        # Alinear en x
        next_move = list(self.pos)
        if self.pos[0] != self.incineratorPos[0]:
            if self.pos[0] < self.incineratorPos[0]:
                next_move[0] += 1
            else:
                next_move[0] -= 1
        else:
            self.pos
        # Alinear en y
        if self.pos[1] != self.incineratorPos[1]:
            if self.pos[1] < self.incineratorPos[1]:
                next_move[1] += 1
            else:
                next_move[1] -= 1
        if tuple(next_move) == self.incineratorPos:
            self.delivering = False
            return list(self.pos)
        return next_move

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
        next_move = list(self.pos)  # almacenaje del siguiente movimiento del robot
        #Funcion de backup
        if self.pos[0] < self.c_coords[0][0]:
            self.iniReturn = True
        elif self.pos[0] > self.c_coords[2][0]:
            self.iniReturn = True
        elif self.pos[1] < self.c_coords[0][1]:
            self.iniReturn = True
        elif self.pos[1] > self.c_coords[1][1]:
            self.iniReturn = True
        # En caso de toparse con el incinerador
        if self.pos == self.incineratorStop[0] or self.pos == self.incineratorStop[1]:
            self.iniReturn = True
            if self.section == 0:
                next_move[0] -= 1
            else:
                next_move[0] += 1
            return next_move
        # En caso de estar de regreso:
        elif self.iniReturn:
            if self.pos[0] != self.iniPos[0]:
                i = 1 if self.pos[0] < self.iniPos[0] else -1
                next_move[0] += i

            if self.pos[1] != self.iniPos[1]:
                i = 1 if self.pos[1] < self.iniPos[1] else -1
                next_move[1] += i

            if next_move[0] == self.iniPos[0] and next_move[1] == self.iniPos[1]:
                self.iniReturn = False
                self.direction = -1 if self.section == 0 else 1

            return next_move
        # En caso de que esten en su posicion inicial:
        elif self.pos == self.iniPos:
            print("arranque inicial")
            next_move[1] += self.direction
            return next_move
        # En caso de que llegue a un limite:
        elif self.pos[1] == self.iniPos[1] or self.pos[1] == self.c_coordsLimit[1]:
            if self.aux:
                self.aux = False
                next_move[1] += self.direction
                return next_move
            else:
                self.direction *= -1
                if self.section == 0:
                    next_move[0] += 1
                else:
                    next_move[0] -= 1
                next_move[1] += self.direction + (-1 * self.direction)
                self.aux = True
                return next_move
        # En cualquier otro caso:
        else:
            next_move[1] += self.direction
            return next_move

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
