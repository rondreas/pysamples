"""

    Attempting to recreate the cc_chanmod_double.cpp from sdk samples.

    Found useful hints in how to implement looking at 

        extra/scripts/lxserv/stringEncode.py

    Found this is already made in the official sdk also

        https://modosdk.foundry.com/wiki/Channel_Modifier_Python_Wrapper

"""


import lx
from lxu import chanmod


class Operator(chanmod.Operator):
    def initialize(self, desc):
        desc.add('input', lx.symbol.sTYPE_FLOAT)
        desc.chmod_value(lx.symbol.fCHMOD_INPUT)

        desc.add('output', lx.symbol.sTYPE_FLOAT)
        desc.chmod_value(lx.symbol.fCHMOD_OUTPUT)

    def eval(self, chans):
        in_value = chans.input.GetFlt()
        chans.output.SetFlt(in_value * 2.0)


class Package(chanmod.MetaPackage):
    def operator(self):
        return Operator()


# this will call lx.bless but with tags that are required
# for channel modifiers.
chanmod.bless_server(Package, "py.chanmod.double")
