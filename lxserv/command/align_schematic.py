"""

    Python version of cc_command_alignschema.cpp

"""

from __future__ import annotations
from typing import Tuple

import lx
import lxu.command


class Command(lxu.command.BasicCommand):
    def __init__(self):
        lxu.command.BasicCommand.__init__(self)

    @staticmethod
    def get_selected_item() -> lx.object.Item:
        """ Utility method for 'keeping things organized' """
        selection_service = lx.service.Selection()
        item_translation_packet = lx.object.ItemPacketTranslation(
            selection_service.Allocate(lx.symbol.sSELTYP_ITEM)
        )
        packet = selection_service.Recent(lx.symbol.iSEL_ITEM)
        return item_translation_packet.Item(packet)

    @staticmethod
    def get_schematic_group(item: lx.object.Item) -> Tuple[lx.object.SchematicGroup, lx.object.SchematicNode]:
        schematic_group = lx.object.SchematicGroup()
        scene = item.Context()
        group_type = lx.service.Scene().ItemTypeLookup(lx.symbol.sITYPE_GROUP)
        group_count = scene.ItemCount(group_type)
        for group_index in range(group_count):
            group_item = scene.ItemByIndex(group_type, group_index)
            if not schematic_group.set(group_item):
                continue

            node_count = schematic_group.NodeCount()
            for node_index in range(node_count):
                schematic_node = schematic_group.NodeByIndex(node_index)  # type: lx.object.SchematicNode
                item_ = schematic_node.Item()  # type: lx.object.Item
                if item_.Ident() == item.Ident():
                    return schematic_group, schematic_node

    def basic_Execute(self, msg: lxu.object.Message, flags: int):
        item = self.get_selected_item()
        group, node = self.get_schematic_group(item)

        _, y = node.Position()
        for node_index in range(group.NodeCount()):
            node_ = group.NodeByIndex(node_index)  # type: lx.object.SchematicNode
            x, _ = node_.Position()
            node_.SetPosition(x, y)


lx.bless(Command, "py.align.schematic")
