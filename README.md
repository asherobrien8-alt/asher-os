# Asher OS

A custom operating system for iPods, built on [Rockbox](https://www.rockbox.org/).
It dual boots with Apple's own software, so the iPod can always go back to it.

Current version: **2.6.2**

## Supported iPods

| iPod | Build |
|---|---|
| iPod Classic 6th / 7th gen | `ipod6g` |
| iPod Video 5th gen (30 and 60 GB) | `ipodvideo --ram=64`, `EXTRA_DEFINES=-DASHER_VIDEO_GEN=50` |
| iPod Video 5.5 gen (30 and 80 GB) | `ipodvideo --ram=64`, `EXTRA_DEFINES=-DASHER_VIDEO_GEN=55` |
| iPod nano 3rd gen | `ipodnano3g` |

## What's in this repo

- `asher_os_source.patch`: every Asher OS change, as one patch on top of Rockbox
  commit `e5092187c5219056dbd2dde99f5cf55515a6d37d`.
- `.github/workflows/build.yml`: builds the firmware for every iPod above.
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

Finished builds are also put on the `builds` branch, named with the version
and the iPod they're for (e.g. `AsherOS_2.5.8_iPod_Video_5.5_gen.zip`).

## Adding music

Copy the two files in `Add Songs/` to the top of the iPod drive once. Then
drag songs onto `Add Songs.bat`, pick the playlists, eject: the song is copied
once into `Music\Artist\Album\`, added to those playlists (never twice), and
the iPod adds it to its library by itself when it starts.

On the iPod: hold Play on a song > Add to Playlist to put it in more playlists, or
Remove from Playlist to take it out of one. A song that's in no playlist any more
waits in Playlists > Vacant Songs.

Asher OS is based on Rockbox and is released under the GNU GPL, version 2 or
later, the same as Rockbox.
