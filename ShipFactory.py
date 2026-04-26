from Ship import Ship

class ShipFactory:
    @staticmethod
    def create_fleet():
        return [
            Ship("Carrier", 5),
            Ship("Battleship", 4),
            Ship("Cruiser", 3),
            Ship("Submarine", 3),
            Ship("Destroyer", 2),
        ]
