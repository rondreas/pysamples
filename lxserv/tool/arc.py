"""

    /samples/tool/arc/arc.cpp

"""

from __future__ import annotations

from math import pi

import lx

import lxu
import lxu.vector

import lxifc


# constants used to define default values for attributes.
from typing import Tuple

DEFAULT_RADIUS = 1.0  # this is DEF_RADI in the arc.cpp
DEFAULT_ANGLE = pi / 2.0  # and this DEF_ANGL, better explicit than saving two chars...
DEFAULT_SEGMENTS = 15
DEFAULT_REVERSE = False


class ArcTool(lxifc.Tool, lxifc.ToolModel, lxu.attributes.DynamicAttributes):
    def __init__(self):
        packet_service = lx.service.Packet()

        # Allocate a vector type,
        self.vector_type = packet_service.CreateVectorType(lx.symbol.sCATEGORY_TOOL)  # type: lx.object.VectorType

        # "allow packets to be added to the definition"
        packet_service.AddPacket(self.vector_type, lx.symbol.sP_TOOL_VIEW_EVENT, lx.symbol.fVT_GET)
        packet_service.AddPacket(self.vector_type, lx.symbol.sP_TOOL_INPUT_EVENT, lx.symbol.fVT_GET)
        packet_service.AddPacket(self.vector_type, lx.symbol.sP_TOOL_EVENTTRANS, lx.symbol.fVT_GET)
        packet_service.AddPacket(self.vector_type, lx.symbol.sP_TOOL_ACTCENTER, lx.symbol.fVT_GET)
        packet_service.AddPacket(self.vector_type, lx.symbol.sP_TOOL_AXIS, lx.symbol.fVT_GET)
        packet_service.AddPacket(self.vector_type, lx.symbol.sP_TOOL_XFRM, lx.symbol.fVT_GET)

        # Get the 'offsets', so we can easier look up action center etc.
        self.offset_view = packet_service.Lookup(lx.symbol.sCATEGORY_TOOL, lx.symbol.sP_TOOL_VIEW_EVENT)
        self.offset_input = packet_service.Lookup(lx.symbol.sCATEGORY_TOOL, lx.symbol.sP_TOOL_INPUT_EVENT)
        self.offset_event = packet_service.Lookup(lx.symbol.sCATEGORY_TOOL, lx.symbol.sP_TOOL_EVENTTRANS)
        self.offset_center = packet_service.Lookup(lx.symbol.sCATEGORY_TOOL, lx.symbol.sP_TOOL_ACTCENTER)
        self.offset_axis = packet_service.Lookup(lx.symbol.sCATEGORY_TOOL, lx.symbol.sP_TOOL_AXIS)
        self.offset_xfrm = packet_service.Lookup(lx.symbol.sCATEGORY_TOOL, lx.symbol.sP_TOOL_XFRM)

        lxu.attributes.DynamicAttributes.__init__(self)

        # Define the attributes for the tool,
        # TODO: Can Float3 types be used?
        self.dyna_Add("center.x", lx.symbol.sTYPE_FLOAT)
        self.dyna_Add("center.y", lx.symbol.sTYPE_FLOAT)
        self.dyna_Add("center.z", lx.symbol.sTYPE_FLOAT)

        self.dyna_Add("start.x", lx.symbol.sTYPE_FLOAT)
        self.dyna_Add("start.y", lx.symbol.sTYPE_FLOAT)
        self.dyna_Add("start.z", lx.symbol.sTYPE_FLOAT)

        self.dyna_Add("end.x", lx.symbol.sTYPE_FLOAT)
        self.dyna_Add("end.y", lx.symbol.sTYPE_FLOAT)
        self.dyna_Add("end.z", lx.symbol.sTYPE_FLOAT)

        self.dyna_Add("radius", lx.symbol.sTYPE_DISTANCE)
        self.dyna_Add("angle", lx.symbol.sTYPE_ANGLE)

        self.dyna_Add("segments", lx.symbol.sTYPE_INTEGER)
        self.dyna_Add("reverse", lx.symbol.sTYPE_BOOLEAN)

        selection_service = lx.service.Selection()
        self.scene_code = selection_service.LookupType(lx.symbol.sSELTYP_SCENE)

    # Using python properties here to more easily access the attributes,
    @property
    def center(self) -> Tuple[float, float, float]:
        return (
            self.dyna_GetFlt(0),
            self.dyna_GetFlt(1),
            self.dyna_GetFlt(2)
        )

    @property
    def start(self) -> Tuple[float, float, float]:
        return (
            self.dyna_GetFlt(3),
            self.dyna_GetFlt(4),
            self.dyna_GetFlt(5)
        )

    @property
    def end(self) -> Tuple[float, float, float]:
        return (
            self.dyna_GetFlt(6),
            self.dyna_GetFlt(7),
            self.dyna_GetFlt(8)
        )

    # Here we will define the methods for lxifc.Tool
    def tool_Reset(self):
        # LXx_VCLR sets a vector to (0.0, 0.0, 0.0)
        self.attr_SetFlt(0, 0.0)
        self.attr_SetFlt(1, 0.0)
        self.attr_SetFlt(2, 0.0)

        # LXx_VSET3 will set the vector to given values,
        self.attr_SetFlt(3, DEFAULT_RADIUS)
        self.attr_SetFlt(4, 0.0)
        self.attr_SetFlt(5, 0.0)

        self.attr_SetFlt(6, 0.0)
        self.attr_SetFlt(7, DEFAULT_RADIUS)
        self.attr_SetFlt(8, 0.0)

        self.attr_SetFlt(9, DEFAULT_RADIUS)
        self.attr_SetFlt(10, DEFAULT_ANGLE)

        self.attr_SetInt(11, DEFAULT_SEGMENTS)
        self.attr_SetInt(12, DEFAULT_REVERSE)  # the bool is implicitly converted into an integer

    # The example calls these three methods "Boilerplate" that identify this as an action (state altering) tool
    def tool_VectorType(self) -> lx.object.VectorType:
        return self.vector_type

    def tool_Order(self):
        # TODO: There is no match to LXs_ORD_ACTR in symbols,
        return "\xF0"  # this is what the constant is defined as,

    def tool_Task(self):
        return lx.symbol.i_TASK_ACTR

    def tool_Evaluate(self, vts: lx.object.Unknown):
        vector_stack = lx.object.VectorStack(vts)
        # view = vector_stack.Optional(self.offset_view)  # TODO: not sure what a ToolViewEvent is in Python...

        # tool_xfrm = vector_stack.Optional(self.offset_xfrm)

        layer_service = lx.service.Layer()
        layer_scan = layer_service.ScanAllocate(
            lx.symbol.f_LAYERSCAN_PRIMARY | lx.symbol.f_LAYERSCAN_WRITEMESH | lx.symbol.f_LAYERSCAN_MARKVERTS)

        # No active mesh available, exit early
        if layer_scan.Count() == 0:
            return

        mesh = layer_scan.MeshEdit(0)
        vert = mesh.PointAccessor()
        poly = mesh.PolygonAccessor()

        num_segments = self.dyna_GetInt(11)
        if num_segments < 1:
            num_segments = 1

        num_points = num_segments + 2

        for index in range(num_segments):
            t = (index + 1) / num_segments


    def GetPos(self, t: float) -> Tuple[float, float, float]:
        vector_0 = lxu.vector.sub(self.start, self.center)
        vector_1 = lxu.vector.sub(self.end, self.center)
        vector_2 = lxu.vector.cross(vector_0, vector_1)
        length = lxu.vector.length(vector_2)

        if not length:
            pass

        return 0.0, 0.0, 0.0

    # Here we will define the methods for lxifc.ToolModel
    def tmod_Flags(self):
        """ Just copying the docstring from the C++ sample,

        'We employ a combination of event-based input and hauling. I0 input events (left mouse button) are handled
        through event callbacks. I1 input events (right mouse button) are treated as hauling, which affects the radius.'

        """
        return lx.symbol.fTMOD_I1_ATTRHAUL | lx.symbol.fTMOD_DRAW_3D | lx.symbol.fTMOD_I0_INPUT

    def tmod_Initialize(self,vts,adjust,flags):
        adjust_tool = lx.object.AdjustTool(adjust)
        vector_stack = lx.object.VectorStack(vts)

        # Get matrices for tool
        tool_action_center
        tool_axis = None


lx.bless(ArcTool, "py.prim.arc")
