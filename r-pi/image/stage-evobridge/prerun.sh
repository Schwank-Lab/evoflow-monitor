#!/bin/bash -e
# Standard pi-gen stage prelude: seed our rootfs from the previous stage.
if [ ! -d "${ROOTFS_DIR}" ]; then
	copy_previous
fi
