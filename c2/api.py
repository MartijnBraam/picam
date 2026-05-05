import os
import socket
import struct


class ControlAPI:
    def __init__(self, cam, path=None):
        self.path = path
        self.cam = cam
        if path is None:
            self.path = "/tmp/sensor-control"

        try:
            os.unlink(self.path)
        except OSError:
            pass

        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
        self.sock.bind(self.path)
        self.sock.setblocking(False)
        self.sock.listen(1)

        self.clients = []

        self.state = {}
        self.last_state = {}

        # Default state
        self.auto_exposure = True
        self.auto_whitebalance = True

        # Runtime state for one-push
        self.op_whitebalance = False

    def broadcast(self, fn):
        for c in self.clients:
            fn(c)

    def do_work(self):
        if self.op_whitebalance:
            self.op_whitebalance = False
            self.cam.set_controls(AwbEnable=False)
        try:
            client, addr = self.sock.accept()
            self.clients.append(client)
        except BlockingIOError:
            pass

        if self.cam.ui.ec.once(self):
            self.broadcast(self.send_controls)
        if self.cam.ui.ae.once(self):
            self.broadcast(self.send_controls)

        for c in self.clients:
            try:
                c.setblocking(False)
                packet = c.recv(1920 * 1080 * 4 * 2)
                if len(packet) == 0:
                    continue

                if packet[0] == 0x01:
                    # Request full state
                    self.send_all_state(c)
                elif packet[0] == 0x02:
                    # Configure auto exposure
                    pkt = struct.unpack("<B?", packet)
                    self.cam.set_controls(AeEnable=pkt[1])
                    self.auto_exposure = pkt[1]
                elif packet[0] == 0x03:
                    # Configure auto whitebalance
                    pkt = struct.unpack("<B?", packet)
                    self.cam.set_controls(AwbEnable=pkt[1])
                    self.auto_whitebalance = pkt[1]
                elif packet[0] == 0x04:
                    # One-push white balance
                    self.cam.set_controls(AwbEnable=True)
                    self.auto_whitebalance = False
                    self.op_whitebalance = True
                elif packet[0] == 0x05:
                    # Tally
                    pkt = struct.unpack("<BB", packet)
                    self.cam.set_tally(pkt[1])
                elif packet[0] == 0x06:
                    # Gain
                    pkt = struct.unpack("<BB", packet)
                    self.cam.set_gain(pkt[1])
                elif packet[0] == 0x07:
                    # Shutter
                    pkt = struct.unpack("<BH", packet)
                    self.cam.set_shutter(pkt[1])
                elif packet[0] == 0x08:
                    # Change framerate
                    pkt = struct.unpack("<BB", packet)
                    self.cam.set_fps(pkt[1])
                elif packet[0] == 0x09:
                    # Change auto exposure compensation
                    pkt = struct.unpack("<Bf", packet)
                    self.cam.set_ev(pkt[1])
                elif packet[0] == 0x0A:
                    # Show/hide the overlays on the HDMI output
                    pkt = struct.unpack("<B?", packet)
                    self.cam.enable_hdmi_overlay(pkt[1])

            except BlockingIOError:
                pass
            except Exception as e:
                print("Recv err", e)

        if len(self.last_state):
            if self.state["AnalogueGain"] != self.last_state["AnalogueGain"]:
                for c in self.clients:
                    try:
                        self.send_sensor_state(c)
                    except BrokenPipeError:
                        pass

        self.last_state = self.state

    def send_all_state(self, client):
        self.send_sensor_state(client)
        self.send_controls(client)

    def send_sensor_state(self, client):
        blob = struct.pack(b'<BffII', 0x01, self.state["AnalogueGain"], self.state["DigitalGain"],
                           self.state["ExposureTime"], self.state["ColourTemperature"])
        self.send(client, blob)

    def send_controls(self, client):
        ui = self.cam.ui
        blob = struct.pack(b'<B??fB', 0x02, ui.ae.value, self.auto_whitebalance, ui.ec.value, ui.tally.value)
        self.send(client, blob)

    def send(self, client, data):
        try:
            client.send(data)
        except BrokenPipeError:
            self.clients.remove(client)

    def update_state(self, state):
        self.state = state
