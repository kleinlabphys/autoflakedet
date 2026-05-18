import time
from functools import wraps
import matplotlib.pyplot as plt

def wait_until_ready(max_cycles=20, cycle_wait=0.5):
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            for _ in range(max_cycles):
                ready = func(self, *args, **kwargs)
                if ready:
                    return ready
                time.sleep(cycle_wait)
        return wrapper
    return decorator

def plot_detected_flakes(points,
                   width,
                   height,
                   chipIdx=0,
                   show_grid=True,
                   point_size=50,
                   color="blue",
                   max_figure_size=8):
    """
    Plot (x, y) points inside a rectangle.
    """

    title = f"Potential Flake Locations on Chip {chipIdx}"

    # Scale figure dimensions proportionally
    aspect_ratio = width / height

    if aspect_ratio >= 1:
        fig_width = max_figure_size
        fig_height = max_figure_size / aspect_ratio
    else:
        fig_height = max_figure_size
        fig_width = max_figure_size * aspect_ratio

    # Ensure window is wide enough for title visibility
    min_width_for_title = max(6, len(title) * 0.12)
    fig_width = max(fig_width, min_width_for_title)

    # Extra room for title
    fig_height += 1.0

    fig, ax = plt.subplots(figsize=(fig_width, fig_height))

    # Draw rectangle boundary
    ax.plot([0, width], [0, 0], color='black')
    ax.plot([width, width], [0, height], color='black')
    ax.plot([width, 0], [height, height], color='black')
    ax.plot([0, 0], [height, 0], color='black')

    # Extract coordinates
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]

    # Plot points
    ax.scatter(xs, ys, s=point_size, color=color)

    # Configure axes
    ax.set_xlim(0, width)
    ax.set_ylim(0, height)

    # Preserve geometry
    ax.set_aspect('equal', adjustable='box')

    # Grid
    if show_grid:
        ax.grid(True, linestyle='--', alpha=0.6)

    ax.set_xlabel("x")
    ax.set_ylabel("y")

    # Figure-level title
    fig.suptitle(
        title,
        fontsize=14,
        y=0.98
    )

    # Reserve space for title
    plt.subplots_adjust(top=0.90)

    plt.show()
