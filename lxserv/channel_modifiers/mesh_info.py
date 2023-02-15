"""

    Python version of the Channel Modifier, Mesh Info

"""

import lx
import lxifc


SERVER = "py.cmMeshInfo"
GRAPH = SERVER + ".graph"
USER = GRAPH + "UserName"


def get_mesh_change(flag: int):
    """ Check the bitmask for mesh edit changes, and return the list of reported changes. """
    masks = (
        (lx.symbol.f_MESHEDIT_POSITION, "Position"),
        (lx.symbol.f_MESHEDIT_POINTS, "Points"),
        (lx.symbol.f_MESHEDIT_POLYGONS, "Polygons"),
        (lx.symbol.f_MESHEDIT_POL_TAGS, "Polygon Tags"),
        (lx.symbol.f_MESHEDIT_POL_TYPE, "Polygon Type"),
        (lx.symbol.f_MESHEDIT_MAP_CONTINUITY, "Map Continuity"),
        (lx.symbol.f_MESHEDIT_MAP_UV, "Map UV"),
        (lx.symbol.f_MESHEDIT_MAP_MORPH, "Map Morph"),
        (lx.symbol.f_MESHEDIT_MAP_OTHER, "Map Other"),
        (lx.symbol.f_MESHEDIT_UPDATE, "Update"),
        (lx.symbol.f_MESHEDIT_DELTA, "Delta"),
    )
    for mask, name in masks:
        if mask & flag:
            lx.out(name)


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


class Modifier(lxifc.Modifier):
    def __init__(self, item: lx.object.Item, eval: lx.object.Evaluation):
        self.attr = lx.object.Attributes(eval)

        self.item = lx.object.Item()
        self.mesh = lx.object.Mesh()
        self.mesh_tracker = lx.object.MeshTracker()
        self.ident = None

        scene = item.Context()
        if not item.test() and not scene.test():
            return

        # AddChannelName requires that the channel already exists, or will raise LookupError
        self.deformed_index = eval.AddChannelName(item, "deformed", lx.symbol.fECHAN_READ)
        self.world_space_index = eval.AddChannelName(item, "worldSpace", lx.symbol.fECHAN_READ)

        self.points_index = eval.AddChannelName(item, "nPoints", lx.symbol.fECHAN_WRITE)
        self.edges_index = eval.AddChannelName(item, "nEdges", lx.symbol.fECHAN_WRITE)
        self.polygons_index = eval.AddChannelName(item, "nPolygons", lx.symbol.fECHAN_WRITE)
        self.parts_index = eval.AddChannelName(item, "nParts", lx.symbol.fECHAN_WRITE)

        self.graph = lx.object.ItemGraph(scene.GraphLookup(GRAPH))

        if self.graph.RevCount(item):
            item_ = self.graph.RevByIndex(item, 0)
            self.item = item_
            self.ident = item_.Ident()
            channel_read = lx.object.ChannelRead(scene.Channels(lx.symbol.s_ACTIONLAYER_EDIT, 0.0))
            self.mesh = lx.object.Mesh(channel_read.ValueObj(item_, item_.ChannelLookup(lx.symbol.sICHAN_MESH_MESH)))
            self.mesh_tracker = lx.object.MeshTracker(self.mesh.TrackChanges())
            self.mesh_tracker.Start()

    def mod_Test(self, item: lx.object.Unknown, index: int) -> bool:
        """ Test an instance to see if its still valid for the given key. """
        item = lx.object.Item(item)
        scene = item.Context()
        if not item.test() and not scene.test():
            return False

        if self.graph.RevCount(item) > 0:
            item_ = self.graph.RevByIndex(item, 0)
            if self.ident == item_.Ident():
                changes = self.mesh_tracker.Changes()
                get_mesh_change(changes)  # debug print what changed with geo
                return changes & lx.symbol.f_MESHEDIT_GEOMETRY

        return False

    def mod_Evaluate(self):
        if not self.mesh.test():
            return

        vert_count = self.mesh.PointCount()
        edge_count = self.mesh.EdgeCount()
        poly_count = self.mesh.PolygonCount()

        part_count = 0
        poly = self.mesh.PolygonAccessor()
        for i in range(self.mesh.PolygonCount()):
            poly.SelectByIndex(i)
            part_count = max(part_count, poly.Part())
        part_count += 1

        # if we want to calculate the bounds in world space, we will need to get the transform from the item,
        world_space = self.attr.GetInt(self.world_space_index)
        if world_space:
            # TODO: from item, get locator, which can get us a matrix to apply to all point positions,
            lx.out("World Space!")

        vert = self.mesh.PointAccessor()
        for i in range(vert_count):
            vert.SelectByIndex(i)

        self.attr.SetInt(self.points_index, vert_count)
        self.attr.SetInt(self.edges_index, edge_count)
        self.attr.SetInt(self.polygons_index, poly_count)
        self.attr.SetInt(self.parts_index, part_count)


class EvalModifier(lxifc.EvalModifier):
    def __init__(self):
        scene_service = lx.service.Scene()
        self.item_type = scene_service.ItemTypeLookup(SERVER)

        self.scene = lx.object.Scene()
        self.index = 0
        self.count = 0

    def eval_Reset(self, scene):
        self.scene.set(scene)
        self.index = 0
        self.count = self.scene.ItemCount(self.item_type)

    def eval_Next(self):
        if self.index >= self.count:
            return 0, 0
        item = self.scene.ItemByIndex(self.item_type, self.index)
        self.index += 1
        return item, 0

    def eval_Alloc(self, item, index, evaluation):
        return Modifier(lx.object.Item(item), lx.object.Evaluation(evaluation))


class Schematic(lxifc.SchematicConnection, lxifc.SchemaDest):
    def __init__(self):
        scene_service = lx.service.Scene()
        self.item_type = scene_service.ItemTypeLookup(SERVER)
        self.mesh_type = scene_service.ItemTypeLookup("mesh")

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
        item = lx.object.Item(from_obj)
        return item.TestType(self.mesh_type)

    def schm_GraphName(self):
        """ Without this, we seem to never be able to connect the mesh to the input plug. """
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


MeshEditListener()

lx.bless(Schematic, GRAPH, {lx.symbol.sSRV_USERNAME: USER})

lx.bless(EvalModifier, SERVER, {lx.symbol.sMOD_TYPELIST: SERVER, lx.symbol.sMOD_GRAPHLIST: GRAPH})

lx.bless(Manager, SERVER, {
    lx.symbol.sPKG_SUPERTYPE: lx.symbol.sITYPE_CHANMODIFY,
    lx.symbol.sPKG_GRAPHS: GRAPH
})
