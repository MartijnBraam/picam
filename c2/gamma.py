import ctypes
import glob
import math
from fcntl import ioctl

from c2.ioctl import VIDIOC_QUERYCAP, v4l2_capability, v4l2_ext_controls, v4l2_ext_control, V4L2_CTRL_CLASS_USER, \
    V4L2_CID_USER_BASE, VIDIOC_G_EXT_CTRLS, bcm2835_isp_gamma, VIDIOC_S_EXT_CTRLS

basecurve = [
    (0.000000, 0.000000),
    (0.018124, 0.026126),
    (0.143357, 0.370145),
    (0.330116, 0.730507),
    (0.457952, 0.853462),
    (0.734950, 0.965061),
    (0.904758, 0.985699),
    (1.000000, 1.000000),
]


def basecurve_arric4(points):
    c = 95 / 1023
    b = (1023 - 95) / 1023
    ah = ((2 ** 18) - 16) * (3200 / 800)

    result = []
    for i in range(points):
        Esensor = i / (points - 1)
        E = min((math.log2(ah * Esensor + 64) - 6) / 14 * b + c, 1)
        result.append((Esensor, E))
    return result


def sample_curve(curve, pos):
    lower = [0, 0]
    upper = [0, 0]
    for x, y in curve:
        if x < pos:
            lower = [x, y]
        if x > pos and upper[0] == 0:
            upper = [x, y]
            break
    offset = (pos - lower[0]) / (upper[0] - lower[0])
    return lower[1] * (1 - offset) + (upper[1] * (offset))


def generate_curve(lift, gamma, gain, offset):
    points = 33
    curve = []
    for i in range(0, points):
        x = i / (points - 1)

        result = sample_curve(basecurve, x) ** (1 / (gamma + 1.5))

        result += lift * (2 - (x * 2))
        result *= gain
        result += offset
        curve.append(max(min(result, 1), 0))
    return curve


def set_isp_gamma(fd, curve):
    ctrls = v4l2_ext_controls()
    ctrl = v4l2_ext_control()

    ctrls.ctrl_class = V4L2_CTRL_CLASS_USER
    ctrls.count = 1
    ctrls.controls = ctypes.pointer(ctrl)

    ctrl.id = V4L2_CID_USER_BASE + 0x10e0 + 5
    ctrl.size = 136
    ctrl.ptr = ctypes.cast(ctypes.create_string_buffer(ctrl.size), ctypes.c_void_p)

    try:
        ioctl(fd, VIDIOC_G_EXT_CTRLS, ctrls)
    except OSError as e:
        pass
    gamma = bcm2835_isp_gamma()
    gamma.enabled = 1
    x = [42] * 33
    y = [0] * 33
    for i in range(0, 33):
        gamma.x[i] = int(i / 32 * 65535)
        x[i] = gamma.x[i]
        gamma.y[i] = int(curve[i] * 65535)
        y[i] = gamma.y[i]

    ctrl.gamma = ctypes.pointer(gamma)

    ioctl(fd, VIDIOC_S_EXT_CTRLS, ctrls)


def open_isp():
    for file in sorted(glob.glob("/dev/video*")):
        fd = open(file, "rb")
        qc = v4l2_capability()
        ioctl(fd, VIDIOC_QUERYCAP, qc)

        if qc.card == b'bcm2835-isp' and qc.driver == b'bcm2835-isp':
            if qc.capabilities & 2:
                return fd

        fd.close()


if __name__ == '__main__':
    fd = open_isp()
    curve = generate_curve(0, 0, 1, 0)
    set_isp_gamma(fd, curve)
