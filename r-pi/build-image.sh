#!/usr/bin/env bash
#
# Build the EvoHub appliance image with pi-gen (in Docker).
#
# Produces a flashable Raspberry Pi OS Lite (arm64) image that boots straight
# into the EvoHub stack: Postgres + Mosquitto + Grafana + listener + UI under
# docker compose, with the hub acting as its own Wi-Fi access point (evo-net).
# Every container image is built or pulled here and preloaded into the SD image,
# so the hub needs no internet access, on first boot or ever.
#
# Requirements on the BUILD host (your laptop or CI):
#   - Docker 28 or newer, able to run linux/arm64 containers (native on Apple
#     Silicon and arm64 CI runners, via qemu elsewhere)
#   - ~15 GB free disk and ~30-60 min
#
# Usage:
#   ./build-image.sh
# Output:
#   r-pi/image/.pi-gen/deploy/*-evohub.img.xz
#
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_DIR="$HERE/image"
PIGEN_DIR="${PIGEN_DIR:-$IMAGE_DIR/.pi-gen}"
PIGEN_BRANCH="${PIGEN_BRANCH:-arm64}"   # 64-bit: native on Apple Silicon + no 32-bit setarch path
COMPOSE="$HERE/docker/docker-compose.yml"
ENV_FILE="$HERE/docker/evohub.env"
# Kept outside the pi-gen tree: pi-gen copies its whole tree into a Docker build
# context, so the image tarball is mounted into the build container instead.
IMAGES_DIR="$IMAGE_DIR/.images"

echo "==> pi-gen checkout: $PIGEN_DIR ($PIGEN_BRANCH)"
if [ ! -d "$PIGEN_DIR/.git" ]; then
  git clone --depth=1 --branch "$PIGEN_BRANCH" https://github.com/RPi-Distro/pi-gen "$PIGEN_DIR"
fi

echo "==> staging compose + env into the appliance stage"
STAGE_FILES="$IMAGE_DIR/stage-evohub/00-evohub/files"
rm -rf "$STAGE_FILES"; mkdir -p "$STAGE_FILES"
cp "$COMPOSE"  "$STAGE_FILES/docker-compose.yml"
cp "$ENV_FILE" "$STAGE_FILES/evohub.env"
# Grafana datasource + dashboards, so the hub serves EvoMonitor on first boot
# instead of an empty Grafana.
cp -r "$HERE/docker/grafana" "$STAGE_FILES/grafana"

echo "==> building the listener and UI images (linux/arm64)"
docker build --platform linux/arm64 -t evoflow_listener:latest "$HERE/../evohub/evoflow_listener"
docker build --platform linux/arm64 -t evoflow_ui:latest       "$HERE/../evohub/evoflow_ui"

echo "==> pulling the Postgres, Mosquitto and Grafana images (linux/arm64)"
DOCKER_DEFAULT_PLATFORM=linux/arm64 \
  docker compose -f "$COMPOSE" --env-file "$ENV_FILE" pull postgres mosquitto grafana

echo "==> saving every image the compose file uses, for preloading"
mkdir -p "$IMAGES_DIR"
# Word splitting is intended: one argument per image name.
docker save --platform linux/arm64 -o "$IMAGES_DIR/evohub-images.tar" \
  $(docker compose -f "$COMPOSE" --env-file "$ENV_FILE" config --images | sort -u)
ls -lh "$IMAGES_DIR/evohub-images.tar"

echo "==> installing config + custom stage into pi-gen"
cp "$IMAGE_DIR/config" "$PIGEN_DIR/config"
rm -rf "$PIGEN_DIR/stage-evohub"
cp -r "$IMAGE_DIR/stage-evohub" "$PIGEN_DIR/stage-evohub"
# Only the EvoHub image is exported, not the intermediate Lite image.
touch "$PIGEN_DIR/stage2/SKIP_IMAGES"

echo "==> building (this is the long part)"
cd "$PIGEN_DIR"
docker rm -v pigen_work >/dev/null 2>&1 || true   # clear any stale container from a prior run
PIGEN_DOCKER_OPTS="--volume $IMAGES_DIR:/evohub-images:ro" CONTINUE=0 ./build-docker.sh

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
