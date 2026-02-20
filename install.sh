#!/bin/bash

MEDIAMTX_RELEASE=1.16.1

NORMAL="\033[1;0m"
STRONG="\033[1;1m"
RED="\033[1;31m"
GREEN="\033[1;32m"
YELLOW="\033[1;33m"
BLUE="\033[1;34m"

APTOPT=
SYSTEMDOPT=--now

msg() {
	local prompt="$GREEN>>>${NORMAL}"
	printf "${prompt} %s\n" "$1" >&2
}

error() {
	local prompt="${RED}>>> ERROR:${NORMAL}"
	printf "${prompt} %s\n" "$1" >&2
}

debian() {
  run_apt=false
  for pkg in "$@"; do
    if dpkg -s "${pkg}" &>/dev/null; then
      echo "${pkg} is installed"
    else
      error "Missing ${pkg}"
      run_apt=true
    fi
  done

  if [ "$run_apt" = true ] ; then
    apt $APTOPT install "$@"
  fi
}

if [ ! -f "/etc/debian_version" ]; then
   error "This script requires running on a debian system"
   exit 1
fi

if [ "$1" == "image" ]; then
  msg "Running inside the image creation tool"
  APTOPT=-qy
  SYSTEMDOPT=
fi

msg "Installing dependencies available in Debian Trixie"
debian python3-opencv python3-evdev python3-picamera2 python3-pil python3-humanfriendly fonts-liberation haproxy golang wget

msg "Build the API server..."
make all

msg "Installing MediaMTX..."
if [ ! -x /usr/local/bin/mediamtx ]; then
  wget "https://github.com/bluenviron/mediamtx/releases/download/v${MEDIAMTX_RELEASE}/mediamtx_v${MEDIAMTX_RELEASE}_linux_arm64.tar.gz" -O mediamtx.tar.gz
  mkdir mediamtx
  tar -xvf mediamtx.tar.gz -C mediamtx
  mv mediamtx/mediamtx /usr/local/bin/mediamtx
  rm -rf mediamtx mediamtx.tar.gz
else
  echo "Already installed, skipping..."
fi

msg "Putting config files in place..."
install -m644 system/camera.service /etc/systemd/system/camera.service
sed -i '/^WorkingDirectory=/c\WorkingDirectory='$PWD /etc/systemd/system/camera.service
install -m644 system/camera-api.service /etc/systemd/system/camera-api.service
sed -i '/^ExecStart=/c\ExecStart='$PWD/mncam_api /etc/systemd/system/camera-api.service
install -m644 system/haproxy.cfg /etc/haproxy/haproxy.cfg
mkdir -p /etc/mediamtx
install -m644 system/mediamtx.yml /etc/mediamtx/mediamtx.yml
install -m644 system/mediamtx.service /etc/systemd/system/mediamtx.service

msg "Enabling the camera services..."
systemctl enable $SYSTEMDOPT camera
systemctl enable $SYSTEMDOPT camera-api

ip=$(ip -o route get to 1.2.3.4 | sed -n 's/.*src \([0-9.]\+\).*/\1/p')
echo "Installation complete"
echo "The webinterface should now be available at http://${ip}/"