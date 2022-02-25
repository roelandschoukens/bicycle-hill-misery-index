from math import floor
from shapely.geometry import LineString
import numpy as np


def split_line(line, dist_limit):
    """ split a Line into lines of at most dist_limit length
    
    parameters:
     - line: a shapely.geometry.LineString to split
     - dist_limit: the maximal distance you’d like to have
    
    return: list of shapely.geometry.LineString. Any vertex of `line` is guaranteed
            to be a vertex in one or two of the returned lines.
    """
    if line.length <= dist_limit:
        return [line]
    else:
        new_list = []
        coords = np.asarray(line.coords)
        dist = np.sqrt(np.sum((coords[:-1]-coords[1:])**2, axis=1))
        
        # start with a quick check if we need to split segments:
        if np.max(dist) > dist_limit:
            # make new list of coordinates, breaking up too large segments
            coords_filled = [[coords[0]]]
            dist_filled = []
            for i, d in enumerate(dist):
                # use some tolerance:
                if d >= dist_limit * 1.5:
                    # too large segments are split in some amount of even parts
                    n = floor(d / dist_limit + 0.5)
                    coords_filled.append(np.linspace(coords[i], coords[i+1], n+1)[1:])
                    dist_filled.append([d/n] * n)
                else:
                    coords_filled.append([coords[i+1]])
                    dist_filled.append([d])
            coords = np.concatenate(coords_filled)
            dist = np.concatenate(dist_filled)
        
        start = 0
        new_d = dist[0]
        
        # group coordinates in new lines, ensuring that no line
        # is too long
        for i in range(1, len(dist)):
            if new_d > 0 and new_d + dist[i] > dist_limit:
                new_list.append(LineString(coords[start:i+1]))
                new_d = dist[i]
                start = i
            new_d += dist[i]

        if new_d > 0:
            new_list.append(LineString(coords[start:]))
            
        return new_list

if __name__ == '__main__':
    np.set_printoptions(precision=2, suppress=True)
    line = LineString([
        [  1, 0],
        [190, 1],
        [320, 2],
        [330, 3],
        [340, 4],
        [380, 5],
        [600, 6],
        [1100, 7]])
    ll = split_line(line, 100)
    for l in ll:
        print('l =', l.length)
        print(np.asarray(l.coords))