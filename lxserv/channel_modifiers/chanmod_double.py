"""

    This implements a ChannelModifier server with one input and one output.

    Modifier can be added in schematic and wired up to an input. The output will
    be twice the input.

"""


import lx
import lxu.meta


class Operator(lxu.meta.ChannelModifier):
    """ The Operator is the core of the channel modifier. It both sets up the
    channels for the modifier and serves as the object to hold onto value
    interfaces.

    """
    def init_chan(self, desc):
        """ init_chan() is called once to initialize the channels of the modifier.

        We add the channels with required name and type. Channel modifier inputs
        and outputs are associated with Value wrappers in the class itself.

        The INPUT and OUTPUT flags tell the schematic which side to put the dot.

        """
        desc.add('input', lx.symbol.sTYPE_FLOAT)
        desc.chmod_value(lx.symbol.fCHMOD_INPUT)

        desc.add('output', lx.symbol.sTYPE_FLOAT)
        desc.chmod_value(lx.symbol.fCHMOD_OUTPUT)

    def eval(self, chan):
        """ eval() is called to perform operation. Inputs and outputs are bound
        and can be read and written.

        Read out input float and output twice its value to the result.

        """
        in_value = chan.input.GetFlt()
        chan.output.SetFlt(in_value * 2.0)


chmod_meta = lxu.meta.Meta_ChannelModifier("py.chanmod.double", Operator)
lxu.meta.MetaRoot(chmod_meta)
