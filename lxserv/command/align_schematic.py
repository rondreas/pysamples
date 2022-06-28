"""

    Python version of cc_command_alignschema.cpp

"""

from __future__ import annotations
from typing import Tuple

import lx
import lxu.command


class Command(lxu.command.BasicCommand):
    """ Implements a command which will align the y position of all nodes in a workspace to that of the currently
    selected item. """
    def __init__(self):
        lxu.command.BasicCommand.__init__(self)

    @staticmethod
    def get_selected_item() -> lx.object.Item:
        """ Get the first selected item or raises LookupError """
        selection_service = lx.service.Selection()
        item_translation_packet = lx.object.ItemPacketTranslation(
            selection_service.Allocate(lx.symbol.sSELTYP_ITEM)
        )
        packet = selection_service.Recent(lx.symbol.iSEL_ITEM)
        return item_translation_packet.Item(packet)

    @staticmethod
    def get_schematic_group(item: lx.object.Item) -> Tuple[lx.object.SchematicGroup, lx.object.SchematicNode]:
        """ Given an item, search all group items in scene testing against schematic group interface then attempting
        to find the node for the item.

        Return group and node for the item or raise LookupError

        """
        schematic_group = lx.object.SchematicGroup()
        scene = item.Context()  # type: lx.object.Scene
        group_type = lx.service.Scene().ItemTypeLookup(lx.symbol.sITYPE_GROUP)  # type: int
        group_count = scene.ItemCount(group_type)  # type: int
        for group_index in range(group_count):
            group_item = scene.ItemByIndex(group_type, group_index)  # type: lx.object.Item
            if not schematic_group.set(group_item):  # see if the item has the interface for schematic group or skip
                continue

            node_count = schematic_group.NodeCount()  # type: int
            for node_index in range(node_count):
                schematic_node = schematic_group.NodeByIndex(node_index)  # type: lx.object.SchematicNode
                item_ = schematic_node.Item()  # type: lx.object.Item
                if item_.Ident() == item.Ident():  # if we've found the node for the input item, return group and node
                    return schematic_group, schematic_node

        raise LookupError("Failed to find schematic group and node")

    def basic_Execute(self, message: lxu.object.Message, flags: int):  # pylint: disable=invalid-name, unused-argument
        """ Overridden method,

        Using our utility methods, align nodes along y-coordinates in same schematic as the selected item

        """
        try:
            item = self.get_selected_item()  # Get the first selected item,
        except LookupError:
            message.SetCode(lx.result.FAILED)
            message.SetMessage('common', '', 99)
            message.SetArgumentString(1, "No selected item")
            return

        try:
            group, node = self.get_schematic_group(item)  # Find a schematic group item where item is present,
        except LookupError as exception:
            message.SetCode(lx.result.FAILED)
            message.SetMessage('common', '', 99)
            message.SetArgumentString(1, str(exception))
            return

        _, y = node.Position()  # Get the y position for the selected item's node,

        # For each other node in that schematic group, set their y position to match
        for node_index in range(group.NodeCount()):
            node_ = group.NodeByIndex(node_index)  # type: lx.object.SchematicNode
            x, _ = node_.Position()
            node_.SetPosition(x, y)


lx.bless(Command, "py.align.schematic")
