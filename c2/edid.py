import glob
import struct


class EdidInfo:
    def __init__(self):
        self.vendor = None
        self.cec = None
        self.camera_id = None


def edid_strcode(raw):
    val, = struct.unpack('>H', raw)
    c3 = val & 0b00011111
    val = val >> 5
    c2 = val & 0b00001111
    val = val >> 5
    c1 = val & 0b00001111
    name = chr(c1 + ord('A') - 1) + chr(c2 + ord('A') - 1) + chr(c3 + ord('A') - 1)
    return name


def check_edid():
    files = glob.glob("/sys/class/drm/card*-HDMI-A-1/edid")
    if len(files) == 0:
        return

    with open(files[0], 'rb') as handle:
        edid = handle.read()

    if len(edid) == 0:
        return EdidInfo()

    vendor = edid_strcode(edid[0x08:0x0A])

    result = EdidInfo()
    result.vendor = vendor
    num_exts = edid[0x7e]
    if num_exts == 1:
        ext = edid[0x80:]
        if vendor == 'HHA':
            cec_addr = edid[0x9a]
            output = cec_addr >> 4
            result.cec = cec_addr
            result.camera_id = output

    return result


if __name__ == '__main__':
    check_edid()
