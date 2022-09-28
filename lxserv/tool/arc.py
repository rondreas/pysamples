"""

    /samples/tool/arc/arc.cpp

    The tool already exists in Modo as prim.arc that we can compare against.

    To run, `tool.set py.prim.arc on`

"""

from __future__ import annotations

import math
import ctypes

import lx
import lxu
import lxu.vector
import lxu.attributes
import lxu.select
import lxifc


from typing import Tuple
vector = Tuple[float, float, float]  # typedef double LXtVector[3];
matrix = Tuple[vector, vector, vector]  # typedef double LXtMatrix[3][3]:


# constants used to define default values for attributes.
DEFAULT_RADIUS = 1.0  # this is DEF_RADI in the arc.cpp
DEFAULT_ANGLE = math.pi * 0.5  # and this DEF_ANGL,
DEFAULT_SEGMENTS = 15
DEFAULT_REVERSE = False

# constants defining the "id" for the parts, this is to be able to tell which handles etc are being hit by users.
ARC_HANDLE_CENTER = 10000
ARC_HANDLE_START = 10001
ARC_HANDLE_END = 10002

""" These structs are not defined or exposed to the python API, but packet service will give us pointers to addresses
for the structures, so using ctypes we can try match the structs and access most data. """


class ToolActionCenter(ctypes.Structure):
    """ This should mirror the st_LXpToolActionCenter structure in lxtoolui.h """
    _fields_ = [("v", ctypes.c_double*3)]

    def __repr__(self):
        return f"ToolActionCenter(v=({self.v[0]}, {self.v[1]}, {self.v[2]}))"


class ToolAxis(ctypes.Structure):
    """ copying docstring for st_LXpToolAxis from lxtool.h

    This packet is set by axis tools, like the Auto-Axis tool which sets the axis using a principal axis chosen by the
    event translation object.

    The axis is a unit vector which will often be along a principal axis. In this case, the 'axIndex' will have the
    index for that axis.  Otherwise, axIndex will be -1.

    The axIndex should be treated as a hint, so a tool setting this packet should assure that a correct axis vector is
    set even if a principal axis is selected and the index is set.

    A tool reading this packet should be prepared to use the axis vector, since the index may be set to -1 even though
    the vector happens to lie along a principal direction.

    The axis vector is also the 'forward' vector.

    The 'up' vector is a unit vector perpendicular to the axis, which is nominally in the 'up' direction.

    The 'right' vector is the last vector to form the basis.

    The 'm' matrix is the matrix formed by the 3 basis vectors and 'mInv' is its inverse.
    """
    _fields_ = [
        ("axis", ctypes.c_double*3),
        ("up", ctypes.c_double*3),
        ("right", ctypes.c_double*3),
        ("m", (ctypes.c_double*3)*3),
        ("mInv", (ctypes.c_double*3)*3),
        ("axIndex", ctypes.c_int),
        ("type", ctypes.c_int),
    ]

    def __repr__(self):
        return f"ToolAxis(axis={self.axis}, up={self.up}, right={self.right}, m={self.m}, mInv={self.mInv},\
         axIndex={self.axIndex}, type={self.type})"


class ToolViewEvent(ctypes.Structure):
    """ This should mirror the st_LXpToolViewEvent structure in lxtoolui.h """
    _fields_ = [
        ("vport", ctypes.c_void_p),
        ("view", ctypes.c_void_p),
        ("flags", ctypes.c_uint),
        ("type", ctypes.c_uint),
        ("vportType", ctypes.c_uint),
        ("viewProjection", ctypes.c_uint),
    ]

    def __repr__(self):
        return f"ToolViewEvent(vport={self.vport}, view={self.view}, flags={self.flags}, type={self.type},\
         vportType={self.vportType}, viewProjection={self.viewProjection})"


class ToolXfrm(ctypes.Structure):
    _fields_ = [
        ("v", ctypes.c_double*3),
        ("m", (ctypes.c_double*3)*3),
        ("mInv", (ctypes.c_double*3)*3),
        ("flags", ctypes.c_int),
        ("handedness", ctypes.c_int),
        ("marks", ctypes.c_uint),
    ]

    def __repr__(self):
        return f"ToolXfrm(v={self.v}, m={self.m}, mInt={self.mInv}, flags={self.flags}, handedness={self.handedness},\
         marks={self.marks})"


class ToolInputEvent(ctypes.Structure):
    _fields_ = [
        ("mode", ctypes.c_int),   # modifier key,
        ("input", ctypes.c_int),  # lx.symbol.iTIE_* define indicating the user-remappable input event
        ("count", ctypes.c_int),  # 1 for single click, 2 for double click
        ("part", ctypes.c_int),   # Tool-defined part, or INVIS for clicks elsewhere,
        ("type", ctypes.c_int),   # iTIE_TYPE_* indicating if this is a down/move/up event or none
        ("haul", ctypes.c_int),   # True when attribute hauling is happening
    ]

    def __repr__(self):
        return f"ToolInputEvent(mode={self.mode}, input={self.input}, count={self.count}, part={self.part},\
         type={self.type}, haul={self.haul})"


def matrix_multiply(m: matrix, v: vector) -> vector:
    """ recreating the matrix multiply from lxu math """
    r = [0.0, 0.0, 0.0]
    for i in range(3):
        d = 0.0
        for j in range(3):
            d += v[j] * m[i][j]
        r[i] = d

    return tuple(r)


def matrix_axis_rotation(a: vector, s: float, c: float) -> matrix:
    m = [[0.0, 0.0, 0.0] for _ in range(3)]
    t = 1.0 - c
    m[0][0] = t * a[0] * a[0] + c
    m[0][1] = t * a[0] * a[1] - s * a[2]
    m[0][2] = t * a[0] * a[2] + s * a[1]
    m[1][0] = t * a[1] * a[0] + s * a[2]
    m[1][1] = t * a[1] * a[1] + c
    m[1][2] = t * a[1] * a[2] - s * a[0]
    m[2][0] = t * a[2] * a[0] - s * a[1]
    m[2][1] = t * a[2] * a[1] + s * a[0]
    m[2][2] = t * a[2] * a[2] + c

    return m


class ArcTool(lxifc.Tool, lxifc.ToolModel, lxu.attributes.DynamicAttributes):
    """ """
    def __init__(self):
        """ Allocate a vector type and look up some tool packet offsets. We also allocate values and their string
        conversion for nice encoding. """
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

        # Define the attributes for the tool, we will declare these as properties to the class with getters/setters
        self.dyna_Add("center.x", lx.symbol.sTYPE_FLOAT)
        self.dyna_Add("center.y", lx.symbol.sTYPE_FLOAT)
        self.dyna_Add("center.z", lx.symbol.sTYPE_FLOAT)
        self.center = (0.0, 0.0, 0.0)

        self.dyna_Add("start.x", lx.symbol.sTYPE_FLOAT)
        self.dyna_Add("start.y", lx.symbol.sTYPE_FLOAT)
        self.dyna_Add("start.z", lx.symbol.sTYPE_FLOAT)
        self.start = (0.0, 0.0, 0.0)

        self.dyna_Add("end.x", lx.symbol.sTYPE_FLOAT)
        self.dyna_Add("end.y", lx.symbol.sTYPE_FLOAT)
        self.dyna_Add("end.z", lx.symbol.sTYPE_FLOAT)
        self.end = (0.0, 0.0, 0.0)

        self.dyna_Add("radius", lx.symbol.sTYPE_DISTANCE)
        self.radius = 0.0
        self.dyna_Add("angle", lx.symbol.sTYPE_ANGLE)
        self.angle = 0.0

        self.dyna_Add("segments", lx.symbol.sTYPE_INTEGER)
        self.segments = 1
        self.dyna_Add("reverse", lx.symbol.sTYPE_BOOLEAN)
        self.reverse = 0

        selection_service = lx.service.Selection()
        self.scene_code = selection_service.LookupType(lx.symbol.sSELTYP_SCENE)

        self.start_vector = (0.0, 0.0, 0.0)  # initial start vector
        self.end_vector = (0.0, 0.0, 0.0)  # initial end vector
        self.axis_vector = (0.0, 0.0, 0.0)  # initial axis vector

        self.part = -1
        self.initial_drag = False

        self.primary = lx.object.Item()
        self.lock_angle = False

    # Using python properties here to more easily access the attributes,
    # in the cpp version these are saved as members to the class like "m_name"
    @property
    def center(self) -> vector:
        """ Center Handle """
        return (
            self.attr_GetFlt(0),
            self.attr_GetFlt(1),
            self.attr_GetFlt(2)
        )

    @center.setter
    def center(self, center_: vector):
        x, y, z = center_
        self.attr_SetFlt(0, x)
        self.attr_SetFlt(1, y)
        self.attr_SetFlt(2, z)

    @property
    def start(self) -> vector:
        return (
            self.attr_GetFlt(3),
            self.attr_GetFlt(4),
            self.attr_GetFlt(5)
        )

    @start.setter
    def start(self, start_: vector):
        x, y, z = start_
        self.attr_SetFlt(3, x)
        self.attr_SetFlt(4, y)
        self.attr_SetFlt(5, z)

    @property
    def end(self) -> vector:
        return (
            self.attr_GetFlt(6),
            self.attr_GetFlt(7),
            self.attr_GetFlt(8)
        )

    @end.setter
    def end(self, end_: vector):
        x, y, z = end_
        self.attr_SetFlt(6, x)
        self.attr_SetFlt(7, y)
        self.attr_SetFlt(8, z)

    @property
    def radius(self) -> float:
        return self.attr_GetFlt(9)

    @radius.setter
    def radius(self, radius_: float):
        self.attr_SetFlt(9, radius_)

    @property
    def angle(self) -> float:
        return self.attr_GetFlt(10)

    @angle.setter
    def angle(self, angle_: float):
        self.attr_SetFlt(10, angle_)

    @property
    def segments(self) -> int:
        return self.attr_GetInt(11)

    @segments.setter
    def segments(self, segments_: int):
        self.attr_SetInt(11, segments_)

    @property
    def reverse(self) -> bool:
        return bool(self.attr_GetInt(12))

    @reverse.setter
    def reverse(self, reverse_: bool):
        self.attr_SetInt(12, int(reverse_))

    def tool_Reset(self):
        """ Resets the attributes back to defaults. """
        self.center = (0.0, 0.0, 0.0)
        self.start = (DEFAULT_RADIUS, 0.0, 0.0)
        self.end = (0.0, DEFAULT_RADIUS, 0.0)
        self.radius = DEFAULT_RADIUS
        self.angle = DEFAULT_ANGLE
        self.segments = DEFAULT_SEGMENTS
        self.reverse = DEFAULT_REVERSE

    # The example calls these three methods "Boilerplate" that identify this as an action (state altering) tool
    def tool_VectorType(self) -> lx.object.VectorType:
        return self.vector_type

    def tool_Order(self):
        return "\xF0"

    def tool_Task(self):
        return lx.symbol.i_TASK_ACTR

    def tmod_Flags(self):
        """ Just copying the docstring from the C++ sample,

        'We employ a combination of event-based input and hauling. I0 input events (left mouse button) are handled
        through event callbacks. I1 input events (right mouse button) are treated as hauling, which affects the radius.'

        """
        return lx.symbol.fTMOD_I1_ATTRHAUL | lx.symbol.fTMOD_DRAW_3D | lx.symbol.fTMOD_I0_INPUT

    def tmod_Haul(self, index):
        if index == 0:
            return "radius"
        return 0

    def tmod_Initialize(self, vts, adjust, flags):
        """ Set the initial center position to the action center """
        vector_stack = lx.object.VectorStack(vts)

        tool_action_center = ToolActionCenter.from_address(vector_stack.Optional(self.offset_center))
        tool_axis = ToolAxis.from_address(vector_stack.Optional(self.offset_axis))

        self.center = (tool_action_center.v[0], tool_action_center.v[1], tool_action_center.v[2])
        self.start_vector = (tool_axis.right[0], tool_axis.right[1], tool_axis.right[2])
        self.end_vector = (tool_axis.up[0], tool_axis.up[1], tool_axis.up[2])
        self.axis_vector = (tool_axis.up[0], tool_axis.up[1], tool_axis.up[2])

        self.start = lxu.vector.add(self.center, lxu.vector.scale(self.start_vector, self.radius))
        self.end = lxu.vector.add(self.center, lxu.vector.scale(self.end_vector, self.radius))

        if self.radius > 0.0:
            self.end = self.get_pos(1.0, 1.0)

        self.initial_drag = True

    def tmod_Down(self, vts, adjust):
        adjust_tool = lx.object.AdjustTool(adjust)
        vector_stack = lx.object.VectorStack(vts)
        tool_input_event = ToolInputEvent.from_address(vector_stack.Optional(self.offset_input))

        # TODO: Get the EventTranslatePacket from the vector stack
        address = vector_stack.Optional(self.offset_event)
        event_translate_packet = lx.object.EventTranslatePacket()
        # event_translate_packet.set(address)  # NOTE: not working,

        # Test that the primary mesh is in the scene, (#56533)
        # guessing this is referring to a reported bug with the tool
        scene_selection = lxu.select.SceneSelection()
        scene = scene_selection.current()  # type: lx.object.Scene

        layer_service = lx.service.Layer()
        if scene.test():
            layer_service.SetScene(scene)

        for i in range(layer_service.Count()):
            if layer_service.Flags(i) == lx.symbol.f_LAYER_MAIN:
                self.primary = layer_service.Item(i)
                break

        if self.initial_drag:
            adjust_tool.SetFlt(9, 1.0e-6)  # how is this different from just setting the attribute?
            return lx.result.TRUE

        self.part = tool_input_event.part
        self.lock_angle = False
        if self.part == ARC_HANDLE_CENTER:
            pass
        elif self.part == ARC_HANDLE_START:
            pass
        elif self.part == ARC_HANDLE_END:
            pass
        else:
            pass

        return lx.result.TRUE

    def tmod_Move(self, vts, adjust):
        pass

    def tmod_Up(self, vts, adjust):
        pass

    def tool_Evaluate(self, vts):
        """ Tool evaluation gets the primary mesh and creates the arc shape on the mesh. """
        vector_stack = lx.object.VectorStack(vts)
        tool_view_event = ToolViewEvent.from_address(vector_stack.Optional(self.offset_view))

        if (tool_view_event.type != lx.symbol.i_VIEWTYPE_3D) and (tool_view_event.type != lx.symbol.i_VIEWTYPE_2D):
            return

        tool_xfrm = ToolXfrm.from_address(vector_stack.Optional(self.offset_xfrm))

        layer_service = lx.service.Layer()
        layer_scan = layer_service.ScanAllocate(
            lx.symbol.f_LAYERSCAN_PRIMARY | lx.symbol.f_LAYERSCAN_WRITEMESH | lx.symbol.f_LAYERSCAN_MARKVERTS)

        # No active mesh available, exit early
        if layer_scan.Count() == 0:
            return

        mesh = layer_scan.MeshEdit(0)
        vert = mesh.PointAccessor()
        poly = mesh.PolygonAccessor()
        vmap = mesh.MeshMapAccessor()

        # NOTE: redundant "safety check" ?
        num_segments = self.segments
        if num_segments < 1:
            num_segments = 1

        num_points = num_segments + 2
        points = lx.object.storage('p', num_points)

        tool_xfrm_vector = (tool_xfrm.v[0], tool_xfrm.v[1], tool_xfrm.v[2])
        v = lxu.vector.sub(self.start, tool_xfrm_vector)
        mInv = (
            (tool_xfrm.mInv[0][0], tool_xfrm.mInv[0][1], tool_xfrm.mInv[0][2]),
            (tool_xfrm.mInv[1][0], tool_xfrm.mInv[1][1], tool_xfrm.mInv[1][2]),
            (tool_xfrm.mInv[2][0], tool_xfrm.mInv[2][1], tool_xfrm.mInv[2][2]),
        )

        pos = matrix_multiply(mInv, v)
        points[0] = vert.New(pos)

        for index in range(num_segments):
            t = (index + 1) / num_segments
            pos = self.get_pos(t, 1.0)
            v = lxu.vector.sub(pos, tool_xfrm_vector)
            pos = matrix_multiply(mInv, v)
            points[index + 1] = vert.New(pos)

        v = lxu.vector.sub(self.center, tool_xfrm_vector)
        pos = matrix_multiply(mInv, v)
        points[num_points-1] = vert.New(pos)

        poly.New(lx.symbol.iPTYP_FACE, points, num_points, 0)

        layer_scan.SetMeshChange(0, lx.symbol.f_MESHEDIT_GEOMETRY)
        layer_scan.Apply()

    def get_pos(self, t: float, scale: float) -> Tuple[float, float, float]:
        """ Compute the arc position for the given fractional t. """
        vector_0 = lxu.vector.sub(self.start, self.center)
        vector_1 = lxu.vector.sub(self.end, self.center)
        vector_2 = lxu.vector.cross(vector_0, vector_1)

        length = lxu.vector.length(vector_2)
        if not length:
            vector_2 = self.axis_vector
            length = lxu.vector.length(vector_2)

        if length > 0.0:
            scale_ = 1.0 / length
            vector_2 = lxu.vector.scale(vector_2, scale_)
            if self.reverse:
                vector_2 = tuple(-x for x in vector_2)
                angle = (math.tau - self.angle) * t
            else:
                angle = self.angle * t

            value_service = lx.service.Value()
            m = lx.object.Matrix(value_service.CreateValue(lx.symbol.sTYPE_MATRIX3))
            m.Set3(matrix_axis_rotation(vector_2, math.sin(angle), math.cos(angle)))

            vector_0 = lxu.vector.scale(vector_0, scale)

            # NOTE: potentially issue with column vs row major matrix, if it looks weird we can try transposing m
            pos = m.MultiplyVector(vector_0)
            pos = lxu.vector.add(pos, self.center)

        else:
            pos = self.start

        return pos

    # Here we will define the methods for lxifc.ToolModel
    def draw_handles(self, vts, stroke, flags):
        pass

    def tmod_Draw(self, vts, stroke, flags):
        self.draw_handles(vts, stroke, flags)

    def tmod_TestType(self, type_):
        if type_ in (lx.symbol.i_VPSPACE_MODEL, lx.symbol.i_VPSPACE_WORLD, lx.symbol.i_VPSPACE_MODEL2D):
            return lx.result.TRUE
        return lx.result.FALSE


lx.bless(ArcTool, "py.prim.arc")
