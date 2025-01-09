from forest import Forest
from visualization import animate_forest
from typing import Dict, Any
import json


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

        size = params.get('size')
        tree_density = params.get('tree_density')
        lightning_prob = params.get('lightning_prob')
        growth_prob = params.get('growth_prob')
        spread_prob = params.get('spread_prob')
        radius = params.get('radius')

        forest = Forest(size=size,
                        tree_density=tree_density,
                        lightning_prob=lightning_prob,
                        growth_prob=growth_prob,
                        spread_prob=spread_prob,
                        radius=radius)

        steps = params.get('steps')
        interval = params.get('interval')

        animate_forest(forest, steps=steps, interval=interval)

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()