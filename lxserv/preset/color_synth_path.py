"""

    Recreating the colorSynthPath from samples.

    Presets are packaged content for Modo, such as a mesh, a material, an environment, kits etc...

    > The Preset Browser is a visual library of pre-defined objects, surfaces, kits, and settings available
    in Modo.

    https://learn.foundry.com/modo/content/help/pages/modo_interface/viewports/utility/preset_browser.html

"""

from time import time

import lx
import lxifc
import lxu.command
import lxu.attributes


COLORPRESET_NAME = "ColorPB"
COLORPRESET_ENTRYNAME = COLORPRESET_NAME+"Entry"
COLORPRESET_PRESETTYPE = COLORPRESET_NAME+"PresetType"
COLORPRESET_PRESETMETRICS = COLORPRESET_NAME+"Metrics"
COLORPRESET_SYNTH = "["+COLORPRESET_NAME+"]"


def sanitize_string(string: str) -> str:
    """ Replace colons with space and any slashes with a bar """
    return string.replace(':', ' ').replace('\\', '|').replace('/', '|')


class ColorPBSyntheticEntry(lxifc.DirCacheSyntheticEntry):  # pylint: disable=too-many-instance-attributes
    """ Synthetic Cache Entry handles each entry. """
    def __init__(self, path: str, name: str, is_file: bool, color=(0.0, 0.0, 0.0)):
        # our path which always starts with [ColorPB]:
        self.path = path
        # our name, this has been sanitized ie colons and slashes removed for use in path.
        self.name = sanitize_string(name)
        # the name without colons and slashes removed.
        self.display_name = name
        # If we're a folder or a file.
        self.is_file = is_file

        self.tooltip = ""  # optional tooltip string.
        self.modtime = time()  # time since we last modified this entry.

        # child 'nodes'
        self.files = []
        self.dirs = []

        self.color = color

    def dcsyne_Path(self) -> str:
        """ Entry path. Always starts with "[ColorPB]:"

        We store the path to the entry and its name separately, so we need to combine them and the root path
        to get the full path.

        """
        full_path = self.path
        if not self.name:
            full_path += ":"

        if self.path[-1] != ":":
            full_path += "/"

        full_path += self.name

        return full_path

    def dcsyne_Name(self):
        """ Name of the preset or the directory. Directories must be separated with forward slashes.
        Return the name portion of the path. This represents the filename of the entry. """
        return self.name

    def dcsyne_DirUsername(self):
        """ Username of the directory as seen in the preset browser. """
        return self.display_name

    def dcsyne_DirCount(self, list_mode: int) -> int:
        """ Get the number of files/dirs inside a directory. List mode is one of vDCELIST_DIRS,
        vDCELIST_FILES or vDCELIST_BOTH. Since BOTH resolves to DIRS | FILES, we just test the bits. """
        count = 0
        if list_mode & lx.symbol.vDCELIST_FILES:
            count += len(self.files)
        if list_mode & lx.symbol.vDCELIST_DIRS:
            count += len(self.dirs)
        return count

    def dcsyne_DirByIndex(self, list_mode: int, index: int):
        """ Get a child entry in a directoy given an index and a list mode. We return dirs then files when
        in BOTH mode. """
        entry = None

        if (list_mode & lx.symbol.vDCELIST_DIRS) and index < len(self.dirs):
            entry = self.dirs[index]
        elif list_mode & lx.symbol.vDCELIST_FILES:
            entry = self.files[index - len(self.dirs)]
        else:
            lx.throw(lx.symbol.e_FAILED)
        return entry

    def dcsyne_IsFile(self):
        """ is entry a directory or a file. Returns true for file or false for dirs. """
        return self.is_file

    def dcsyne_Size(self):  # pylint: disable=no-self-use
        """ Return the 'file size'. We don't have a size so we just return 0.0

        Modo expects a double in order to support file sizes larger than 4gb, but does not expect fractional
        values.
        """
        return 0.0

    def dcsyne_ModTime(self) -> str:
        """ Check the time in order to know if the entry has changed. """
        return str(int(self.modtime))

    def update_modtime(self):
        """ Update modtime to now """
        self.modtime = time()


class ColorPBSynthetic(lxifc.DirCacheSynthetic):
    """ Synthetic cache is managing the different entries, from the root path of [ColorPB]: entries are
    ColorPBSyntheticEntry instances.

    Synthetics are only instanced once.

    """

    _root: ColorPBSyntheticEntry

    @classmethod
    def lookup(cls, path: str) -> ColorPBSyntheticEntry:
        """ Get a synthetic entry by it's path. SynthGetEntry in the cpp example, but avoiding the recursion
        and as the function was only used inside the dcsyn_Lookup"""
        if not path.startswith(COLORPRESET_SYNTH):
            lx.throw(lx.symbol.e_NOTFOUND)

        # return root if path matches root,
        if path in (COLORPRESET_SYNTH, COLORPRESET_SYNTH + ":"):
            return cls._root

        # split the path to get each level in the tree
        _, relative_path = path.split(":", 1)

        current = cls._root
        if '/' in relative_path:
            for part in relative_path.split('/'):
                for file in current.files:
                    if part == file.name:
                        current = file

                for directory in current.dirs:
                    if part == directory.name:
                        current = directory
        else:
            for file in current.files:
                if relative_path == file.name:
                    current = file

            for directory in current.dirs:
                if relative_path == directory.name:
                    current = directory

        return current

    def __init__(self):
        # path, but not including the :
        self.root = ColorPBSyntheticEntry(COLORPRESET_SYNTH, "", False)

        self.root.files = [
            ColorPBSyntheticEntry(f"{COLORPRESET_SYNTH}:", "red", True, color=(1.0, 0.0, 0.0)),
            ColorPBSyntheticEntry(f"{COLORPRESET_SYNTH}:", "green", True, color=(0.0, 1.0, 0.0)),
            ColorPBSyntheticEntry(f"{COLORPRESET_SYNTH}:", "blue", True, color=(0.0, 0.0, 1.0)),
        ]

        # assign tooltips,
        for file, tooltip in zip(self.root.files, ("roses are red", "grass is green", "blue is a mood")):
            file.tooltip = tooltip

        self.root.dirs = [
            ColorPBSyntheticEntry(path=f"{COLORPRESET_SYNTH}:", name="pastels", is_file=False),
            ColorPBSyntheticEntry(path=f"{COLORPRESET_SYNTH}:", name="cmyk", is_file=False)
        ]

        self.root.dirs[0].files = [
            ColorPBSyntheticEntry(
                f"{COLORPRESET_SYNTH}:pastels",
                "moss",
                True,
                color=((248/255), (243/255), (230/255))
            ),
            ColorPBSyntheticEntry(
                f"{COLORPRESET_SYNTH}:pastels",
                "salmon",
                True,
                color=((248 / 255), (219 / 255), (184 / 255))
            ),
        ]

        self.root.dirs[1].files = [
            ColorPBSyntheticEntry(f"{COLORPRESET_SYNTH}:cmyk", "cyan", True, color=(0.0, 1.0, 1.0)),
            ColorPBSyntheticEntry(f"{COLORPRESET_SYNTH}:cmyk", "magenta", True, color=(1.0, 0.0, 1.0)),
            ColorPBSyntheticEntry(f"{COLORPRESET_SYNTH}:cmyk", "yellow", True, color=(1.0, 1.0, 0.8)),
            ColorPBSyntheticEntry(f"{COLORPRESET_SYNTH}:cmyk", "key", True, color=(0.0, 0.0, 0.0)),
        ]

        ColorPBSynthetic._root = self.root

    def dcsyn_Lookup(self, path: str) -> ColorPBSyntheticEntry:  # pylint: disable=no-self-use
        """ Lookup for synthetic entry from path. The path will always start with [ColorPB]: or else it
        wouldn't be in our hierarchy. """
        return ColorPBSynthetic.lookup(path)

    def dcsyn_Root(self):
        """ Get the synthetic root, which matches the path [ColorPB]: """
        print("Getting Root")
        return self.root


lx.bless(
    ColorPBSynthetic,
    COLORPRESET_NAME,
    {lx.symbol.sDCSYNTH_BACKING: lx.symbol.sDCSYNTH_BACKING_MEMORY}
)


class ColorPresetType(lxifc.PresetType):
    """ The preset type for a synthetic is just like one for an on-disk preset. We only recognize presets
    that start with our root path [ColorPB]:.

    There is no need to look at the contents of the "file", because anything in that path is defined by
    ours. """
    def ptyp_Recognize(self, path: str) -> str:  # pylint: disable=no-self-use
        """ Recognize 'claims' any path that starts with [ColorPB]: and should return the category name."""
        if not path.startswith(COLORPRESET_SYNTH):
            lx.notimpl()
        return COLORPRESET_SYNTH

    def ptyp_Do(self, path: str):  # pylint: disable=no-self-use
        """ When double-clicked, or run through preset.do this is called to apply the color. We simply call
        color.hdrValue for each of the RGB components which automatically sets the color on whatever target
        is selected by the user.

        This is the same as would be targetet by the color picket itself.

        We do this from a command block so that is looks like a single call to the command history,
        and this can be undone with one ctrl-z."""
        entry = ColorPBSynthetic.lookup(path)
        if not entry:
            lx.throw(lx.symbol.e_NOTFOUND)

        command_service = lx.service.Command()
        command_service.BlockBegin("Do ColorPB Preset", lx.symbol.fCMDBLOCK_UI)

        for i in range(3):
            command_service.ExecuteArgString(
                -1,
                lx.symbol.iCTAG_NULL,
                f"color.hdrValue axis:{i} value:{entry.color[i]}"
            )

        command_service.BlockEnd()


    # pylint: disable=too-many-arguments,unused-argument,no-self-use
    def ptyp_Metrics(self,
                     path: str,
                     flags: int,
                     width: int,
                     height: int,
                     previous_metrics: lx.object.Unknown):
        """ Generating metrics is only needed if the previous metrics provided were null.

        Our metrics don't change so if non-null we can just return the previous metrics again. If there are
        no previous metrics, we create new metrics and return those instead.

        The flags indicate the kind of information request by the dir cache. If ..."""
        if previous_metrics.test():
            print(f"previous metrics: {previous_metrics}")
            if not flags & lx.symbol.iPBMETRICS_THUMBNAIL_IMAGE:
                print("Here we should return a previously stored metric!")

        entry = ColorPBSynthetic.lookup(path)
        return ColorPresetMetrics(entry, width, height)

    def ptyp_GenericThumbnailResource(self, path: str):  # pylint: disable=no-self-use
        """ The generic thumbnails is defined as an image resource in the configs, and is used when the
        preset doesn't define its own thumbnail image or the image isn't ready yet. We just want to use
        a generic one but really this will never be called for our presets... """
        return "item.thumbnail.undefined"


lx.bless(ColorPresetType, COLORPRESET_PRESETTYPE, {
    lx.symbol.sSRV_USERNAME: "Colors (Synth)",  # Username of the preset browser, should be defined in
                                                # message table
    lx.symbol.sPBS_CATEGORY: COLORPRESET_NAME,  # Preset category,
    lx.symbol.sPBS_CANAPPLY: "false",           # don't support Apply(), legacy replaced with drop servers,
    lx.symbol.sPBS_CANDO: "true",               # supports Do(), double-clicking on the preset fires
                                                # preset.do command
    lx.symbol.sPBS_DYNAMICTHUMBNAILS: "true",   # Thumbnail is dynamic, do not cache it to disc always ask
                                                # for new thumb
    lx.symbol.sPBS_SYNTHETICSUPPORT: "true"     # supports synthetic paths. If false only works on real
                                                # files on disk
})


class ColorPresetMetrics(lxifc.PresetMetrics):
    """ Metrics return specific information for a given preset.

    This includes the metadata (name/description/caption) metadata and markup.

    Metadata is defined as being an inherent property of the file, such as its name, author, creation date
    and so on, while markup is defined by the user of the preset, such as start ratings or favorites."""
    def __init__(self, entry, width, height):
        self.entry = entry
        self.width = width
        self.height = height

        self.metadata = lxu.attributes.DynamicAttributes()
        self.metadata.dyna_Add(lx.symbol.sPBMETA_LABEL, lx.symbol.sTYPE_STRING)
        self.metadata.attr_SetString(0, entry.display_name)

        self.metadata.dyna_Add(lx.symbol.sPBMETA_CAPTION, lx.symbol.sTYPE_STRING)
        self.metadata.attr_SetString(1, entry.display_name)

        if entry.tooltip:
            self.metadata.dyna_Add(lx.symbol.sPBMETA_TOOLTIP, lx.symbol.sTYPE_STRING)
            self.metadata.attr_SetString(2, entry.tooltip)

    def pmet_Flags(self) -> int:  # pylint: disable=no-self-use
        """ This allows for per-file flags override with iDCFM_ flags. The only flag currently avaiable
        is iDCFM_DYNAMIC_THUMBNAILS and we provided that as part of our server definition, so we don't
        need to provide it again for each file."""
        return 0

    def pmet_Metadata(self):
        """ Meta data is an attribute object that contains common properties like name, caption and tooltip. """
        if not self.metadata:
            lx.notimpl()
        return self.metadata

    def pmet_ThumbnailImage(self):
        """ Generate our thumbnail image. """
        image_service = lx.service.Image()
        image = image_service.Create(32, 32, lx.symbol.iIMP_RGBFP, 0)

        if not image.test():
            lx.throw(lx.symbol.e_NOTFOUND)

        write_image = lx.object.ImageWrite(image)
        color = lx.object.storage('f', 3)
        color.set(self.entry.color)
        for i in range(32):
            for j in range(32):
                write_image.SetPixel(i, j, lx.symbol.iIMP_RGBFP, color)

        return image

    def pmet_ThumbnailIdealSize(self):  # pylint: disable=no-self-use
        """ Return the ideal size of the thumbnail. Since colors have no size we return 0 to indicate that we
        can accomodate any size requested.

        If we used a thumbnail embedded in a preset file, we might return the dimensions of that thumbnail
        instead. """
        return 0, 0
