#!/bin/bash

REL="2025-12-04"
BASE="https://downloads.raspberrypi.com/raspios_lite_arm64/images/raspios_lite_arm64-${REL}/${REL}-raspios-trixie-arm64-lite.img.xz"
WORK="workdir"
CACHE=$WORK/cache

NORMAL="\033[1;0m"
STRONG="\033[1;1m"
RED="\033[1;31m"
GREEN="\033[1;32m"
YELLOW="\033[1;33m"
BLUE="\033[1;34m"

LO=""
KPARTX=""

msg() {
	local prompt="$GREEN>>>${NORMAL}"
	printf "${prompt} %s\n" "$1" >&2
}

error() {
	local prompt="${RED}>>> ERROR:${NORMAL}"
	printf "${prompt} %s\n" "$1" >&2
}

function cleanup {
  if [ "$KPARTX" != "" ]; then
    msg "Unmounting filesystems"
    mapfile -t PART < <(grep -o 'loop.p.' <<<"${KPARTX}")
    PART_BOOT=${PART[0]}
    PART_ROOT=${PART[1]}
    sudo umount /dev/mapper/$PART_BOOT
    sudo umount "$WORK"/rootfs/dev
    sudo umount "$WORK"/rootfs/proc
    sudo umount "$WORK"/rootfs/sys
    sudo umount /dev/mapper/$PART_ROOT
    sudo kpartx -v -d $LO
  fi
  if [ "$LO" != "" ]; then
    msg "Tearing down loop mount"
    sudo losetup -d $LO
  fi
}

function trap_exit {
  error "Error occurred"
  cleanup
}

if [ ! -d "$WORK" ] ; then
  msg "Creating working directory ${WORK}"
  mkdir -p "$WORK"
fi

mkdir -p "$CACHE"

if [ ! -f "$CACHE/base-${REL}.img.xz" ] ; then
  msg "Downloading RaspiOS Trixie ${REL}"
  wget -q --show-progress "$BASE" -O "$CACHE"/base-${REL}.img.xz
fi

msg "Extracting image"
unxz -k -- "$CACHE"/base-${REL}.img.xz
mv "$CACHE"/base-${REL}.img "$WORK"/disk.img

msg "Growing image"
truncate  --no-create --size=+2G "$WORK"/disk.img
parted -s "$WORK"/disk.img resizepart 2 100%

msg "Mounting disk image"
LO=$(losetup -f)
echo "Using $LO"
sudo losetup $LO "$WORK"/disk.img
trap trap_exit EXIT
KPARTX=$(sudo kpartx -a -v -s $LO)
mapfile -t PART < <(grep -o 'loop.p.' <<<"${KPARTX}")
mkdir -p "$WORK"/rootfs
PART_BOOT=${PART[0]}
PART_ROOT=${PART[1]}

msg "Resizing root file system"
sudo resize2fs /dev/mapper/$PART_ROOT

msg "Mounting partitions"
sudo mount /dev/mapper/$PART_ROOT "$WORK"/rootfs
sudo mount /dev/mapper/$PART_BOOT "$WORK"/rootfs/boot
sudo mount -o bind /dev "$WORK"/rootfs/dev
sudo mount -t proc none "$WORK"/rootfs/proc
sudo mount -o bind /sys "$WORK"/rootfs/sys

TVER=$(cat "$WORK"/rootfs/etc/debian_version)
msg "Detected Debian ${TVER}"

if [ ! -f /proc/sys/fs/binfmt_misc/qemu-aarch64 ] ; then
  msg "Registering qemu-aarch64 in binfmt_misc"
  MAGIC='\x7f\x45\x4c\x46\x02\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\xb7\x00'
  MASK='\xff\xff\xff\xff\xff\xff\xff\x00\xff\xff\xff\xff\xff\xff\xff\xff\xfe\xff\xff\xff'
  reg=":qemu-aarch64:M::$MAGIC:$MASK:/usr/bin/qemu-aarch64-static:C"
  sud sh -c "echo '$reg' > /proc/sys/fs/binfmt_misc/register"
fi

msg "Setting raspberry pi config options in /boot"
sudo cp system/config.txt "$WORK"/rootfs/boot/config.txt

msg "Disabling userconfig service"
sudo chroot "$WORK"/rootfs systemctl disable userconfig
sudo chroot "$WORK"/rootfs systemctl mask userconfig

msg "Setting root password to 'camera' and enable for ssh"
sudo chroot "$WORK"/rootfs sh -c 'echo "root:camera" | /usr/sbin/chpasswd'
sudo chroot "$WORK"/rootfs sh -c 'echo "PermitRootLogin yes" >> /etc/ssh/sshd_config'

msg "Refreshing repositories"
sudo chroot "$WORK"/rootfs /usr/bin/apt-get update

msg "Configuring apt"
sudo chroot "$WORK"/rootfs sh -c "echo 'APT::Install-Recommends \"false\";' >> /etc/apt/apt.cfg"
sudo chroot "$WORK"/rootfs sh -c "echo 'APT::Install-Suggests \"false\";' >> /etc/apt/apt.cfg"
sudo chroot "$WORK"/rootfs sh -c "echo 'Acquire::GzipIndexes \"true\";' >> /etc/apt/apt.cfg"
sudo chroot "$WORK"/rootfs sh -c "echo 'Acquire::CompressionTypes::Order:: \"gz\";' >> /etc/apt/apt.cfg"
sudo mkdir -p "$WORK"/rootfs/etc/dpkg/dpkg.conf.d
sudo cp system/nodoc "$WORK"/rootfs/etc/dpkg/dpkg.conf.d/01_nodoc

msg "Installing base packages"
sudo chroot "$WORK"/rootfs /usr/bin/apt-get -q -y install make git

msg "Cleaning unneeded files in the image"
sudo rm -rf "$WORK"/var/cache/apt/archives/
sudo rm -rf "$WORK"/usr/share/doc/

msg "Cloning repository"
sudo chroot "$WORK"/rootfs git clone https://github.com/MartijnBraam/picam /opt/mncam

msg "Running installer script"
sudo cp install.sh "$WORK"/rootfs/opt/mncam/install.sh
sudo chroot "$WORK"/rootfs sh -c "cd /opt/mncam && ./install.sh image"

msg "Enabling SSH"
sudo chroot "$WORK"/rootfs systemctl enable ssh

trap - EXIT
cleanup

msg "Re-compressing image"
xz -v --stdout "$WORK"/disk.img > mncam-pi4-$(date +"%Y-%m-%d").img.xz
