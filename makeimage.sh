#!/bin/sh
set -e

export ALPINE_VERSION=3.23
export APPDIR=$(dirname "$0")
export WORKDIR=$APPDIR/workdir
export CACHEDIR=$WORKDIR/cache/apk

mkdir -p "$WORKDIR"
mkdir -p "$CACHEDIR"

docker run --rm \
  -v $APPDIR:/app \
  -v $WORKDIR:/workdir \
  -v $CACHEDIR:/etc/apk/cache \
  -e ALPINE_VERSION \
  -e BUILD_ARCH \
  -w /app \
  --tty -i \
  alpine:$ALPINE_VERSION \
  "sh" -c 'apk add bash; /app/alpine/build.sh'