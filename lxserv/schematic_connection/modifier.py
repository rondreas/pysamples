"""

    Python implementation of cc_schema_modifier

"""
import lx
import lxu
import lxu.meta
import lxu.attrdesc


ITEM = "py.schema.modItem"
GRAPH = "py.schema.modGraph"
EVAL = "py.schema.modifier"


class Package(lxu.meta.Package):
    def synth_name(self) -> str:
        return "Graph Test Item"


class Channels(lxu.meta.Channels):
    def init_chan(self, desc: lxu.attrdesc.AttributeDesc):
        desc.add("channelCount", lx.symbol.sTYPE_INTEGER)
        desc.default_val(0)


class Eval(lxu.meta.EvalModifier):
    def __init__(self):
        self.item = lx.object.Item()
        self.cached_name = ""
        self.itemNameChannelID = 0

    def bind(self, item, ident):
        self.item.set(item)
        self.mod_add_chan(item, "channelCount", lx.symbol.fECHAN_WRITE)

    def current_link(self) -> lx.object.Item:
        graph = lx.object.ItemGraph()

        if self.item.test():
            scene = self.item.Context()
            scene_graph = scene.GraphLookup(GRAPH)
            graph.set(scene_graph)
            if graph.RevCount(self.item):
                linked_item = lx.object.Item(graph.RevByIndex(self.item, 0))
                if linked_item.test():
                    return linked_item

    def change_test(self):
        item = self.current_link()
        if item:
            return item.Ident() == self.cached_name

    def eval(self):
        channel_count = 0
        item = self.current_link()
        if item:
            channel_count = item.ChannelCount()

        value = self.mod_cust_write(self.itemNameChannelID)
        value.SetInt(channel_count)


channels_meta = lxu.meta.Meta_Channels(Channels)
package_meta = lxu.meta.Meta_Package(ITEM, Package)
schematic_meta = lxu.meta.Meta_SchematicConnection(GRAPH)
eval_meta = lxu.meta.Meta_EvalModifier(EVAL, Eval)

package_meta.set_supertype(lx.symbol.sITYPE_LOCATOR)
package_meta.add_tag(lx.symbol.sPKG_GRAPHS, GRAPH)

schematic_meta.set_itemtype(ITEM)
schematic_meta.set_graph(GRAPH)

eval_meta.add_dependent_graph(GRAPH)

lxu.meta.MetaRoot(channels_meta, package_meta, schematic_meta, eval_meta)
