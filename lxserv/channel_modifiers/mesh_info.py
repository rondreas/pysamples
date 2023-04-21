"""

    Python version of the Channel Modifier, Mesh Info

"""

from math import sqrt

import lx
import lxifc
import lxu

SERVER = "py.cmMeshInfo"  # the name of our item,
GRAPH = SERVER + ".graph"  # the name of our schematic graph


def square_distance(a, b) -> float:
    """ Get the squared distance between to points """
    return sum((x-y)**2 for x, y in zip(a, b))


def distance(a, b) -> float:
    """ Get the distance between two points """
    return sqrt(square_distance(a, b))


def triangle_area(a, b, c) -> float:
    """ Using Herons formula - get the area for a triangle
    for a,b,c uv positions. """
    # Get the length for each edge
    ab = distance(a, b)
    bc = distance(b, c)
    ca = distance(c, a)

    # Get the half of triangle perimeter
    s = (ab + bc + ca) / 2.0

    # Return the surface area
    return sqrt(s * (s-ab) * (s-bc) * (s-ca))


class Instance(lxifc.PackageInstance):
    pass


class Manager(lxifc.Package, lxifc.ChannelModManager):
    def pkg_SetupChannels(self, addChan):
        """ The SetupChannels() method is called once when the package is initialized to define the set of channels
        common to all item with this package. """
        add_channel = lx.object.AddChannel(addChan)

        add_channel.NewChannel("deformed", lx.symbol.sTYPE_BOOLEAN)
        add_channel.SetDefault(0.0, 0)
        add_channel.NewChannel("worldSpace", lx.symbol.sTYPE_BOOLEAN)
        add_channel.SetDefault(0.0, 0)

        add_channel.NewChannel("nPoints", lx.symbol.sTYPE_INTEGER)
        add_channel.SetDefault(0.0, 0)
        add_channel.NewChannel("nEdges", lx.symbol.sTYPE_INTEGER)
        add_channel.SetDefault(0.0, 0)
        add_channel.NewChannel("nPolygons", lx.symbol.sTYPE_INTEGER)
        add_channel.SetDefault(0.0, 0)

        add_channel.NewChannel("nParts", lx.symbol.sTYPE_INTEGER)
        add_channel.SetDefault(0.0, 0)

        add_channel.NewChannel("surfaceArea", lx.symbol.sTYPE_DISTANCE)
        add_channel.SetDefault(0.0, 0)

        default_vector = lx.object.storage("d", 3)
        default_vector.set((0.0, 0.0, 0.0))

        add_channel.NewChannel("boundsMin", lx.symbol.sTYPE_DISTANCE)
        add_channel.SetVector(lx.symbol.sCHANVEC_XYZ)
        add_channel.SetDefaultVec(default_vector)

        add_channel.NewChannel("boundsMax", lx.symbol.sTYPE_DISTANCE)
        add_channel.SetVector(lx.symbol.sCHANVEC_XYZ)
        add_channel.SetDefaultVec(default_vector)

        add_channel.NewChannel("size", lx.symbol.sTYPE_DISTANCE)
        add_channel.SetVector(lx.symbol.sCHANVEC_XYZ)
        add_channel.SetDefaultVec(default_vector)

        add_channel.NewChannel("center", lx.symbol.sTYPE_DISTANCE)
        add_channel.SetVector(lx.symbol.sCHANVEC_XYZ)
        add_channel.SetDefaultVec(default_vector)

        add_channel.NewChannel("boundingBox", lx.symbol.sTYPE_BOOLEAN)
        add_channel.SetDefault(0.0, 0)
        add_channel.NewChannel("dimensions", lx.symbol.sTYPE_BOOLEAN)
        add_channel.SetDefault(0.0, 0)

    def pkg_TestInterface(self, guid):
        return guid == lx.symbol.u_PACKAGEINSTANCE

    def pkg_Attach(self):
        """ The Attach() method is called for each item to assign as the package is being attached, and should return
        an object implementing ILxPackageInstance."""
        return Instance()

    def cman_Define(self, cmod: lx.object.Unknown):
        """ The Define() method is passed a ChannelModSetup interface and is expected to call AddChannel() or AddTime()
        methods on that object to add the channels it wants for reading and writing. The names are all for channels on
        items of this type, and may be set as inputs or outputs."""
        setup = lx.object.ChannelModSetup(cmod)

        setup.AddChannel("nPoints", lx.symbol.fCHMOD_OUTPUT)
        setup.AddChannel("nEdges", lx.symbol.fCHMOD_OUTPUT)
        setup.AddChannel("nPolygons", lx.symbol.fCHMOD_OUTPUT)
        setup.AddChannel("nParts", lx.symbol.fCHMOD_OUTPUT)
        setup.AddChannel("surfaceArea", lx.symbol.fCHMOD_OUTPUT)

        setup.AddChannel("boundsMin.X", lx.symbol.fCHMOD_OUTPUT)
        setup.AddChannel("boundsMin.Y", lx.symbol.fCHMOD_OUTPUT)
        setup.AddChannel("boundsMin.Z", lx.symbol.fCHMOD_OUTPUT)

        setup.AddChannel("boundsMax.X", lx.symbol.fCHMOD_OUTPUT)
        setup.AddChannel("boundsMax.Y", lx.symbol.fCHMOD_OUTPUT)
        setup.AddChannel("boundsMax.Z", lx.symbol.fCHMOD_OUTPUT)

        setup.AddChannel("size.X", lx.symbol.fCHMOD_OUTPUT)
        setup.AddChannel("size.Y", lx.symbol.fCHMOD_OUTPUT)
        setup.AddChannel("size.Z", lx.symbol.fCHMOD_OUTPUT)

        setup.AddChannel("center.X", lx.symbol.fCHMOD_OUTPUT)
        setup.AddChannel("center.Y", lx.symbol.fCHMOD_OUTPUT)
        setup.AddChannel("center.Z", lx.symbol.fCHMOD_OUTPUT)


class Modifier(lxifc.Modifier):
    def __init__(self, item: lx.object.Item, eval: lx.object.Evaluation):
        # Get the scene this modifier is added to, and test that both scene and this modifier is valid.
        scene = item.Context()
        if not item.test() and not scene.test():
            return

        self.attr = lx.object.Attributes(eval)
        self.item = lx.object.Item()
        # self.mesh = lx.object.Mesh()
        # self.mesh_tracker = lx.object.MeshTracker()
        self.ident = None

        self.graph = lx.object.ItemGraph(scene.GraphLookup(GRAPH))
        if self.graph.RevCount(item):
            self.item = self.graph.RevByIndex(item, 0)
            self.ident = self.item.Ident()

        # AddChannelName requires that the channel already exists, or will raise LookupError
        self.deformed_index = eval.AddChannelName(item, "deformed", lx.symbol.fECHAN_READ)
        self.world_space_index = eval.AddChannelName(item, "worldSpace", lx.symbol.fECHAN_READ)

        self.points_index = eval.AddChannelName(item, "nPoints", lx.symbol.fECHAN_WRITE)
        self.edges_index = eval.AddChannelName(item, "nEdges", lx.symbol.fECHAN_WRITE)
        self.polygons_index = eval.AddChannelName(item, "nPolygons", lx.symbol.fECHAN_WRITE)
        self.parts_index = eval.AddChannelName(item, "nParts", lx.symbol.fECHAN_WRITE)
        self.surface_area_index = eval.AddChannelName(item, "surfaceArea", lx.symbol.fECHAN_WRITE)

        self.bounds_min_x_index = eval.AddChannelName(item, "boundsMin.X", lx.symbol.fECHAN_WRITE)
        self.bounds_min_y_index = eval.AddChannelName(item, "boundsMin.Y", lx.symbol.fECHAN_WRITE)
        self.bounds_min_z_index = eval.AddChannelName(item, "boundsMin.Z", lx.symbol.fECHAN_WRITE)

        self.bounds_max_x_index = eval.AddChannelName(item, "boundsMax.X", lx.symbol.fECHAN_WRITE)
        self.bounds_max_y_index = eval.AddChannelName(item, "boundsMax.Y", lx.symbol.fECHAN_WRITE)
        self.bounds_max_z_index = eval.AddChannelName(item, "boundsMax.Z", lx.symbol.fECHAN_WRITE)

        self.size_x_index = eval.AddChannelName(item, "size.X", lx.symbol.fECHAN_WRITE)
        self.size_y_index = eval.AddChannelName(item, "size.Y", lx.symbol.fECHAN_WRITE)
        self.size_z_index = eval.AddChannelName(item, "size.Z", lx.symbol.fECHAN_WRITE)

        self.center_x_index = eval.AddChannelName(item, "center.X", lx.symbol.fECHAN_WRITE)
        self.center_y_index = eval.AddChannelName(item, "center.Y", lx.symbol.fECHAN_WRITE)
        self.center_z_index = eval.AddChannelName(item, "center.Z", lx.symbol.fECHAN_WRITE)

        if self.item.test():
            self.mesh_index = eval.AddChannelName(self.item, lx.symbol.sICHAN_MESH_MESH, lx.symbol.fECHAN_READ)
            self.xfrm_index = eval.AddChannelName(self.item, lx.symbol.sICHAN_XFRMCORE_WORLDMATRIX, lx.symbol.fECHAN_READ)
        else:
            self.mesh_index, self.xfrm_index = 0, 0

    def mod_Test(self, item: lx.object.Unknown, index: int) -> bool:
        """ Test an instance to see if its still valid for the given key. """
        return False

    def mod_Evaluate(self):
        if not (self.mesh_index and self.xfrm_index):
            return

        mesh_stack = self.attr.Value(self.mesh_index, False)
        mesh_filter = lx.object.MeshFilter(mesh_stack)
        if not mesh_filter.test():
            return

        mesh = mesh_filter.Generate()
        if not mesh.test():
            return

        matrix_object = self.attr.Value(self.xfrm_index, False)
        matrix = lx.object.Matrix(matrix_object)

        # if we want to calculate the bounds in world space, we will need to get the transform from the item,
        world_space = self.attr.GetInt(self.world_space_index)

        vert_count = mesh.PointCount()
        edge_count = mesh.EdgeCount()
        poly_count = mesh.PolygonCount()

        min_bounds = tuple((float("inf"),) * 3)
        max_bounds = tuple((-float("inf"),) * 3)

        part_count = 0
        surface_area = 0.0
        poly = mesh.PolygonAccessor()
        vert = mesh.PointAccessor()
        for i in range(mesh.PolygonCount()):
            poly.SelectByIndex(i)
            part_count = max(part_count, poly.Part())
            if world_space:
                for j in range(poly.GenerateTriangles()):
                    a, b, c = poly.TriangleByIndex(j)

                    vert.Select(a)
                    a_pos = matrix.MultiplyVector(vert.Pos())
                    min_bounds = tuple(min(x, y) for x, y in zip(min_bounds, a_pos))
                    max_bounds = tuple(max(x, y) for x, y in zip(max_bounds, a_pos))

                    vert.Select(b)
                    b_pos = matrix.MultiplyVector(vert.Pos())
                    min_bounds = tuple(min(x, y) for x, y in zip(min_bounds, b_pos))
                    max_bounds = tuple(max(x, y) for x, y in zip(max_bounds, b_pos))

                    vert.Select(c)
                    c_pos = matrix.MultiplyVector(vert.Pos())
                    min_bounds = tuple(min(x, y) for x, y in zip(min_bounds, c_pos))
                    max_bounds = tuple(max(x, y) for x, y in zip(max_bounds, c_pos))

                    surface_area += triangle_area(a_pos, b_pos, c_pos)
            else:
                surface_area += poly.Area()

        part_count += 1  # parts start counting from zero

        if not world_space:
            min_bounds, max_bounds = mesh.BoundingBox(lx.symbol.iMARK_ANY)

        size = tuple(b - a for a, b in zip(min_bounds, max_bounds))
        center = tuple((a + b) * 0.5 for a, b in zip(min_bounds, max_bounds))

        self.attr.SetInt(self.points_index, vert_count)
        self.attr.SetInt(self.edges_index, edge_count)
        self.attr.SetInt(self.polygons_index, poly_count)
        self.attr.SetInt(self.parts_index, part_count)
        self.attr.SetFlt(self.surface_area_index, surface_area)

        self.attr.SetFlt(self.bounds_min_x_index, min_bounds[0])
        self.attr.SetFlt(self.bounds_min_y_index, min_bounds[1])
        self.attr.SetFlt(self.bounds_min_z_index, min_bounds[2])

        self.attr.SetFlt(self.bounds_max_x_index, max_bounds[0])
        self.attr.SetFlt(self.bounds_max_y_index, max_bounds[1])
        self.attr.SetFlt(self.bounds_max_z_index, max_bounds[2])

        self.attr.SetFlt(self.size_x_index, size[0])
        self.attr.SetFlt(self.size_y_index, size[1])
        self.attr.SetFlt(self.size_z_index, size[2])

        self.attr.SetFlt(self.center_x_index, center[0])
        self.attr.SetFlt(self.center_y_index, center[1])
        self.attr.SetFlt(self.center_z_index, center[2])


class EvalModifier(lxifc.EvalModifier):
    """ Modifiers have two forms. The modifier class is a plug-in server of type ILxEvalModifier. This provides methods
    for creating modifier instances which operate on specific channels. The instance is an object that caches specific
    references to input and output channels and can perform computations over them. For example there is only one "IK"
    ILxEvalModifier server, but it will create instances to evaluate IK for all locators with parents.

    Each instance is identified by a key channel. The class interface provides methods for enumerating through key
    channels and creating and testing instances."""
    def __init__(self):
        scene_service = lx.service.Scene()
        self.item_type = scene_service.ItemTypeLookup(SERVER)

        self.scene = lx.object.Scene()
        self.index = 0
        self.count = 0

    def eval_Reset(self, scene):
        """ Set the modifier class to the given scene, and reset the count of key channels for the Next() method."""
        self.scene.set(scene)
        self.index = 0
        self.count = self.scene.ItemCount(self.item_type)

    def eval_Next(self):
        """ Returns the item and index for the next key channel for this modifier in the current scene. If the last one
        has already been read, this method returns null."""
        if self.index >= self.count:
            return 0, 0
        item = self.scene.ItemByIndex(self.item_type, self.index)
        self.index += 1
        return item, 0

    def eval_Alloc(self, item, index, evaluation):
        """ Create a new instance for the given key channel.  The eval object allows the instance to create references
        to the channels it wants to be able to read and write, and to cache the attributes interface needed to read
        their values during evaluation."""
        return Modifier(lx.object.Item(item), lx.object.Evaluation(evaluation))


class Schematic(lxifc.SchematicConnection):
    """ A SchematicConnection server manages a particular connection point for inter-item relations. Normally this is a
    graph link but can be any type of relation that the client wants to implement. The name of the connection point
    (the text shown on the node) is the name of the server."""
    def __init__(self):
        scene_service = lx.service.Scene()
        self.item_type = scene_service.ItemTypeLookup(SERVER)  # item type we want to add the schematic graph to
        self.mesh_type = scene_service.ItemTypeLookup("mesh")  # item type we want to accept as input

    def schm_ItemFlags(self, item) -> int:
        """ A SchematicConnection server manages a particular connection point for inter-item relations. Normally this
        is a graph link but can be any type of relation that the client wants to implement. The name of the connection
        point (the text shown on the node) is the name of the server.

        This method is called for every item displayed in the schematic to determine if and how it supports this
        connection point. Failure or a zero flags value means that the item does not have a connection."""
        item = lx.object.Item(item)
        if item.Type() == self.item_type:
            return lx.symbol.fSCON_SINGLE
        return 0

    def schm_AllowConnect(self, from_obj, to_obj) -> bool:
        """ Given a pair of items, this function returns LXe_TRUE if the connection is allowed. The 'to' item is the one
        with the connection point, and is assumed to have valid item flags, above."""
        item = lx.object.Item(from_obj)
        return item.TestType(self.mesh_type)

    def schm_GraphName(self):
        """ This returns the name of a single graph. For connection points that can be described by one graph the graph
        name is sufficient for schematic to do all the legwork. Connecting adds a link from the source to the target in
        the graph, and drawing just enumerates the graph. """
        return GRAPH


class MeshEditListener(lxifc.SceneItemListener):
    """ Listener to invalidate the Modifier whenever a mesh has been edited. """
    def __init__(self):
        self.listenerService = lx.service.Listener()
        self.COM_object = lx.object.Unknown(self)
        self.listenerService.AddListener(self.COM_object)

    def __del__(self):
        self.listenerService.RemoveListener(self.COM_object)

    def sil_ChannelValue(self, action, item, index):
        if action != "edit":
            return

        # if a mesh has been edited, invalidate all mesh info modifiers
        item = lx.object.Item(item)
        if item.ChannelType(index) == 4:  # TODO: guessing I need to find the sICHAN_MESH_MESH lookup value,
            scene = item.Context()
            scene.EvalModInvalidate(SERVER)


MeshEditListener()  # instantiate our listener to mesh edits invalidates the eval modifier

lx.bless(Schematic, GRAPH, {lx.symbol.sSRV_USERNAME: "Mesh"})
lx.bless(EvalModifier, SERVER, {lx.symbol.sMOD_TYPELIST: SERVER, lx.symbol.sMOD_GRAPHLIST: GRAPH})
lx.bless(Manager, SERVER, {lx.symbol.sPKG_SUPERTYPE: lx.symbol.sITYPE_CHANMODIFY, lx.symbol.sPKG_GRAPHS: GRAPH})
