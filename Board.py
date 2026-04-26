class Board:
    def __init__(self, size=10):
        self.size = size
        self.grid = [[None for _ in range(size)] for _ in range(size)]
        self.ships = []

    def place_ship(self, ship, x, y, orientation):
        ship_id = len(self.ships)
        if orientation == 'H':
            if y + ship.size > self.size: return False
            if any(self.grid[x][y + i] is not None for i in range(ship.size)): return False
            for i in range(ship.size):
                self.grid[x][y + i] = ship_id
                ship.positions.append((x, y + i))
        else:
            if x + ship.size > self.size: return False
            if any(self.grid[x + i][y] is not None for i in range(ship.size)): return False
            for i in range(ship.size):
                self.grid[x + i][y] = ship_id
                ship.positions.append((x + i, y))
        self.ships.append(ship)
        return True

    def attack(self, x, y):
        cell = self.grid[x][y]
        if cell in ('O', 'X'):
            return "Already attacked"
        if cell is None:
            self.grid[x][y] = 'O'
            return "Miss"
        ship = self.ships[cell]
        ship.hit()
        self.grid[x][y] = 'X'
        if ship.is_sunk():
            return f"sunk:{ship.name}"
        return "Hit"

    def all_sunk(self):
        return all(s.is_sunk() for s in self.ships)
