"""

    Example of how to use the UI Value Hints to create a drop down menu where users can select available mesh items.

"""

import lx
import lxifc
import lxu.command


class Hints(lxifc.UIValueHints):
    def uiv_Flags(self) -> int:
        return lx.symbol.fVALHINT_ITEMS | lx.symbol.fVALHINT_ITEMS_NONE

    def uiv_ItemTest(self, item: lx.object.Unknown) -> bool:
        item_ = lx.object.Item(item)
        scene_service = lx.service.Scene()
        mesh_type = scene_service.ItemTypeLookup(lx.symbol.sITYPE_MESH)
        return item_.TestType(mesh_type)


class Command(lxu.command.BasicCommand):
    def __init__(self):
        lxu.command.BasicCommand.__init__(self)
        self.dyna_Add("item", "&item")

    def arg_UIValueHints(self, index):
        if index == 0:
            return Hints()

    def cmd_DialogInit(self):
        if not self.dyna_IsSet(0):
            self.attr_SetString(0, "(none)")

    def basic_Execute(self, msg, flags):
        selected_mesh = self.dyna_String(0, "(none)")
        print(f"You selected {selected_mesh}")


lx.bless(Command, "py.item.hints")

