"""

    Selection Operation to select a random percent of components.

"""

import random

import lx
import lxu
import lxu.attributes
import lxifc


class SelectionOperation(lxifc.SelectionOperation, lxu.attributes.DynamicAttributes):
    def __init__(self):
        lxifc.SelectionOperation.__init__(self)
        lxu.attributes.DynamicAttributes.__init__(self)

        self.dyna_Add("random", lx.symbol.sTYPE_PERCENT)
        self.attr_SetFlt(0, 0.5)

        self.mesh = lx.object.Mesh()
        self.point = lx.object.Point()
        self.edge = lx.object.Edge()
        self.polygon = lx.object.Polygon()

        # Keep sets for indices for each type of component
        self.points = set()
        self.edges = set()
        self.polygons = set()

    def selop_SetMesh(self, mesh):
        """ Get's called whenever item get channel changes,"""

        # Check the % from input,
        percent = self.dyna_Float(0, 0.5)

        if self.mesh.set(mesh):
            # If we got a valid mesh, populate all sets and return OK
            points, edges, polygons = self.mesh.PointCount(), self.mesh.EdgeCount(), self.mesh.PolygonCount()
            self.points = set(random.sample([i for i in range(points)], k=int(percent * points)))
            self.edges = set(random.sample([i for i in range(edges)], k=int(percent * edges)))
            self.polygons = set(random.sample([i for i in range(polygons)], k=int(percent * polygons)))
            return lx.result.OK

        return lx.result.FAILED

    # Perform tests for each component, if they return true - that component will be selected by the selop
    def selop_TestPoint(self, point):
        self.point.set(self.mesh.PointAccessor())
        self.point.Select(point)
        return self.point.Index() in self.points

    def selop_TestEdge(self, edge):
        self.edge.set(self.mesh.EdgeAccessor())
        self.edge.Select(edge)
        return self.edge.Index() in self.edges

    def selop_TestPolygon(self, polygon):
        self.polygon.set(self.mesh.PolygonAccessor())
        self.polygon.Select(polygon)
        return self.polygon.Index() in self.polygons


tags = {lx.symbol.sSELOP_PMODEL: "."}
lx.bless(SelectionOperation, "py.selops.random", tags)
