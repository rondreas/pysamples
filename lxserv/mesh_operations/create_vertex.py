"""

    Python version of pmodel_createVertex.cpp

"""


import lx
import lxifc


SERVER_NAME = "py.create.vertex"


class Instance(lxifc.PackageInstance):
    pass


class Package(lxifc.Package, lxifc.ChannelUI):
    """ Package describing this plug-in.

    Packages are defined by a server interface that describes the channels for the package and adds instances to items.

    """
    def pkg_SetupChannels(self, addChan):
        """ This method is called once when the package is initialized to define the set of channels common to all items
        with this package. """
        add_channel = lx.object.AddChannel(addChan)
        add_channel.NewChannel('position', lx.symbol.sTYPE_DISTANCE)  # starts a new channel definition,

        # storage with three doubles,
        position = lx.object.storage('d', 3)
        position.set((0.0, 0.0, 0.0))

        # setting the vector type to sCHANVEC* will cause this one channel definition to create multiple channels
        # comprising the vector,
        add_channel.SetVector(lx.symbol.sCHANVEC_XYZ)
        add_channel.SetDefaultVec(position)

    def pkg_TestInterface(self, guid):
        """ This method is required so that 'nexus' knows what interfaces instance of this support. """
        return lx.service.GUID().Compare(guid, lx.symbol.u_PACKAGEINSTANCE) == 0

    def pkg_Attach(self):
        """ This method is called for each item to assign as the package is being attached, and should return an object
        implementing PackageInstance. """
        return Instance()


class MeshOperation(lxifc.MeshOperation):
    """ MeshOperation implementation that modifies a mesh by adding a vertex """
    def __init__(self):
        self.position = (0.0, 0.0, 0.0)

    def mop_Evaluate(self, mesh, type, mode):
        """ Evalutate the MeshOp by modifying the input mesh. """
        mesh = lx.object.Mesh(mesh)
        if not mesh.test():
            return

        point = mesh.PointAccessor()
        if not point.test():
            return

        # create a new vertex at position,
        point.New(self.position)
        mesh.SetMeshEdits(lx.symbol.f_MESHEDIT_GEOMETRY)


class ModifierElement(lxifc.Modifier):
    """ A modifier that can create new instances of our MeshOperation """
    def __init__(self, item, evaluation):
        evaluation = lx.object.Evaluation(evaluation)
        self.attr = lx.object.Attributes(evaluation)

        item = lx.object.Item(item)
        if not item.test():
            return

        # Save the indices of the channels so we can query and return values when evaluating the modifier.
        self.position_x_index = evaluation.AddChannelName(item, "position.X", lx.symbol.fECHAN_READ)
        self.position_y_index = evaluation.AddChannelName(item, "position.Y", lx.symbol.fECHAN_READ)
        self.position_z_index = evaluation.AddChannelName(item, "position.Z", lx.symbol.fECHAN_READ)

        # And set meshop as out
        self._output_index = evaluation.AddChannelName(item, lx.symbol.sICHAN_MESHOP_OBJ, lx.symbol.fECHAN_WRITE)

    def mod_Test(self, item, index):
        """ Test if this modifier matches what we would create with EvalModifier.eval_Alloc() """
        item = lx.object.Item(item)
        if not item.test():
            return False

    def mod_Evaluate(self):
        """ Evaluate the modifier to produce a new instance of the MeshOp """
        mesh_operation = MeshOperation()

        value_reference = lx.object.ValueReference(self.attr.Value(self._output_index, 1))
        value_reference.SetObject(mesh_operation)

        position = (  # the attributes object also has a lookup method so we could just get the index from there.
            self.attr.GetFlt(self.position_x_index),
            self.attr.GetFlt(self.position_y_index),
            self.attr.GetFlt(self.position_z_index),
        )

        mesh_operation.position = position


class ModifierServer(lxifc.EvalModifier):
    """ The modifier server is subclassed by the client, and is exported as a server.

    The virtual methods specify the item type to traverse and provide a way to allocate new elements for items in the
    scene """
    def __init__(self):
        self.itemType = lx.service.Scene().ItemTypeLookup(SERVER_NAME)
        self.scene = None
        self.index = 0
        self.count = 0

    def eval_Reset(self, scene):
        self.scene = lx.object.Scene(scene)
        self.index = 0
        self.count = self.scene.ItemCount(self.itemType)

    def eval_Next(self):
        if self.index >= self.count:
            return 0, 0

        item = self.scene.ItemByIndex(self.itemType, self.index)
        self.index += 1

        return item, 0

    def eval_Alloc(self, item, index, evaluation):
        """ For each item this method is used to allocate the modifier node. We spawn the object and store the eval
        context, but the rest is done by the client. """
        return ModifierElement(item, evaluation)


tags = {lx.symbol.sMOD_TYPELIST: SERVER_NAME}
lx.bless(ModifierServer, SERVER_NAME + ".mod", tags)

tags = {  # Trying to match the descInfo[] on the package in the sdk,
    lx.symbol.sPKG_SUPERTYPE: lx.symbol.sITYPE_MESHOP,
    lx.symbol.sPMODEL_SELECTIONTYPES: lx.symbol.sSELOP_TYPE_NONE,
    lx.symbol.sPMODEL_NOTRANSFORM: "."
}
lx.bless(Package, SERVER_NAME, tags)
