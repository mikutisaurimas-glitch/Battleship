import random
from Player import Player
from AIPlayer import AIPlayer

class Game:
    def __init__(self, player_name="Player"):
        self.player = Player(player_name)
        self.ai = AIPlayer()
        self.ai.place_ships_randomly()
        self.game_over = False
        self.ai_goes_first = random.choice([True, False])

    def player_turn(self, x, y):
        result = self.player.attack(self.ai.board, x, y)
        won = self.ai.board.all_sunk()
        if won: self.game_over = True
        extra_turn = not self.game_over and ("Hit" in result or "sunk" in result.lower())
        return result, won, extra_turn

    def ai_turn(self):
        result, x, y = self.ai.make_move(self.player.board)
        lost = self.player.board.all_sunk()
        if lost: self.game_over = True
        extra_turn = not self.game_over and ("Hit" in result or "sunk" in result.lower())
        return result, x, y, lost, extra_turn
