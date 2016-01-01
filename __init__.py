def main():
    from . import game
    from .game.game import Game
    game.GAME = Game()
    game.GAME.run()

