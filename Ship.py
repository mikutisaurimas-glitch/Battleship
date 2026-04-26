class Ship:
    def __init__(self, name, size):
        self.name = name
        self.size = size
        self.hits = 0
        self.positions = []

    def hit(self):
        if not self.is_sunk():
            self.hits += 1

    def is_sunk(self):
        return self.hits >= self.size
