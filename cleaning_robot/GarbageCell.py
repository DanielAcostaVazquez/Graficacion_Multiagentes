from mesa import Agent

class GarbageCell(Agent):
    def __init__(self, model):
        super().__init__(model.next_id(), model)
        self.dirty = True
        self.burned = False
    
    def pickUp(self):
        self.dirty = False
    
    def drop(self, nextPos):
        self.dirty = True
        self.model.grid.move_agent(self, tuple(nextPos))
    
    def burn(self):
        self.burned = True

        