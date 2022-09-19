import lx
import lxu
import lxu.meta
import lxu.select
import lxu.object


class Drop(lxu.meta.Drop):
    def __init__(self):
        super(Drop, self).__init__()
        self.drag_list = lx.object.ValueArray()
        self.drop_item = lx.object.Drop()

    def recognize_array(self, array: lxu.object.ValueArray):
        for index in range(array.Count()):
            reference = array.GetValue(index)  # type: lx.object.Value
            if reference.TypeName() == "&item":
                item_id = reference.GetString()
                item = lxu.select.SceneSelection().current().ItemLookup(item_id)  # type: lx.object.Item
                if item.TestType(lx.symbol.i_CIT_LOCATOR):
                    self.drag_list.set(array)
                    return True

        return False

    def enabled(self, destination):
        # Attempting to "cast" the destination to LocatorDest object,
        # if it raises no interface, well it's not supported.
        try:
            locator_destination = lxu.object.LocatorDest(destination)
            if locator_destination.test():
                self.drop_item = locator_destination.Item()
                return True

        except Exception as e:
            return False

    def perform_drop(self):
        """ Copy the size of the destination locator, to change all items being dragged. """
        command_service = lx.service.Command()
        selection_service = lx.service.Selection()

        command_service.BlockBegin("python Drop Actions", 0)

        mode = "set"
        scene = lxu.select.SceneSelection().current()

        # TODO: We should make this section into a function, as it's same used for recognize
        for index in range(self.drag_list.Count()):
            reference = self.drag_list.GetValue(index)
            if reference.TypeName() == "&item":
                item_id = reference.GetString()
                item = scene.ItemLookup(item_id)  # type: lx.object.Item
                if item.TestType(lx.symbol.i_CIT_LOCATOR):
                    flag, _, command = command_service.SpawnFromString(f"select.item {item_id} {mode}")
                    command.Execute(flag)
                    mode = "add"

        channel_read = lx.object.ChannelRead(scene.Channels(None, selection_service.GetTime()))
        size = channel_read.Double(self.drop_item, self.drop_item.ChannelLookup(lx.symbol.sICHAN_LOCATOR_SIZE))

        flag, _, command = command_service.SpawnFromString(f"item.channel {lx.symbol.sICHAN_LOCATOR_SIZE} {size}")
        command.Execute(flag)

        command_service.BlockEnd()


class DropAction(lxu.meta.DropAction):
    def exec_act(self):
        self._drop.perform_drop()


drop_meta = lxu.meta.Meta_Drop("py.drop.items", Drop)


class Root(lxu.meta.MetaRoot):
    def pre_init(self):
        drop_meta.set_source_type(lx.symbol.sDROPSOURCE_ITEMS)
        drop_meta.add_action("copySize", DropAction())
        self.add(drop_meta)
        return False


root_meta = Root()
