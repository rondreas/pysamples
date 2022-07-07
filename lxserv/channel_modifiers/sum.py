"""

    Python version of cc_chanmod_sum.cpp, implements a channel modifier with one input which accommodates multiple input
    links and one output.

    To test add in a schematic and connect multiple float inputs, the output will be the sum of all linked input
    channels.

"""


import lx
import lxu.meta
import lxu.attrdesc


class Operator(lxu.meta.ChannelModifier):
    def init_chan(self, desc: lxu.attrdesc.AttributeDesc):
        # add an ValueArray of floats that we can access in eval
        desc.add("input", lx.symbol.sTYPE_FLOAT)
        desc.chmod_array(lx.symbol.fCHMOD_INPUT)

        desc.add("output", lx.symbol.sTYPE_FLOAT)
        desc.chmod_value(lx.symbol.fCHMOD_OUTPUT)

    def eval(self, chan: lxu.attrdesc.AttributeDescData):
        output = 0.0
        for i in range(chan.input.Count()):
            output += chan.input.GetFloat(i)
        chan.output.SetFlt(output)


chmod_meta = lxu.meta.Meta_ChannelModifier("py.sum", Operator)
lxu.meta.MetaRoot(chmod_meta)
