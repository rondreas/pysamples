import lx

from enum import Enum
from typing import Tuple


class CameraFilmfit(Enum):
    FILL = 0
    VERTICAL = 1
    HORIZONTAL = 2
    OVERSCAN = 3


class CameraInfo(object):
    def __init__(self, camera: lx.object.Item):
        self.valid = False

        # Python doesn't do headers, so here we just thunder through and set initial values for all properties
        self.aperture_x = 1.0
        self.aperture_y = 1.0
        self.focal_length = 0.01
        self.focus_distance = 1.0
        self.target_distance = 1.0
        self.fstop = 1.0
        self.eye_separation = 0.01
        self.convergence_distance = 1.0
        self.film_fit = 1
        self.offset_x = 1.0
        self.offset_y = 1.0
        self.render_x = 1.0
        self.render_y = 1.0
        self.overscan = 0.0
        self.pixel_aspect = 1.0
        """ projection types can be one among the following "symbols"
        
        #define LXiICVAL_CAMERA_PROJTYPE_PERSP		    0
        #define LXiICVAL_CAMERA_PROJTYPE_ORTHO		    1
        #define LXiICVAL_CAMERA_PROJTYPE_CYLINDRICAL	2
        #define LXiICVAL_CAMERA_PROJTYPE_CYLINDRICALVR	3
        #define LXiICVAL_CAMERA_PROJTYPE_SPHERICAL	    4
        #define LXiICVAL_CAMERA_PROJTYPE_SPHERICALVR	5
        
        """
        self.projection_type = 1
        self.use_sensor = False

        # Create a float3 storage object which will hold position data, we set that to zero
        self.position = lx.object.storage('f', 3)
        self.position.set((0.0, 0.0, 0.0))

        # Create two matrices, one for the the transform and another for it's inverse
        # initially as identity matrices.
        value_service = lx.service.Value()
        self.xfrm = lx.object.Matrix(value_service.CreateValue(lx.symbol.sTYPE_MATRIX4))
        self.xfrm.SetIdentity()
        self.xfrm_inverse = lx.object.Matrix(value_service.CreateValue(lx.symbol.sTYPE_MATRIX4))
        self.xfrm_inverse.SetIdentity()

        self.camera = camera

    def read_camera_channels(self, chan: lx.object.ChannelRead):
        """ Read channels from camera item """

        """ To get a channel read, we can get the context from the camera to get the scene,
        then from scene create the channel reader like this
        
        scene = self.camera.Context()
        selection_service = lx.service.Selection()
        chan = lx.object.ChannelRead(scene.Channels(None, selection_service.GetTime()))
        
        """

        self.aperture_x = chan.Double(self.camera, self.camera.ChannelLookup(lx.symbol.sICHAN_CAMERA_APERTUREX))
        self.aperture_y = chan.Double(self.camera, self.camera.ChannelLookup(lx.symbol.sICHAN_CAMERA_APERTUREY))

        self.focal_length = chan.Double(self.camera, self.camera.ChannelLookup(lx.symbol.sICHAN_CAMERA_FOCALLEN))
        self.focus_distance = chan.Double(self.camera, self.camera.ChannelLookup(lx.symbol.sICHAN_CAMERA_FOCUSDIST))
        self.fstop = chan.Double(self.camera, self.camera.ChannelLookup(lx.symbol.sICHAN_CAMERA_FSTOP))

        self.eye_separation = chan.Double(self.camera, self.camera.ChannelLookup(lx.symbol.sICHAN_CAMERA_IODIST))
        self.convergence_distance = chan.Double(self.camera, self.camera.ChannelLookup(lx.symbol.sICHAN_CAMERA_CONVDIST))

        self.film_fit = chan.Integer(self.camera, self.camera.ChannelLookup(lx.symbol.sICHAN_CAMERA_FILMFIT))
        self.projection_type = chan.Integer(self.camera, self.camera.ChannelLookup(lx.symbol.sICHAN_CAMERA_PROJTYPE))
        self.offset_x = chan.Double(self.camera, self.camera.ChannelLookup(lx.symbol.sICHAN_CAMERA_OFFSETX))
        self.offset_y = chan.Double(self.camera, self.camera.ChannelLookup(lx.symbol.sICHAN_CAMERA_OFFSETY))
        self.target_distance = chan.Double(self.camera, self.camera.ChannelLookup(lx.symbol.sICHAN_CAMERA_TARGET))

        # Get the resolution, either from camera override or the renderer in the scene.
        self.pixel_aspect = 1.0
        resolution_override = chan.Integer(self.camera, self.camera.ChannelLookup(lx.symbol.sICHAN_CAMERA_RESOVERRIDE))
        if resolution_override:
            self.render_x = chan.Integer(self.camera, self.camera.ChannelLookup(lx.symbol.sICHAN_CAMERA_RESX))
            self.render_y = chan.Integer(self.camera, self.camera.ChannelLookup(lx.symbol.sICHAN_CAMERA_RESY))
        else:
            scene = self.camera.Context()
            renderer = scene.AnyItemOfType(lx.symbol.sITYPE_POLYRENDER)
            self.render_x = chan.Integer(renderer, renderer.ChannelLookup(lx.symbol.sICHAN_POLYRENDER_RESX))
            self.render_y = chan.Integer(renderer, renderer.ChannelLookup(lx.symbol.sICHAN_POLYRENDER_RESY))
            self.pixel_aspect = chan.Double(renderer, renderer.ChannelLookup(lx.symbol.sICHAN_POLYRENDER_PASPECT))

        # Get the world transform for the camera,
        _obj = chan.ValueObj(self.camera, self.camera.ChannelLookup(lx.symbol.sICHAN_XFRMCORE_WORLDMATRIX))
        _matrix = lx.object.Matrix(_obj)  # the matrix read from channels are Read Only, in effect
        self.xfrm.Set4(_matrix.Get4())  # copy over the values to our property

        self.position.set(_matrix.GetOffset())

        # copy and invert the world transform matrix,
        self.xfrm_inverse.Set4(_matrix.Get4())
        self.xfrm_inverse.Invert()

        # If we made it all the way here, set the instance to valid,
        self.valid = True

    def fit_aperture(self):
        """ Compute the effective aperture given image resolution and film fit modes """

        camera_aspect_ratio = self.aperture_x / self.aperture_y
        film_aspect_ratio = self.pixel_aspect * self.render_x / self.render_y

        # TODO: sort out this mess, could likely be written more clearly
        if camera_aspect_ratio > film_aspect_ratio:
            if self.film_fit in (CameraFilmfit.FILL, CameraFilmfit.VERTICAL):
                self.aperture_x *= film_aspect_ratio / camera_aspect_ratio
            elif self.film_fit in (CameraFilmfit.HORIZONTAL, CameraFilmfit.OVERSCAN):
                self.aperture_y *= camera_aspect_ratio / film_aspect_ratio

        elif film_aspect_ratio > camera_aspect_ratio:
            if self.film_fit in (CameraFilmfit.FILL, CameraFilmfit.VERTICAL):
                self.aperture_y *= camera_aspect_ratio / film_aspect_ratio
            elif self.film_fit in (CameraFilmfit.HORIZONTAL, CameraFilmfit.OVERSCAN):
                self.aperture_x *= film_aspect_ratio / camera_aspect_ratio

    def get_zooms(self) -> Tuple[float, float]:
        if not self.use_sensor:
            self.fit_aperture()

        zoom_x = 0.5 / self.focal_length
        zoom_y = zoom_x * self.aperture_y
        zoom_x *= self.aperture_x

        return zoom_x, zoom_y

    def uv_to_cam3D(self, uv: Tuple[float, float], z: float) -> Tuple[float, float, float]:
        """ Find the 3D position in camera coordinates at depth z, of a spot in the camera view/render"""
        x = 2 * uv[0] - 1.0  # convert from 0..1 range to -1..1
        y = 2 * uv[1] - 1.0

        zx, zy = self.get_zooms()

        v = abs(z)

        return v * zx * x, v * zy * y, z

    def cam3D_to_uv(self, position: Tuple[float, float, float]) -> Tuple[float, float]:
        """ Find the position in the camera view/render of a 3D position in camera coords,
        raises RuntimeError for positions not visible """
        z = abs(position[2])

        zoom_x, zoom_y = self.get_zooms()

        u = position[0] / (zoom_x * z)
        v = position[1] / (zoom_y * z)

        u = (u + 1.0) / 2.0
        v = (v + 1.0) / 2.0

        if not 0.0 <= u <= 1.0 and 0.0 <= v <= 1.0 and 0.0 <= position[2]:
            raise RuntimeError("Position is not inside of camera frustum")

        return u, v

    def world_to_uv(self, position: Tuple[float, float, float]) -> Tuple[float, float]:
        """ get image plane coords in u,v=(0-1)"""
        cpos = self.xfrm_inverse.MultiplyVector(position)
        return self.cam3D_to_uv(cpos)

    def uv_to_world(self, uv: Tuple[float, float], z: float) -> Tuple[float, float, float]:
        """ compute 3D position of screen spot at given depth """
        cpos = self.uv_to_cam3D(uv, z)
        return self.xfrm.MultiplyVector(cpos)
