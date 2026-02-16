# Raspberry Pi studio camera

This is the codebase for a broadcast/studio style camera build on top of the Raspberry Pi 4 and the HQ sensor.

It's build as a Python application that configures libcamera and libdrm to play nicely with eachother and have a low
latency camera feed going from the sensor to HDMI while showing an configuration interface on a secondary display.

## Limitations

* Max output is 1080p30 when the hardware H.264 encoder is used (and it cannot be disabled at the moment)
* Higher resolutions are limited by the HQ sensor

## Installation

The easiest way to install it is by installing Raspian Trixie to an SD card, make sure no graphical user interface
is starting by either uninstalling it or disabling all related systemd services. Then put the picam application
in place:

```shell-session
$ apt install python3-opencv python3-evdev python3-picamera2 python3-pillow
$ cd /opt
$ git clone https://github.com/martijnbraam/picam
$ cp /opt/picam/systemd/camera.service /etc/systemd/system/camera.service
$ systemctl start camera
```

## Configuration

The application reads a .ini config file from /boot/camera.ini to do a full headless initial setup. This config file
will be created on the first launch. If on first boot a DSI display is connected it will configure itself to use that
as monitoring output, otherwise HDMI 2 will be used.

```ini
[output]
output = HDMI-A-1
mode = 1920x1080

[monitor]
output = DSI-1
mode = 1280x720
touchscreen-rotate = 0
touchscreen-flip-x = False
touchscreen-flip-y = False
touchscreen-res = 1280x720
exposure-helper-min = 61
exposure-helper-max = 70

[encoder]
bitrate = 10M
```

## Streaming

Currently the application pushes the frames directly into the hardware video encoder and the result is streamed to
mediamtx running on the pi to allow clients to connect and view the stream. Using the webrtc viewer
at http://0.0.0.0:8889/cam has the lowest latency but it also is accessible at :8890 for SRT, :8888/cam for HLS and
:1935 for rtmp

## API

The camera application exposes an unix socket for control at /tmp/sensor-control for realtime control. There's a golang
based HTTP api server that works with this that I should publish Soon(tm)