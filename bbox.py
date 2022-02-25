from collections import namedtuple

SrcTile = namedtuple('SrcTile', 'bbox f img scale')

class BBOX(namedtuple('BBOX_base', 'x y w h')):
    """ Represents a bounding box as something more specific than a shapely polygon
    
    Units are usually northing and easting. """

    @classmethod
    def with_xyxy(_cls, x1, y1, x2, y2):
        """ Construct in terms of top-left and bottom-right points """
        return BBOX(x1, y1, x2 - x1, y2 - y1)
    
    def x2(self):
        """ the right edge (east) """
        return self.x + self.w

    def y2(self):
        """ the bottom edge (south) """
        return self.y + self.h

    def xyxy(self):
        """ extent as top-left and bottom-right points.
        
        `shapely.geometry.box()` takes this format. """
        return (self.x, self.y, self.x2(), self.y2())

    def xxyy(self):
        """ extent in `matplotlib` format """
        return (self.x, self.x2(), self.y, self.y2())
