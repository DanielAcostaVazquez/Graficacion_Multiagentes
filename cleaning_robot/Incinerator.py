from mesa import Agent

class Incinerator(Agent):
    def __init__(self, model):
        super().__init__(model.next_id(), model)
        self.on = False
        self.activation = False
        self.garbage = False

    def drop(self, garbage):
        self.garbage = garbage

    def step(self):
        if (self.garbage):
            self.activation = True
            print("activating")
        if (self.activation):
            self.activation = False
            self.garbage.burn()
            self.garbage = False
            self.on = True
            print("on")
        elif (self.on):
            self.on = False
            print("off")
        

