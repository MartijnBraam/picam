import struct
import subprocess

import alsaaudio

from mncam.config import Config


class AudioManager:
    def __init__(self, config: Config):
        self._config = config
        self.audio_enabled = False

        cards = alsaaudio.cards()
        if config.audio.input_device not in cards:
            print(f"Audio device {config.audio.input_device} not found.")
            return
        input_idx = cards.index(config.audio.input_device)
        output_idx = cards.index(config.audio.output_device)

        self._pga = alsaaudio.Mixer(cardindex=input_idx, control='ADC')
        self._left_mux = alsaaudio.Mixer(cardindex=input_idx, control='ADC Left Input')
        self._right_mux = alsaaudio.Mixer(cardindex=input_idx, control='ADC Right Input')
        self.audio_enabled = True

        self.set_gain('L', config.audio.left_gain)
        self.set_gain('R', config.audio.right_gain)
        self.set_route('L', config.audio.left_source)
        self.set_route('R', config.audio.right_source)

    def set_gain(self, channel, gain):
        if not self.audio_enabled:
            return
        if channel == 'L':
            self._pga.setvolume(volume=int(gain * 100), channel=0, units=alsaaudio.VOLUME_UNITS_DB)
            self._config.audio.left_gain = int(gain)
        else:
            self._pga.setvolume(volume=int(gain * 100), channel=1, units=alsaaudio.VOLUME_UNITS_DB)
            self._config.audio.right_gain = int(gain)
        self._config.save_config()

    def get_min_gain(self):
        return -12

    def get_max_gain(self):
        return 40

    def get_routes(self, channel):
        if not hasattr(self, '_left_mux'):
            return []
        mux = self._left_mux
        if channel == 'R':
            mux = self._right_mux
        current, options = mux.getenum()
        return options

    def set_route(self, channel, source):
        mux = self._left_mux
        if channel == 'R':
            mux = self._right_mux
        current, options = mux.getenum()
        if source not in options:
            print("Invalid mux source: " + source)
            return
        item = options.index(source)
        mux.setenum(item)

    def start_loop(self, q):
        cmd = ["alsaloop-fosdem", "-C", f"hw:CARD={self._config.audio.input_device},DEV=0", "-P",
               f"hdmi:CARD={self._config.audio.output_device},DEV=0"]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                             stderr=subprocess.DEVNULL)
        print("Launching", ' '.join(cmd))
        dec = struct.Struct('dd')
        while True:
            frame = p.stdout.read(16)
            if frame == b'':
                print("Alsaloop crashed")
                return
            level = dec.unpack(frame)
            q.put(level)
