import lx
import lxu.meta


class Operator(lxu.meta.ChannelModifier):
    def init_chan(self, desc):
        desc.add("startValue", lx.symbol.sTYPE_DISTANCE)
        desc.chmod_value(lx.symbol.fCHMOD_INPUT)

        desc.add("startTime", lx.symbol.sTYPE_TIME)
        desc.chmod_value(lx.symbol.fCHMOD_INPUT)

        desc.add("startSpeed", lx.symbol.sTYPE_SPEED)
        desc.chmod_value(lx.symbol.fCHMOD_INPUT)

        desc.add("acceleration", lx.symbol.sTYPE_ACCELERATION)
        desc.chmod_value(lx.symbol.fCHMOD_INPUT)

        desc.chmod_time()  # FIXME: this crashes Modo

        desc.add("output", lx.symbol.sTYPE_DISTANCE)
        desc.chmod_value(lx.symbol.fCHMOD_OUTPUT)

    def eval(self, chan):
        start_time = chan.startTime.GetFlt()
        start_value = chan.startValue.GetFlt()
        acceleration = chan.acceleration.GetFlt()
        speed = chan.startSpeed.GetFlt()

        """
        time = chan._time.GetFlt()

        if time > start_time:
            time -= start_time
            start_value += speed * time + 0.5 * acceleration * time * time

        """
        chan.output.SetFlt(start_value)


chmod_meta = lxu.meta.Meta_ChannelModifier("py.simple.kinematics", Operator)
lxu.meta.MetaRoot(chmod_meta)
