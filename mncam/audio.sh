#!/bin/sh

srcdev=$(arecord -l  |grep -E 'hifiberry' |cut -d: -f1 |cut -d' ' -f 2)

ffmpeg -nostats -nostdin -f alsa -i hw:$srcdev \
       -af astats=metadata=1:reset=1,ametadata=print:key=lavfi.astats.1.RMS_level,ametadata=print:key=lavfi.astats.2.RMS_level \
       -f alsa hdmi:CARD=vc4hdmi0,DEV=0 2>&1 | grep RMS
