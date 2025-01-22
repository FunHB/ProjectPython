from typing import Dict, Any
import json
import traceback

from game import Game
from forest import Forest


def load_config(file_path: str) -> Dict[str, Any]:
    try:
        with open(file_path, 'r') as file:
            config = json.load(file)
        return config
    except FileNotFoundError:
        raise FileNotFoundError(f"Config file {file_path} not found.")


def main() -> None:
    try:
        params = load_config('config.json')

        fps = params.get('fps')
        tree_density = params.get('tree_density')
        lightning_prob = params.get('lightning_prob')
        growth_prob = params.get('growth_prob')
        spread_prob = params.get('spread_prob')
        humidity_change = params.get('humidity_change')
        humidity_change_fire = params.get('humidity_change_fire')
        
        wind = params.get('wind')
        wind_change = params.get('wind_change')
        radius = params.get('radius')

        forest = Forest(tree_density=tree_density,
                        lightning_prob=lightning_prob,
                        growth_prob=growth_prob,
                        spread_prob=spread_prob,
                        humidity_change=humidity_change,
                        humidity_change_fire=humidity_change_fire,
                        wind=wind,
                        wind_change=wind_change,
                        radius=radius)

        game = Game(forest, fps=fps)
        game.start()

    except Exception:
        print(f"An error occurred: {traceback.print_exc()}")


if __name__ == "__main__":
    main()
