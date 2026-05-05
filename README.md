# ConfCam: A Pi based conference streaming camera

This is the codebase for a broadcast/studio style camera build on top of the Raspberry Pi 4 and various MIPI sensors.

It's build as a Python application that configures libcamera and libdrm to play nicely with eachother and have a low
latency camera feed going from the sensor to HDMI while showing a configuration interface on a secondary display.

## Installation

Use the `install.sh` script to install c2 on a minimal raspbian trixie installation.

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

Currently, the application pushes the frames directly into the hardware video encoder and the result is streamed to
mediamtx running on the pi to allow clients to connect and view the stream. Using the webrtc viewer
at http://0.0.0.0:8889/cam has the lowest latency, but it also is accessible at :8890 for SRT, :8888/cam for HLS and
:1935 for rtmp

## API

The camera application exposes a unix socket for control at /tmp/sensor-control for realtime control. There's a golang
based HTTP api server that works with this that I should publish Soon(tm)

## Bill of materials

For the first prototype:

* [Raspberry Pi 4 model B](https://www.raspberrypi.com/products/raspberry-pi-4-model-b/)
* [Raspberry Pi HQ camera](https://www.raspberrypi.com/products/raspberry-pi-high-quality-camera/)
* [Raspberry Pi Touch Display 2 5"](https://www.raspberrypi.com/products/touch-display-2/)
  * This is an portrait-orientation display which doesn't work that well, better solution is the old display which is landscape-native or a custom waveshare one
  * [Raspberry Pi Touch Display 7"](https://www.raspberrypi.com/products/raspberry-pi-touch-display/)
  * [Waveshare 5inch 1024x600 DSI touch display](https://www.waveshare.com/5inch-dsi-lcd-c.htm)
* [8-50mm C-mount lens](https://www.waveshare.com/product/raspberry-pi/cameras/10mp-pixels/8-50mm-zoom-lens-for-pi.htm)
* [MicroSD card](https://www.raspberrypi.com/products/sd-cards/)
* Some pieces of wood to keep everything together and some micro-hdmi cables to hook up video outputs