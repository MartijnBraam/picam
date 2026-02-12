import threading

import mmap
import numpy as np
from PIL import Image
from picamera2.previews import NullPreview

try:
    # If available, use pure python kms package
    import kms as pykms
except ImportError:
    import pykms


class Connector:
    def __init__(self, name):
        self.name = name
        self._resman = None
        self._conn = None
        self._crtc = None
        self.ready = False
        self._plane = None
        self.num_overlays = 0
        self.overlay = []
        self.overlay_fb = {}
        self.width = 0
        self.height = 0
        self.overlay_pos = []

        self.overlay_dirty = {}

    def configure(self, resman, width, height, rate, layers):
        self.num_overlays = layers
        self._conn = resman.reserve_connector(self.name)
        self._crtc = resman.reserve_crtc(self._conn)
        self._resman = resman
        self.width = width
        self.height = height
        for i in range(layers):
            self.overlay_pos.append((0, 0, width, height))

        if width is not None and height is not None and rate is not None:
            mode = self._conn.get_default_mode()
            mode.hdisplay = width
            mode.vdisplay = height
            mode.vrefresh = rate
            self._crtc.set_mode(self._conn, mode)

    def start(self, width, height, pixel_format):
        fmt = None
        if pixel_format == "XBGR8888":
            fmt = pykms.PixelFormat.XBGR8888
        elif pixel_format == "YUV420":
            fmt = pykms.PixelFormat.YUV420
        self._plane = self._resman.reserve_overlay_plane(self._crtc, format=fmt)
        for i in range(0, self.num_overlays):
            layer = self._resman.reserve_overlay_plane(self._crtc, format=pykms.PixelFormat.ABGR8888)
            layer.set_prop("pixel blend mode", 1)
            layer.set_prop("alpha", 0xFFFF)
            self.overlay.append(layer)
            self.overlay_dirty[i] = False
        self.ready = True

    def overlay_position(self, idx, x, y, w, h):
        self.overlay_pos[idx] = (x, y, w, h)
        if idx in self.overlay_fb and self.overlay_fb[idx] is not None:
            self.overlay_dirty[idx] = True

    def overlay_opacity(self, idx, opacity):
        val = int(float(0xFFFF) * opacity)
        self.overlay[idx].set_prop("alpha", val)


class DRMOutput(NullPreview):
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.card = pykms.Card()
        self.resman = pykms.ResourceManager(self.card)
        self.conn = {}
        self.lock = threading.Lock()
        self.current = None
        self.own_current = False
        self.drmfbs = {}

        super().__init__(width=width, height=height)

    def handle_request(self, picam2):
        picam2.process_requests(self)

    def use_output(self, name, width=None, height=None, rate=None, overlays=0):
        c = Connector(name)
        c.configure(self.resman, width, height, rate, overlays)
        self.conn[name] = c
        return c

    def render_request(self, completed_request):
        """Draw the camera image using DRM."""
        with self.lock:
            self.render_drm(self.picam2, completed_request)
            if self.current and self.own_current:
                self.current.release()
            self.current = completed_request
            self.own_current = (completed_request.config['buffer_count'] > 1)
            if self.own_current:
                self.current.acquire()

    def render_drm(self, picam2, completed_request):
        if completed_request is not None:
            self.display_stream_name = completed_request.config['display']
            stream = completed_request.stream_map[self.display_stream_name]
        else:
            if self.display_stream_name is None:
                self.display_stream_name = picam2.display_stream_name
            stream = picam2.stream_map[self.display_stream_name]

        cfg = stream.configuration
        pixel_format = str(cfg.pixel_format)
        width, height = (cfg.size.width, cfg.size.height)

        for conn in self.conn:
            if not self.conn[conn].ready:
                self.conn[conn].start(width, height, pixel_format)

        ctx = pykms.AtomicReq(self.card)
        if completed_request is not None:
            fb = completed_request.request.buffers[stream]
            fd = fb.planes[0].fd
            stride = cfg.stride
            if pixel_format == "XBGR8888":
                drmfb = pykms.DmabufFramebuffer(self.card, width, height, pykms.PixelFormat.XBGR8888, [fd], [stride],
                                                [0])
            elif pixel_format == "YUV420":
                yh = height // 2
                cs = stride // 2
                size = height * stride
                drmfb = pykms.DmabufFramebuffer(self.card, width, height, pykms.PixelFormat.YUV420, [fd, fd, fd],
                                                [stride, cs, cs], [0, size, size + yh * cs])

            self.drmfbs[fb] = drmfb

            drmfb = self.drmfbs[fb]

            for cname in self.conn:
                conn = self.conn[cname]
                ctx.add_plane(conn._plane, drmfb, conn._crtc, (0, 0, width, height), (0, 0, conn.width, conn.height))

        for cname in self.conn:
            conn = self.conn[cname]
            for i in range(conn.num_overlays):
                if conn.overlay_dirty[i]:
                    width, height = conn.overlay_fb[i].width, conn.overlay_fb[i].height
                    ctx.add_plane(conn.overlay[i], conn.overlay_fb[i], conn._crtc,
                                  (0, 0, width, height), conn.overlay_pos[i])

        ctx.commit_sync()
        ctx = None

    def set_overlay(self, overlay, output=None, num=0):
        if output is None:
            output = 'DSI-1'
        conn = self.conn[output]

        if isinstance(overlay, Image.Image):
            w, h = overlay.size
            channels = 4
        else:
            h, w, channels = overlay.shape

        init = False
        if num not in conn.overlay_fb or conn.overlay_fb[num] is None:
            init = True
        elif conn.overlay_fb[num].width != w or conn.overlay_fb[num].height != h:
            init = True

        if init:
            conn.overlay_fb[num] = pykms.DumbFramebuffer(self.card, w, h, "AB24")

        with mmap.mmap(conn.overlay_fb[num].fd(0), w * h * 4, mmap.MAP_SHARED, mmap.PROT_WRITE) as mm:
            if isinstance(overlay, Image.Image):
                mm.write(overlay.tobytes())
            else:
                mm.write(np.ascontiguousarray(overlay).data)

        conn.overlay_dirty[num] = True
