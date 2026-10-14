#!/usr/bin/env bash
#
# Build the EvoBridge appliance image with pi-gen (in Docker).
#
# An EvoBridge is a Raspberry Pi that connects one EvoFlow reactor (by USB) to
# the EvoHub: it joins the hub's evo-net Wi-Fi, forwards the reactor's state to
# the hub's MQTT broker and passes commands back to the reactor. The bridge code
# (pico-bridge/) lives in the evoflow-reactor repository and is fetched at
# REACTOR_REF.
#
# Requirements on the BUILD host: Docker able to run linux/arm64 containers,
# ~10 GB free disk and ~20-40 min.
#
# Usage:
#   ./build-bridge-image.sh                         # evoflow-reactor master
#   REACTOR_REF=<branch, tag or commit> ./build-bridge-image.sh
# Output:
#   r-pi/image/.pi-gen-evobridge/deploy/*-evobridge.img.xz
#
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_DIR="$HERE/image"
# A pi-gen checkout separate from the hub's, so the two builds never share state.
PIGEN_DIR="${PIGEN_DIR:-$IMAGE_DIR/.pi-gen-evobridge}"
PIGEN_BRANCH="${PIGEN_BRANCH:-arm64}"   # 64-bit: native on Apple Silicon + no 32-bit setarch path
REACTOR_REPO="https://github.com/Schwank-Lab/evoflow-reactor.git"
REACTOR_REF="${REACTOR_REF:-master}"
REACTOR_DIR="$IMAGE_DIR/.reactor"

echo "==> pi-gen checkout: $PIGEN_DIR ($PIGEN_BRANCH)"
if [ ! -d "$PIGEN_DIR/.git" ]; then
  git clone --depth=1 --branch "$PIGEN_BRANCH" https://github.com/RPi-Distro/pi-gen "$PIGEN_DIR"
fi

echo "==> fetching pico-bridge from evoflow-reactor ($REACTOR_REF)"
if [ ! -d "$REACTOR_DIR/.git" ]; then
  git clone --quiet "$REACTOR_REPO" "$REACTOR_DIR"
fi
git -C "$REACTOR_DIR" fetch --quiet origin "$REACTOR_REF"
git -C "$REACTOR_DIR" checkout --quiet --detach FETCH_HEAD
REACTOR_COMMIT="$(git -C "$REACTOR_DIR" rev-parse HEAD)"
echo "    evoflow-reactor $REACTOR_COMMIT"

echo "==> staging pico-bridge into the appliance stage"
STAGE_FILES="$IMAGE_DIR/stage-evobridge/00-evobridge/files"
rm -rf "$STAGE_FILES"; mkdir -p "$STAGE_FILES"
rsync -a --exclude='__pycache__' --exclude='logs' "$REACTOR_DIR/pico-bridge" "$STAGE_FILES/"
# Records which bridge code is on the card, for anyone looking on the Pi.
echo "$REACTOR_COMMIT" > "$STAGE_FILES/pico-bridge/REACTOR_COMMIT"

echo "==> installing config + custom stage into pi-gen"
cp "$IMAGE_DIR/config-evobridge" "$PIGEN_DIR/config"
rm -rf "$PIGEN_DIR/stage-evobridge"
cp -r "$IMAGE_DIR/stage-evobridge" "$PIGEN_DIR/stage-evobridge"
# Only the EvoBridge image is exported, not the intermediate Lite image.
touch "$PIGEN_DIR/stage2/SKIP_IMAGES"

echo "==> building (this is the long part)"
cd "$PIGEN_DIR"
docker rm -v pigen_work_evobridge >/dev/null 2>&1 || true   # clear any stale container from a prior run
CONTAINER_NAME=pigen_work_evobridge CONTINUE=0 ./build-docker.sh

# pi-gen only runs executable stage scripts and merely logs the ones it skips,
# which would leave the image silently incomplete.
if grep "(not executable)" "$PIGEN_DIR/deploy/build.log"; then
  echo "==> ERROR: pi-gen skipped the stage scripts above; make them executable." >&2
  exit 1
fi

echo
echo "==> done. Flashable image:"
ls -1 "$PIGEN_DIR/deploy/"*.img.xz
echo "Flash with Raspberry Pi Imager, or see r-pi/README.md for dd."
