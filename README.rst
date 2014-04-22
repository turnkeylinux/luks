Introduction
============

This program is a simple high-level wrapper for creating and accessing
LUKS encrypted filesystems.

Filesystems can be stored in any block device supported by the kernel.
For convenience, filesystems stored in regular files are also supported
transparently by using loopback devices.

Allocation (and reallocation) of the underlying storage layer in which
filesystems are created (e.g., LVM logical volume, hard disk partition,
loopfile) is up to the user and is beyond the scope of this program.

Usage examples
==============

creating and accessing a loopback LUKS filesystem::

    dd if=/dev/zero of=./loopfs bs=1M count=10
    luks-mkfs ./loopfs

    luks-mount ./loopfs ./mnt
    luks-umount ./mnt

creating and accessing a LUKS filesystem on a hard drive partition::

    cfdisk /dev/sdb # create partition /dev/sdb4
    luks-mkfs /dev/sdb4

    luks-mount /dev/sdb4 /mnt/sdb4
    luks-umount /mnt/sdb4


