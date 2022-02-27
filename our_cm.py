import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap

"""
Color map used to preview map data.
"""

colmap = np.array([
    (195, 221, 233),
    (226, 239, 212),
    (255, 255, 191),
    (255, 229, 172),
    (255, 204, 152),
    (247, 160, 165),
    (239, 114, 179),
]) / 255

our_cm = ListedColormap(colmap, name='map-height')


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
    
    