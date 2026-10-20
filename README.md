# Asher OS

A custom operating system for iPods, built on [Rockbox](https://www.rockbox.org/).
It dual boots with Apple's own software, so the iPod can always go back to it.

Current version: **2.5.2**

## Supported iPods

| iPod | Build |
|---|---|
| iPod Classic 6th / 7th gen | `ipod6g` |
| iPod Video 5th / 5.5 gen (30, 60 and 80 GB; the 64 MB build fits itself to 32 MB) | `ipodvideo --ram=64` |
| iPod nano 3rd gen | `ipodnano3g` |

## What's in this repo

- `asher_os_source.patch`: every Asher OS change, as one patch on top of Rockbox
  commit `e5092187c5219056dbd2dde99f5cf55515a6d37d`.
- `.github/workflows/build.yml`: builds the firmware for all three iPods.
  Run it from the **Actions** tab ("Build Asher OS", then "Run workflow"); each
  iPod's firmware zip shows up under the run's artifacts.

The wallpaper and theme pack is not stored here. The GitHub build gives the
firmware only; the complete install zips (firmware plus wallpapers and themes)
are made separately.

## Building by hand

```sh
git clone https://github.com/Rockbox/rockbox.git
cd rockbox
git checkout e5092187c5219056dbd2dde99f5cf55515a6d37d
git apply ../asher_os_source.patch
mkdir build && cd build
../tools/configure --target=ipod6g --type=n    # or one of the builds above
make -j"$(nproc)" && make zip
```

## Installing

Copy the whole `.rockbox` folder from the install zip to the top level of the
iPod (show hidden files first), replace everything, eject, then reboot.

Asher OS is based on Rockbox and is released under the GNU GPL, version 2 or
later, the same as Rockbox.
