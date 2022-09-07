"""

    cc_falloff_box.cpp

"""


import lx
import lxu.meta
import lxu.object
import lxu.attrdesc


class Channels(lxu.meta.Channels):
    def init_chan(self, desc: lxu.attrdesc.AttributeDesc):
        desc.add("distance", lx.symbol.sTYPE_BOOLEAN)


chan_meta = lxu.meta.Meta_Channels(Channels)


class Falloff(lxu.meta.Falloff, Channels):
    def weight_local(self, pos):
        lx.out(f"weight_local: {pos}")
        if any(abs(x) > 1.0 for x in pos):
            return 0.0

        if (self.distance):
            return 1.0 - (abs(pos[0]) + abs(pos[1]) + abs(pos[2]) / 3.0)

        return 1.0


class ViewItem3D(lxu.meta.ViewItem3D):
    def draw(self, chanread, stroke, flags, color):
        alpha = 1.0 if (flags & lx.symbol.iSELECTION_SELECTED) else 0.5
        stroke.BeginW(lx.symbol.iSTROKE_BOXES, color, alpha, 2*alpha)
        stroke.Vertex3(-1.0, -1.0, -1.0, lx.symbol.iSTROKE_ABSOLUTE)
        stroke.Vertex3(1.0, 1.0, 1.0, lx.symbol.iSTROKE_ABSOLUTE)


class Modifier(lxu.meta.EvalModifier, lxu.meta.ObjectEvaluation):
    def bind(self, item: lxu.object.Item, ident: int):
        self.mod_add_chan(item, lx.symbol.sICHAN_XFRMCORE_WORLDMATRIX)

    def init_obj(self, mod: lxu.meta.EvalModifier, obj):
        lx.out(f"init_obj: mod = {type(mod)} obj = {type(obj)}")
        obj = mod.mod_read_attr()
        xfrm = mod.mod_cust_value(0)
        obj.world_inverse = xfrm.inverse()


pkg_meta = lxu.meta.Meta_Package("py.falloff.box")
v3d_meta = lxu.meta.Meta_ViewItem3D(ViewItem3D)

mod_meta = lxu.meta.Meta_EvalModifier("py.falloff.box", Modifier)
eval_meta = lxu.meta.Meta_ObjectEvaluation(lx.symbol.sICHAN_FALLOFF_FALLOFF)

fall_meta = lxu.meta.Meta_Falloff(Falloff)


class Root(lxu.meta.MetaRoot):
    def pre_init(self):
        pkg_meta.set_supertype(lx.symbol.sITYPE_FALLOFF)
        fall_meta.set_local()

        self.add(chan_meta)
        self.add(pkg_meta)
        self.add(mod_meta)

        pkg_meta.add(v3d_meta)

        mod_meta.add(eval_meta)
        eval_meta.add(fall_meta)

        return False


root_meta = Root()
