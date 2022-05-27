"""

    Python attempt of: samples/mesh_operations/create_vertex/pmodel_createVertex.cpp

    Useful link:
        https://modosdk.foundry.com/wiki/Mesh_Operation_-_Manual_implementation
        https://modosdk.foundry.com/wiki/Mesh_Operation_-_Automatic_implementation
        https://gist.github.com/rockjail/b83396872463990fdf4e01a2f1c6f83d

    So it seem the manual implementation of a mesh op is

    EvalModifier ( server )
        v
    Modifier ( modifier element )
        v
    MeshOperation ( mesh op )

"""


import lx
import lxu
import lxifc

import lxu.package
import lxu.attributes


SRVNAME = "py.pmodel.createVertex"


class Instance(lxifc.PackageInstance):
    pass


class Package(lxifc.Package, lxifc.ChannelUI):
    def pkg_SetupChannels(self, addChan):
        addChan = lx.object.AddChannel(addChan)
        addChan.NewChannel('position', lx.symbol.sTYPE_DISTANCE)

        # storage with three doubles,
        position = lx.object.storage('d', 3)

        # set their values,
        position[0] = 0.0
        position[1] = 0.0
        position[2] = 0.0

        # set the default vector value,
        addChan.SetVector(lx.symbol.sCHANVEC_XYZ)
        addChan.SetDefaultVec(position)

    def pkg_TestInterface(self, guid):
        return lx.service.GUID().Compare(guid, lx.symbol.u_PACKAGEINSTANCE) == 0

    def pkg_Attach(self):
        return Instance()


class MeshOperation(lxifc.MeshOperation):
    def __init__(self):
        self.position = (0.0, 0.0, 0.0)

    def mop_Evaluate(self, mesh, type, mode):
        mesh = lx.object.Mesh(mesh)
        if not mesh.test():
            return

        point = lx.object.Point(mesh.PointAccessor())
        if not point.test():
            return

        # create a new vertex at position,
        point_id = point.New(self.position)
        mesh.SetMeshEdits(lx.symbol.f_MESHEDIT_GEOMETRY)


class ModifierElement(lxifc.Modifier):
    def __init__(self, item, evaluation):
        evaluation = lx.object.Evaluation(evaluation)
        self.attr = lx.object.Attributes(evaluation)

        item = lx.object.Item(item)
        if not item.test():
            return

        # Add inputs,
        self._posX_index = evaluation.AddChannelName(item, "position.X", lx.symbol.fECHAN_READ)
        self._posY_index = evaluation.AddChannelName(item, "position.Y", lx.symbol.fECHAN_READ)
        self._posZ_index = evaluation.AddChannelName(item, "position.Z", lx.symbol.fECHAN_READ)

        # And set meshop as out
        self._output_index = evaluation.AddChannelName(item, lx.symbol.sICHAN_MESHOP_OBJ, lx.symbol.fECHAN_WRITE)

    def mod_Test(self, item, index):
        item = lx.object.Item(item)
        if not item.test():
            return False

    def mod_Evaluate(self):
        meshOp = MeshOperation()

        val_ref = lx.object.ValueReference(self.attr.Value(self._output_index, 1))
        val_ref.SetObject(meshOp)

        position = (
            self.attr.GetFlt(self._posX_index),
            self.attr.GetFlt(self._posY_index),
            self.attr.GetFlt(self._posZ_index),
        )

        meshOp.position = position


class ModifierServer(lxifc.EvalModifier):
    def __init__(self):
        self.itemType = lx.service.Scene().ItemTypeLookup(SRVNAME)

    def eval_Reset(self, scene):
        self.scene = lx.object.Scene(scene)
        self.index = 0
        self.count = self.scene.ItemCount(self.itemType)

    def eval_Next(self):
        if self.index >= self.count:
            return (0,0)

        item = self.scene.ItemByIndex(self.itemType, self.index)
        self.index += 1

        return (item, 0)

    def eval_Alloc(self, item, index, evaluation):
        return ModifierElement(item, evaluation)


tags = {lx.symbol.sMOD_TYPELIST: SRVNAME}
lx.bless(ModifierServer, SRVNAME + ".mod", tags)

tags = { # Trying to match the descInfo[] on the package in the sdk,
    lx.symbol.sPKG_SUPERTYPE: lx.symbol.sITYPE_MESHOP,
    lx.symbol.sPMODEL_SELECTIONTYPES: lx.symbol.sSELOP_TYPE_NONE,
    lx.symbol.sPMODEL_NOTRANSFORM: "."
}
lx.bless(Package, SRVNAME, tags)
