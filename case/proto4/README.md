# Prototype 4 design files

These are the 3d printed parts for the Proto4 case. This has both a "DSLR" formfactor and box camera design with a
shared mounting system for the sensors.

## DSLR formfactor case

```shell-session
$ make case mounts
```

* Print `case_front.stl` and `case_rear.stl` for the outer case.
* Print one of the sensor mounts and one of the lens mounts from the `mounts` subfolder and screw them together.

#### BOM

* [Raspberry Pi 4 model B](https://www.raspberrypi.com/products/raspberry-pi-4-model-b/)
* [Waveshare 5" raspberry pi panel](https://www.waveshare.com/5inch-dsi-lcd-c.htm)
* 4x metal insert M2.5x4Lx4
* 1x metal insert 1/4-20 UNC for the tripod
* The parts for the lens mounts below
* 8x M2.5 screw (4 are included with the waveshare panel)
* 30cm USB-A to USB-C cable to power the pi from the neutrik USB feedthrough
* 30cm micro-hdmi to HDMI for the neutrik HDMI plug

## Box formfactor case

```shell-session
$ make box mounts panels
```

* Print `box_bottom.stl` and `box_top.stl` for the frame of the camera
* Print one of the sensor mounts and one of the lens mounts from the `mounts` subfolder and screw them together.
* Print the panels to complete all the sides of the camera:
    * `blank.stl` and `blank_short` are empty panels to enclose unused sides.
    * `sensor.stl` is needed to mount the sensor/lens mount assembly into the case
    * `waveshare_5inch.stl` is the mount for the 5" display in one of the sides
    * `rear_io.stl` contains the neutrik d-mount holes for connecting to the outside world
    * `cheese.stl` is a blank plate with holes for various screw sizes to mount attachments

#### BOM

* [Raspberry Pi 4 model B](https://www.raspberrypi.com/products/raspberry-pi-4-model-b/)
* [Waveshare 5" raspberry pi panel](https://www.waveshare.com/5inch-dsi-lcd-c.htm)
* 24x metal insert M2.5x4Lx4
* 3x metal insert 1/4-20 UNC for the tripod
* The parts for the lens mounts below
* Each panel requires 4 M2.5 screws
* For the sensor panel:
    * 4x metal insert M2.5x4Lx4
* For the cheese panel:
    * 3x metal insert 1/4-20 UNC for the tripod
    * 6x metal insert M3x4Lx4.2
* For the I/O panel:
    * The neutrik d-mount inserts for the I/O you need. In the reference this contains:
        * 1x HDMI
        * 2x XLR
        * 1x USB-B feed through
    * Screws and bolts for the neutriks inserts

## Sensor and lens mounts

#### MFT

This mounts Micro Four Thirds lenses using parts of an MFT extension tube.

BOM:

* Generic MFT extension tube (aliexpress.com/item/1005001670741696.html) for the mounting ring, spring rention ring, screws and locking mechanism.
* 4x metal insert M2.5x4Lx4

#### C-mount

This mounts cheap security camera lenses.

BOM:

* 4x metal insert M2.5x4Lx4
* As lens you can use the [Waveshare 8-50mm](https://www.waveshare.com/8-50mm-zoom-lens-for-pi.htm)

#### IMX290 sensor mount

This mounts the IMX290 and IMX462 sensors with the generic IR-cut lens mount available at waveshare.

BOM:
* 4x M2.5 5mm spacer tube (included with the waveshare display)
* 4x M2.5 screw
* The sensor
  * [IMX290 sensor board](https://www.waveshare.com/imx290-83-ir-cut-camera.htm)
  * [IMX462 sensor board](https://www.waveshare.com/imx462-ir-cut-camera-a.htm)