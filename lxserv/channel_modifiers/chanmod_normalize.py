import lx
import lxu.meta
import lxu.object
import lxu.vector
import lxu.attrdesc


class Operator(lxu.meta.ChannelModifier):
    def init_chan(self, desc: lxu.attrdesc.AttributeDesc):
        desc.add('input', lx.symbol.sTYPE_FLOAT)
        desc.chmod_value(lx.symbol.fCHMOD_INPUT)
        desc.vector_type(lx.symbol.sCHANVEC_XYZ)

        desc.add('output', lx.symbol.sTYPE_FLOAT)
        desc.chmod_value(lx.symbol.fCHMOD_OUTPUT)
        desc.vector_type(lx.symbol.sCHANVEC_XYZ)

    def eval(self, chan: lxu.attrdesc.AttributeDescData):
        x, y, z = list(map(lxu.object.Value.GetFlt, chan.input))
        vector = lxu.vector.normalize((x, y, z))
        for value, value_object in zip(vector, chan.output):
            value_object.SetFlt(value)


chmod_meta = lxu.meta.Meta_ChannelModifier("py.chanmod.normalize", Operator)
lxu.meta.MetaRoot(chmod_meta)
