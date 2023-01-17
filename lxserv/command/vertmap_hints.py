"""

    Example of how to use the UI Hints to create a drop down menu where users can select available vertex maps for the
    currently selected item.

"""

import lx
import lxu.command


class Command(lxu.command.BasicCommand):
    def __init__(self):
        lxu.command.BasicCommand.__init__(self)
        self.dyna_Add("map", lx.symbol.sTYPE_VERTMAPNAME)

    def arg_UIHints(self, index: int, hints: lx.object.UIHints):
        """ Set the UI Hints for the argument, we will mostly be using default values but doing explicitly with
        docstring from the SDK. """
        if index == 0:
            # The type of vertex map. Default is UV map.
            hints.VertmapType(lx.symbol.i_VMAP_TEXTUREUV)

            # Specifies when a value of (none) is allowed in the list. Default is TRUE.
            hints.VertmapAllowNone(True)

            # Specifies that the list is only generated from the selected item. Default is FALSE.
            hints.VertmapItemMode(True)

    def basic_Execute(self, msg, flags):
        """ Print the texture map user selected from the ui hints or tell them they didn't select anything. """
        vmap_name = self.dyna_String(0)
        if vmap_name:
            print(f"You selected {vmap_name}")
        else:
            print("You didn't select any vertex map!")


lx.bless(Command, "py.vmap.hints")

