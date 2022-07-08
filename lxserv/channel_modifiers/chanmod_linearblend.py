"""

    cmLinearBlend.cpp

"""

import lx
import lxu.meta
import lxu.attrdesc


class Operator(lxu.meta.ChannelModifier):
    def init_chan(self, desc: lxu.attrdesc.AttributeDesc):
        # Call add() to add a new attribute with a name and type. This becomes
        # the current attribute and further methods can customize the attribute.
        desc.add("inputA", lx.symbol.sTYPE_FLOAT)
        # Set the channel as an input or output of a channel modifier.
        desc.chmod_value(lx.symbol.fCHMOD_INPUT)

        desc.add("inputB", lx.symbol.sTYPE_FLOAT)
        desc.chmod_value(lx.symbol.fCHMOD_INPUT)

        desc.add("blend", lx.symbol.sTYPE_PERCENT)
        desc.chmod_value(lx.symbol.fCHMOD_INPUT)
        # Set the text hints for encoding int values.
        # The C++ calls the "older" api .hint(...) which basically just calls the newer set_hint
        # desc.set_hint([(0, "%min"), (1000, "%max")]) # <-- Does nothing that I can tell
        desc.set_min(0.0)
        desc.set_max(1.0)

        desc.add("output", lx.symbol.sTYPE_FLOAT)
        desc.chmod_value(lx.symbol.fCHMOD_OUTPUT)

    def eval(self, chan):
        a = chan.inputA.GetFlt()
        b = chan.inputB.GetFlt()
        mix = chan.blend.GetFlt()

        chan.output.SetFlt(a + min(max(mix, 0.0), 1.0) * (b - a))


chmod_meta = lxu.meta.Meta_ChannelModifier("py.chanmod.linearblend", Operator)
lxu.meta.MetaRoot(chmod_meta)
