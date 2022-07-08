"""

    Python version of the cc_command_mesh.cpp sample from lxsdk

"""

from __future__ import annotations
from typing import Tuple


import lx
import lxu
import lxu.command
import lxu.vector
import lxifc


class BoundingBox(object):
    """ Bounding Box object, holding two points min & max to define the axis aligned bounds. """
    def __init__(self,
                 min_=(float("inf"), float("inf"), float("inf")),
                 max_=(-float("inf"), -float("inf"), -float("inf"))):
        self.min = min_
        self.max = max_

    @property
    def extent(self):
        return lxu.vector.sub(self.max, self.min)

    def add(self, point: Tuple[float, float, float]):
        """ Add a point to the bounding box, expanding it """
        self.min = tuple(min(a, b) for a, b in zip(self.min, point))
        self.max = tuple(max(a, b) for a, b in zip(self.max, point))


class Visitor(lxifc.Visitor):
    """ We will use a visitor when walking through the points of a mesh. """
    def __init__(self, point: lx.object.Point):
        self.point = point
        self.bound = BoundingBox()

    def vis_Evaluate(self):
        """ vis_Evaluate is called to process each element in an enumeration, this will get the point position and
        expand the bounding box to include it. """
        self.bound.add(self.point.Pos())


class Command(lxu.command.BasicCommand):
    """ Command will output to the log when fired. """
    def __init__(self):
        lxu.command.BasicCommand.__init__(self)

        # Spawn a notifier
        self.notifier_service = lx.service.NotifySys()
        self.item_notifier = lx.object.Notifier()

    def cmd_NotifyAddClient(self, argument, object_):
        # Subscribe to selection events,
        self.item_notifier = self.notifier_service.Spawn(lx.symbol.sNOTIFIER_SELECT, "item +d")
        self.item_notifier.AddClient(object_)

    def cmd_NotifyRemoveClient(self, object_):
        self.item_notifier.RemoveClient(object_)

    def basic_Enable(self, msg) -> bool:
        """ Test if the command should be enabled given the state of the system. """
        layer_service = lx.service.Layer()
        layer_service.SetScene(0)
        for i in range(layer_service.Count()):
            if layer_service.Flags(i) & lx.symbol.f_LAYER_ACTIVE:
                return True

        return False

    def basic_Execute(self, msg, flags):
        """ Get a layer scan for points in active layers and enumerate all the points in all layers. """
        mesh_service = lx.service.Mesh()
        mode = mesh_service.ModeCompose("select", None)

        point = lx.object.Point()  # note: will not have an interface and can not be used until given a valid point
        visitor = Visitor(point)

        layer_service = lx.service.Layer()
        layer_scan = layer_service.ScanAllocate(lx.symbol.f_LAYER_ACTIVE | lx.symbol.f_LAYERSCAN_MARKVERTS)
        for layer_index in range(layer_scan.Count()):
            mesh = layer_scan.MeshInstance(layer_index)
            point = mesh.PointAccessor()
            visitor.point = point
            point.Enumerate(mode, visitor, 0)

        lx.out(f"py.mesh got box {visitor.bound.extent[0]}")


lx.bless(Command, "py.mesh")
