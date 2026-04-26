import unittest
from Ship import Ship
from Board import Board

class TestBattleship(unittest.TestCase):
    def test_ship_sinking(self):
        ship = Ship("TestSub", 2)
        ship.hit()
        self.assertFalse(ship.is_sunk())
        ship.hit()
        self.assertTrue(ship.is_sunk())

    def test_board_placement(self):
        board = Board(10)
        ship = Ship("Destroyer", 2)
        # Test valid placement
        self.assertTrue(board.place_ship(ship, 0, 0, 'H'))
        # Test overlapping placement (should fail)
        ship2 = Ship("Sub", 3)
        self.assertFalse(board.place_ship(ship2, 0, 0, 'V'))

    def test_attack_logic(self):
        board = Board(10)
        ship = Ship("Patrol", 1)
        board.place_ship(ship, 5, 5, 'H')
        # Test Hit
        self.assertIn("sunk", board.attack(5, 5).lower())
        # Test Miss
        self.assertEqual(board.attack(0, 0), "Miss")
        # Test Double Attack
        self.assertEqual(board.attack(0, 0), "Already attacked")

if __name__ == "__main__":
    unittest.main()