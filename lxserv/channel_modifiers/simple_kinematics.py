"""

    Python copy of cmSimpleKinematics.cpp, the C++ version already should exist in Modo and can be found as
    "Simple Kinematics" among the Channel Modifiers.

"""


import lx
import lxu.meta
import lxu.attrdesc


class Operator(lxu.meta.ChannelModifier):
    def init_chan(self, desc: lxu.attrdesc.AttributeDesc):
        desc.add("startValue", lx.symbol.sTYPE_DISTANCE)
        desc.chmod_value(0)

        desc.add("startTime", lx.symbol.sTYPE_TIME)
        desc.chmod_value(0)

        desc.add("startSpeed", lx.symbol.sTYPE_SPEED)
        desc.chmod_value(0)

        desc.add("acceleration", lx.symbol.sTYPE_ACCELERATION)
        desc.chmod_value(0)

        # desc.chmod_time()  # NOTE: this crashes Modo, it forgets to set chmod_flags to 0

        # Doing what chmod_time should be doing,
        # not using the default name of -time- as I don't know how I would access later
        desc.add("time", lx.symbol.sTYPE_TIME)
        desc._cur.is_channel = False
        desc._cur.chmod_type = 4
        desc._cur.chmod_flags = 0

        desc.add("output", lx.symbol.sTYPE_DISTANCE)
        desc.chmod_value(lx.symbol.fCHMOD_OUTPUT)

    def eval(self, chan: lxu.attrdesc.AttributeDescData):
        start_time = chan.startTime.GetFlt()
        start_value = chan.startValue.GetFlt()
        acceleration = chan.acceleration.GetFlt()
        speed = chan.startSpeed.GetFlt()

        time = chan.time.GetFlt()
        if time >= start_time:
            time -= start_time
            start_value += speed * time + 0.5 * acceleration * time * time

        chan.output.SetFlt(start_value)


chmod_meta = lxu.meta.Meta_ChannelModifier("py.simple.kinematics", Operator)
lxu.meta.MetaRoot(chmod_meta)
