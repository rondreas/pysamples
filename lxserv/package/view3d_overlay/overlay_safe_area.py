from dataclasses import dataclass

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
    def __init__(self):
        self.item = lx.object.Item()

    def pins_Initialize(self, item, super):
        self.item = lx.object.Item(item)

    def vitm_Draw(self, channel_read, stroke_draw, selection_flags, item_color):
        # guess we do a check first to see if we're looking through a camera
        view = lx.object.View(stroke_draw)
        if view.Type() != lx.symbol.iVIEWv_CAMERA:
            return

        # cr = lx.object.ChannelRead(channel_read)
        sd = lx.object.StrokeDraw(stroke_draw)
        if not sd.test():
            return

        sd.Begin(lx.symbol.iSTROKE_TEXT, (1.0, 1.0, 1.0), 1.0)
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

    def pkg_Attach(self):
        return Instance()

    def pkg_TestInterface(self, guid: str):
        guid_service = lx.service.GUID()
        package_instance = guid_service.Compare(guid, lx.symbol.u_PACKAGEINSTANCE)
        view3d = guid_service.Compare(guid, lx.symbol.u_VIEW3D)
        return package_instance == 0 or view3d == 0


# tags = {lx.symbol.sPKG_SUPERTYPE: lx.symbol.sITYPE_LOCATOR}
# currently we can't add it through "Add Item" but have to run
# item.addPackage py.safeAreaOverlay on another item
lx.bless(Package, "py.safeAreaOverlay")
