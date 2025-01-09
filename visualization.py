import matplotlib.pyplot as plt
from matplotlib import animation
from matplotlib import colors
from typing import Any

from forest import Forest


def animate_forest(forest: Forest, steps: int, interval: int) -> None:
    fig, ax = plt.subplots()
    cmap = colors.ListedColormap(['#a7f779', '#1c8507', '#f50707'])
    im = ax.imshow(forest.grid, cmap=cmap, vmin=0, vmax=2)

    def update(frame: int) -> Any:
        forest.step(frame)
        im.set_array(forest.grid)
        ax.set_title(f"Step: {frame}")
        return [im]

    ani = animation.FuncAnimation(fig, update, frames=steps, interval=interval, blit=True)
    ani.save('forest_fire_simulation.gif', fps=2, savefig_kwargs={'pad_inches': 0})
    plt.close()

    fire_progression_charts(forest)


def fire_progression_charts(forest: Forest) -> None:
    fig2, ax2 = plt.subplots()
    ax2.plot(forest.history['step'], forest.history['burning'], label='Burning')
    ax2.plot(forest.history['step'], forest.history['tree'], label='Tree')
    ax2.plot(forest.history['step'], forest.history['empty'], label='Empty')

    ax2.set_xlabel('Step')
    ax2.set_ylabel('Number of cells')
    ax2.set_title('Forest Fire Simulation History')
    ax2.legend()

    fig2.savefig('forest_fire_history.png')
    plt.close(fig2)