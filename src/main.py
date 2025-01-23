import traceback

from src.config import load_config
from src.game.game import Game
from src.simulation.forest import Forest


class Main:
    def __init__(self) -> None:
        try:
            params = load_config()

            self.fps = params.get('fps')
            self.tree_density = params.get('tree_density')
            self.lightning_prob = params.get('lightning_prob')
            self.growth_prob = params.get('growth_prob')
            self.spread_prob = params.get('spread_prob')
            self.humidity_change = params.get('humidity_change')
            self.humidity_change_fire = params.get('humidity_change_fire')
            self.water_threshold = params.get('water_threshold')

            self.wind = params.get('wind')
            self.wind_change = params.get('wind_change')
            self.radius = params.get('radius')

            self.forest = Forest(tree_density=self.tree_density,
                                 lightning_prob=self.lightning_prob,
                                 growth_prob=self.growth_prob,
                                 spread_prob=self.spread_prob,
                                 humidity_change=self.humidity_change,
                                 humidity_change_fire=self.humidity_change_fire,
                                 water_threshold=self.water_threshold,
                                 wind=self.wind,
                                 wind_change=self.wind_change,
                                 radius=self.radius)

        except Exception:
            print(f"An error occurred during initialization: {traceback.print_exc()}")

    def run(self) -> None:
        try:
            game = Game(self.forest, fps=self.fps)
            game.start()
        except Exception:
            print(f"An error occurred during game execution: {traceback.print_exc()}")
