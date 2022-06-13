from dataclasses import dataclass
from typing import Tuple

import lx
import lxifc

from .camera_info import CameraInfo


PHI = 1.6180339887499
ONE_OVER_PHI = 0.61803398874989

SPIRAL_A = 1.120529
SPIRAL_B = 0.306349
SPIRAL_CX = 1.17082  # (2PHI+1)/(PHI+2)
SPIRAL_CY = 0.276393  # -1/(PHI+2)


@dataclass
class Rectangle:
    position: tuple = (0.0, 0.0)
    size: tuple = (1.0, 1.77777)


class Instance(lxifc.PackageInstance, lxifc.ViewItem3D):
    """ The instance is the implementation of the item, and there will be one
    allocated for each item in the scene. It can respond to a set of
    events."""
    def __init__(self):
        self.item = lx.object.Item()

        self.camera_type = 0
        self.renderer_type = 0

    def pins_Initialize(self, item, super):
        self.item = lx.object.Item(item)

        # When initializing an instance, we store the item types for camera and renderer, not sure if these are changed
        # often between versions or there is another reason for them not existing in `lx.symbol`
        scene_service = lx.service.Scene()
        self.camera_type = scene_service.ItemTypeLookup(lx.symbol.sITYPE_CAMERA)
        self.renderer_type = scene_service.ItemTypeLookup(lx.symbol.sITYPE_RENDER)

    def vitm_Draw(self, channel_read, stroke_draw, selection_flags, item_color):
        # check to see if we're looking through a camera
        view = lx.object.View(stroke_draw)
        if view.Type() != lx.symbol.iVIEWv_CAMERA:
            return

        cr = lx.object.ChannelRead(channel_read)
        sd = lx.object.StrokeDraw(stroke_draw)

        # Test that the item we've attached this drawing override to is a camera type, or that it's parent is.
        if self.item.TestType(self.camera_type):
            camera = self.item
        else:
            camera = self.item.Parent()
            if not camera.TestType(self.camera_type):
                return

        if not camera.test():
            return

        action_on = cr.Integer(self.item, self.item.ChannelLookup("actionOn"))

        # TODO: these values should all come from reading channels,
        rgb = (0.8, 0.0, 0.8)
        alpha = 1.0

        if action_on:
            sd.Begin(lx.symbol.iSTROKE_TEXT, rgb, alpha)
            sd.Text("Hello", lx.symbol.iTEXT_LEFT)
            sd.Vertex((0.0, 0.0, 0.0), lx.symbol.iSTROKE_ABSOLUTE)


class Package(lxifc.Package, lxifc.ChannelUI):
    """ Packages implement item types, or simple item extensions. They are
    like the metatype object for the item type. They define the common
    set of channels for the item type and spawn new instances.

    """
    def pkg_SetupChannels(self, add_channel):
        """ The package has a set of standard channels with default values. These
        are setup at the start using the AddChannel interface. """

        ac = lx.object.AddChannel(add_channel)
        ac.NewChannel("actionOn", lx.symbol.sTYPE_BOOLEAN)
        ac.SetDefault(0.0, 1)
        ac.NewChannel("actHBorder", lx.symbol.sTYPE_PERCENT)  # border width as percent
        ac.SetDefault(0.05, 0)
        ac.NewChannel("actVBorder", lx.symbol.sTYPE_PERCENT)  # border height as percent
        ac.SetDefault(0.05, 0)

    def pkg_Attach(self):
        """ Attach is called to create a new instance of this item. The returned
        object implements a specific item of this type in the scene."""
        return Instance()

    def pkg_TestInterface(self, guid: str):
        guid_service = lx.service.GUID()
        package_instance = guid_service.Compare(guid, lx.symbol.u_PACKAGEINSTANCE)
        view3d = guid_service.Compare(guid, lx.symbol.u_VIEW3D)
        return package_instance == 0 or view3d == 0

    def cui_Enabled(self, channel_name: str, msg: lx.object.Unknown, item: lx.object.Unknown, channel_read: lx.object.Unknown) -> int:
        """ Much like commands, channels can be disabled through this method. Return lx.result.CMD_DISABLED for disabled
        and lx.result.OK for enabled, any other result codes will be seen as a failure code. """

        if channel_name in ("actHBorder", "actVBorder"):
            i = lx.object.Item(item)
            cr = lx.object.ChannelRead(channel_read)

            actionOn = cr.Integer(i, i.ChannelLookup("actionOn"))
            if actionOn == 1:
                return lx.result.OK

            message = lx.object.Message(msg)
            if message.test():
                message.SetCode(lx.result.CMD_DISABLED)
                message.SetMessage("common", "", 99)
                message.SetArgumentString(1, "Turned off.")

            return lx.result.CMD_DISABLED

    def cui_DependencyCount(self, channel_name: str) -> int:
        """ Channels need to know what other channels this channel depends on to implement the cui_Enable, so we will
        implement cui_DependencyCount and cui_DependencyByIndex to control the enable state. """
        if channel_name in ("actHBorder", "actVBorder"):
            print(channel_name)
            return 1
        else:
            return 0

    def cui_DependencyByIndexName(self, channel_name: str, index: int) -> Tuple[int, str]:
        """ The SDK example was using DependencyByIndex, while the documentation does say this is the preferred method.
        So I opted for using this one over that. """
        if channel_name in ("actHBorder", "actVBorder"):
            return lx.symbol.sITYPE_CAMERA, "actionOn"

# tags = {lx.symbol.sPKG_SUPERTYPE: lx.symbol.sITYPE_LOCATOR}
# currently we can't add it through "Add Item" but have to run
# item.addPackage py.safeAreaOverlay on another item
lx.bless(Package, "py.safeAreaOverlay")
