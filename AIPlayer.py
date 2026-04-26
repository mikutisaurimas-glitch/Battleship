import random
from Player import Player
from ShipFactory import ShipFactory

class AIPlayer(Player):
    def __init__(self):
        super().__init__("AI")
        self.possible_moves = [(x, y) for x in range(10) for y in range(10)]
        self.tried_moves = set()
        self.hit_targets = []

    def place_ships_randomly(self):
        for ship in ShipFactory.create_fleet():
            placed = False
            while not placed:
                x, y = random.randint(0, 9), random.randint(0, 9)
                orientation = random.choice(['H', 'V'])
                placed = self.board.place_ship(ship, x, y, orientation)

    def _valid(self, x, y):
        return 0 <= x < 10 and 0 <= y < 10 and (x, y) not in self.tried_moves

    def _sync_alive(self, opponent_board):
        self._alive_sizes = sorted(
            {ship.size for ship in opponent_board.ships if not ship.is_sunk()}
        )

    def _can_fit(self, x, y, min_size):
        for dx, dy in [(1, 0), (0, 1)]:
            span = 1
            for sign in (1, -1):
                step = 1
                while True:
                    nx, ny = x + dx * sign * step, y + dy * sign * step
                    if 0 <= nx < 10 and 0 <= ny < 10 and (nx, ny) not in self.tried_moves:
                        span += 1
                        step += 1
                    else:
                        break
            if span >= min_size:
                return True
        return False

    def _hunt_move(self):
        min_size = self._alive_sizes[0] if self._alive_sizes else 1
        candidates = [
            (x, y) for (x, y) in self.possible_moves
            if self._can_fit(x, y, min_size)
        ]
        pool = candidates if candidates else self.possible_moves
        return random.choice(pool)

    def _pick_target(self):
        if not self.hit_targets:
            return self._hunt_move()

        hit_set = set(self.hit_targets)

        for hx, hy in self.hit_targets:
            for dx, dy in [(1, 0), (0, 1)]:
                if (hx + dx, hy + dy) in hit_set:
                    step = 2
                    while (hx + dx * step, hy + dy * step) in hit_set:
                        step += 1
                    fwd = (hx + dx * step, hy + dy * step)
                    if self._valid(*fwd):
                        return fwd
                    step = -1
                    while (hx + dx * step, hy + dy * step) in hit_set:
                        step -= 1
                    bwd = (hx + dx * step, hy + dy * step)
                    if self._valid(*bwd):
                        return bwd

        for hx, hy in self.hit_targets:
            for ddx, ddy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = hx + ddx, hy + ddy
                if self._valid(nx, ny):
                    return (nx, ny)

        return self._hunt_move()

    def make_move(self, opponent_board):
        self._sync_alive(opponent_board)
        x, y = self._pick_target()

        self.possible_moves.remove((x, y))
        self.tried_moves.add((x, y))

        result = self.attack(opponent_board, x, y)

        if "Hit" in result:
            self.hit_targets.append((x, y))
            for ship in opponent_board.ships:
                if (x, y) in ship.positions and ship.is_sunk():
                    sunken = set(ship.positions)
                    self.hit_targets = [h for h in self.hit_targets if h not in sunken]
                    break

        return result, x, y
