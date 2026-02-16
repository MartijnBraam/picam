#!/bin/bash
set -e
trap "echo script failed; bash -i" ERR
ALPINE_VERSION=${ALPINE_VERSION}
APP_DIR=/app
WORKDIR=/workdir

# Install dependencies
apk update
apk add alpine-sdk alpine-conf squashfs-tools doas mkinitfs

# Clone the aports repository
if [ ! -d $WORKDIR/aports/.git ]; then
    if [ -d $WORKDIR/aports/ ]; then
        rm -rf $WORKDIR/aports/
    fi
    git clone -b $ALPINE_VERSION-stable --depth=1 https://gitlab.alpinelinux.org/alpine/aports.git /$WORKDIR/aports
else
    cd $WORKDIR/aports
    git checkout $ALPINE_VERSION-stable
    git reset --hard
    git clean -f
    git pull
    cd $APP_DIR
fi

echo "Creating unprivileged user..."
adduser build -G abuild -D
echo "permit nopass keepenv :root" > /etc/doas.d/build.conf

echo "Generate signing keys..."
if [ ! -f $APP_DIR/keys/build.rsa ]; then
    mkdir -p $APP_DIR/keys
    doas -u build abuild-keygen -a -n
    mv /home/build/.abuild/*.rsa.pub $APP_DIR/keys/build.rsa.pub
    mv /home/build/.abuild/*.rsa $APP_DIR/keys/build.rsa
fi
cp $APP_DIR/keys/build.rsa.pub /etc/apk/keys/
mkdir -p /home/build/.abuild
echo "PACKAGER_PRIVKEY=\"$APP_DIR/keys/build.rsa\"" >> /home/build/.abuild/abuild.conf

echo "Creating local overrides..."
cp -fvr $APP_DIR/alpine/aports/* $WORKDIR/aports/

echo "Running mkimage..."
rm -rf $WORKDIR/output
cd $WORKDIR
doas -u build sh $WORKDIR/aports/scripts/mkimage.sh \
    --tag $ALPINE_VERSION-picamera \
    --outdir $WORKDIR/output \
    --profile picamera \
    --arch aarch64 \
    --hostkeys \
    --repository http://dl-cdn.alpinelinux.org/alpine/v$ALPINE_VERSION/main \
    --repository /home/build/packages/testing