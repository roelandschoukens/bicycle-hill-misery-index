import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

"""
Color map used to preview map data.
"""

colmap = [
    (0, 255, 100),
    (80, 255, 120),
    (150, 255, 160),
    (220, 255, 180),
    (255, 248, 200),
    (255, 241, 160),
    (255, 220, 130),
    (255, 200,  90),
    (255, 180,  45),
    (255, 140,  45),
    (255, 110,  20),
    (255, 80,  60),
]

X = np.linspace(0, 1, len(colmap))
cdata = dict(
    red=  [(x, y[0] / 255, y[0] / 255) for x, y in zip(X, colmap)],
    green=[(x, y[1] / 255, y[1] / 255) for x, y in zip(X, colmap)],
    blue= [(x, y[2] / 255, y[2] / 255) for x, y in zip(X, colmap)])

our_cm = LinearSegmentedColormap('map-height', cdata)


if __name__ == '__main__':
    import matplotlib.pyplot as plt
    
    W, H = 1000, 300
    vramp = np.linspace(0, 1, H)
    wave = np.outer(
        vramp * vramp,
        np.sin(np.linspace(0, 628, W)) * 0.15 + 0.15)
    plt.figure(figsize=[15, 6])
    plt.imshow(wave + np.linspace(0, 3, W), cmap=our_cm)
    plt.show()
    
    