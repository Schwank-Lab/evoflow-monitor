#!/usr/bin/env bash
#
# Build the EvoHub appliance image with pi-gen (in Docker).
#
# Produces a flashable Raspberry Pi OS Lite (arm64) image that boots straight
# into the EvoHub stack: Postgres + Mosquitto + Grafana + listener + UI under
# docker compose, with the hub acting as its own Wi-Fi access point.
#
# Requirements on the BUILD host (your laptop or CI):
#   - Docker (pi-gen runs its whole build inside a container via build-docker.sh)
#   - ~10 GB free disk and ~20-40 min
#   - The container images published to GHCR first (see r-pi/README.md)
#
# Usage:
#   ./build-image.sh
# Output:
#   r-pi/image/.pi-gen/deploy/*.img.gz
#
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_DIR="$HERE/image"
PIGEN_DIR="${PIGEN_DIR:-$IMAGE_DIR/.pi-gen}"
PIGEN_BRANCH="${PIGEN_BRANCH:-arm64}"   # 64-bit: native on Apple Silicon + no 32-bit setarch path

echo "==> pi-gen checkout: $PIGEN_DIR ($PIGEN_BRANCH)"
if [ ! -d "$PIGEN_DIR/.git" ]; then
  git clone --depth=1 --branch "$PIGEN_BRANCH" https://github.com/RPi-Distro/pi-gen "$PIGEN_DIR"
fi

echo "==> staging compose + env into the appliance stage"
STAGE_FILES="$IMAGE_DIR/stage-evohub/00-evohub/files"
mkdir -p "$STAGE_FILES"
cp "$HERE/docker/docker-compose.yml" "$STAGE_FILES/docker-compose.yml"
cp "$HERE/docker/evohub.env"         "$STAGE_FILES/evohub.env"

# Default deploy key baked into the image so the on-Pi build works out of the box.
# Override per-card with /boot/firmware/idec_github. NOTE: the image then carries
# this key — keep releases private (or move to path deps to drop it).
DEPLOY_KEY="${EVOHUB_DEPLOY_KEY:-$HOME/.ssh/idec_github}"
rm -f "$STAGE_FILES/idec_github"
if [ -f "$DEPLOY_KEY" ]; then
  echo "==> baking default deploy key from $DEPLOY_KEY"
  cp -L "$DEPLOY_KEY" "$STAGE_FILES/idec_github"
else
  echo "==> WARNING: no deploy key at $DEPLOY_KEY (set EVOHUB_DEPLOY_KEY); the app"
  echo "    images won't build unless the deployer drops one on the boot partition."
fi

echo "==> staging app source (listener/UI build on the Pi at first boot)"
SRC_OUT="$STAGE_FILES/src"
rm -rf "$SRC_OUT"; mkdir -p "$SRC_OUT"
for d in Docker evoflow_listener evoflow_ui; do
  rsync -a --exclude='.venv' --exclude='__pycache__' --exclude='.pytest_cache' \
    "$HERE/../evohub/$d" "$SRC_OUT/"
done

echo "==> installing config + custom stage into pi-gen"
cp "$IMAGE_DIR/config" "$PIGEN_DIR/config"
rm -rf "$PIGEN_DIR/stage-evohub"
cp -r "$IMAGE_DIR/stage-evohub" "$PIGEN_DIR/stage-evohub"

echo "==> building (this is the long part)"
cd "$PIGEN_DIR"
docker rm -v pigen_work >/dev/null 2>&1 || true   # clear any stale container from a prior run
CONTINUE=0 ./build-docker.sh

echo
echo "==> done. Flashable image(s):"
ls -1 "$PIGEN_DIR/deploy/"*.img.gz 2>/dev/null || ls -1 "$PIGEN_DIR/deploy/" 2>/dev/null || true
echo "Flash with Raspberry Pi Imager (or: rpi-imager --cli <img> /dev/diskN)."
