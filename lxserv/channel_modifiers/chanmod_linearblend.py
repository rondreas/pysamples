"""

    cmLinearBlend.cpp

"""

import lx
import lxu.meta


class Operator(lxu.meta.ChannelModifier):
    def init_chan(self, desc):
        desc.add("inputA", lx.symbol.sTYPE_FLOAT)
        desc.chmod_value(lx.symbol.fCHMOD_INPUT)

        desc.add("inputB", lx.symbol.sTYPE_FLOAT)
        desc.chmod_value(lx.symbol.fCHMOD_INPUT)

        desc.add("blend", lx.symbol.sTYPE_PERCENT)
        desc.chmod_value(lx.symbol.fCHMOD_INPUT)
        desc.set_hint([(0, "%min"), (10000, "%max")])

        desc.add("output", lx.symbol.sTYPE_FLOAT)
        desc.chmod_value(lx.symbol.fCHMOD_OUTPUT)

    def eval(self, chan):
        a = chan.inputA.GetFlt()
        b = chan.inputB.GetFlt()
        mix = chan.blend.GetFlt()

        chan.output.SetFlt(a + min(max(mix, 0.0), 1.0) * (b - a))


chmod_meta = lxu.meta.Meta_ChannelModifier("py.chanmod.linearblend", Operator)
lxu.meta.MetaRoot(chmod_meta)
