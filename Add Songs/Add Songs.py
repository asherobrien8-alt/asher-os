"""
Add Songs - put new songs on the iPod and into its playlists in one go.

Use it:  drag song files (or folders of songs) onto "Add Songs.bat" on the
iPod, or double-click "Add Songs.bat" and pick the files.

What it does:
  1. copies each song ONCE into  Music\\Artist\\Album\\  on the iPod
     (a song that's already there isn't copied again)
  2. asks which playlists to put them in (or makes a new playlist) and adds
     them to those playlist files - never twice in the same playlist
  3. if your PC Library and "iPod Playlists" folders exist, does the same
     there, so your computer copy stays in sync
  4. tells Asher OS to add the new songs to its library the next time it
     starts (eject, then the iPod updates by itself)
"""
import os, re, sys, shutil, pathlib, subprocess, unicodedata

HERE = pathlib.Path(__file__).resolve().parent
ROOT = pathlib.Path(HERE.anchor) if os.name == "nt" else HERE   # the iPod drive
MUSIC = ROOT / "Music"
PLAYLISTS = ROOT / "Playlists"
FLAG = ROOT / ".rockbox" / "asher" / "update_library"
PC_MUSIC = pathlib.Path.home() / "Music"
PC_LIBRARY = PC_MUSIC / "Library"
PC_PLAYLISTS = PC_MUSIC / "iPod Playlists"
AUDIO = {".mp3", ".m4a", ".aac", ".flac", ".ogg", ".opus", ".wav", ".wma", ".aiff", ".ape", ".wv"}
IMAGES = ("cover.jpg", "folder.jpg", "cover.png", "folder.png")

try:
    import mutagen
except ImportError:
    print("Getting the tag reader (one time only)...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "mutagen"])
    try:
        import mutagen
    except ImportError:
        mutagen = None
        print("Couldn't get it - songs will be sorted by their file names instead.\n")


def safe(name, fallback="Unknown"):
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name or "")
    name = re.sub(r"\s+", " ", name).strip().rstrip(". ")
    if name.upper() in {"CON", "PRN", "AUX", "NUL"} or re.fullmatch(r"(COM|LPT)\d", name.upper()):
        name += "_"
    return name[:120] or fallback


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "", s)


def first(tags, key):
    v = tags.get(key) if tags else None
    if v:
        v = v[0] if isinstance(v, list) else v
        return str(v).strip()
    return ""


def read_tags(p):
    info = {"artist": "", "album": "", "title": "", "track": None, "disc": None}
    if mutagen:
        try:
            try:
                t = mutagen.File(p, easy=True)
            except Exception:
                t = None
            if t is None and p.suffix.lower() == ".mp3":
                from mutagen.easyid3 import EasyID3
                t = EasyID3(p)
            if t is not None:
                info["artist"] = first(t, "albumartist") or first(t, "artist")
                info["album"] = first(t, "album")
                info["title"] = first(t, "title")
                m = re.match(r"\s*(\d+)", first(t, "tracknumber"))
                info["track"] = int(m.group(1)) if m else None
                m = re.match(r"\s*(\d+)", first(t, "discnumber"))
                info["disc"] = int(m.group(1)) if m else None
        except Exception:
            pass
    stem = p.stem
    if not info["title"] or not info["artist"]:
        # "Artist - Title" file names
        m = re.match(r"\s*(.+?)\s+-\s+(.+)", stem)
        if m:
            info["artist"] = info["artist"] or m.group(1)
            info["title"] = info["title"] or m.group(2)
    info["title"] = info["title"] or stem
    # the first artist only for the folder ("A, B & C" -> "A")
    info["artist"] = re.split(r"\s*(?:,|&| feat\.? | ft\.? | x |;)\s*", info["artist"] or "", maxsplit=1)[0].strip()
    info["album"] = re.sub(r"\s+-\s+(Single|EP)$", "", info["album"]).strip()
    return info


def place(p, base):
    """where the song goes inside a Music folder (same rules as the Library)"""
    t = read_tags(p)
    artist = safe(t["artist"], "Unknown Artist")
    if t["album"]:
        album, tn = safe(t["album"], "Unknown Album"), f"{t['track']:02d} - " if t["track"] else ""
        dn = f"{t['disc']}-" if t["disc"] and t["disc"] > 1 and tn else ""
    else:   # a single: its own folder "Title - Artist"
        album, tn, dn = safe(f"{t['title']} - {t['artist'] or 'Unknown Artist'}"), "", ""
    name = safe(f"{dn}{tn}{t['title']}", p.stem) + p.suffix.lower()
    return base / artist / album / name, t


def already_there(dest, title):
    """the same song already in that artist's folder (any album)?"""
    if dest.exists():
        return dest
    artist_dir = dest.parent.parent
    if artist_dir.is_dir():
        want = norm(title)
        for f in artist_dir.rglob("*"):
            if f.suffix.lower() in AUDIO and norm(re.sub(r"^\d+(-\d+)?\s*-\s*", "", f.stem)) == want:
                return f
    return None


def copy_song(src, base):
    dest, t = place(src, base)
    have = already_there(dest, t["title"])
    if have:
        return have, False
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    for img in IMAGES:      # bring the album cover along if it sits next to the song
        c = src.parent / img
        if c.exists() and not (dest.parent / img).exists():
            shutil.copy2(c, dest.parent / img)
    return dest, True


def playlist_line(song, base_music):
    return "../Music/" + song.relative_to(base_music).as_posix()


def playlist_has(pl, line):
    if not pl.exists():
        return False
    want = line.lower()
    for l in pl.read_text(encoding="utf-8-sig", errors="ignore").splitlines():
        if l.strip().replace("\\", "/").lower() == want:
            return True
    return False


def playlist_add(pl, line):
    if playlist_has(pl, line):
        return False
    text = pl.read_text(encoding="utf-8-sig", errors="ignore") if pl.exists() else "#EXTM3U\n"
    if text and not text.endswith("\n"):
        text += "\n"
    pl.write_text(text + line + "\n", encoding="utf-8", newline="\n")
    return True


def gather(args):
    files = []
    for a in args:
        p = pathlib.Path(a.strip('"'))
        if p.is_dir():
            files += sorted(f for f in p.rglob("*") if f.suffix.lower() in AUDIO)
        elif p.suffix.lower() in AUDIO and p.exists():
            files.append(p)
    return files


def pick_files():
    try:
        import tkinter, tkinter.filedialog
        r = tkinter.Tk(); r.withdraw()
        got = tkinter.filedialog.askopenfilenames(title="Pick the songs to add",
                                                  filetypes=[("Songs", " ".join("*" + e for e in sorted(AUDIO)))])
        r.destroy()
        return list(got)
    except Exception:
        return []


def main():
    if not MUSIC.is_dir():
        print(f"Can't find the Music folder at {MUSIC} - is this file on the iPod?")
        return
    files = gather(sys.argv[1:]) or gather(pick_files())
    files = [f for f in files if MUSIC not in f.resolve().parents]     # not ones already on the iPod
    if not files:
        print("No songs picked.")
        return
    print(f"Songs to add: {len(files)}")
    for f in files:
        print("   ", f.name)

    PLAYLISTS.mkdir(exist_ok=True)
    lists = sorted(PLAYLISTS.glob("*.m3u*"), key=lambda p: p.stem.lower())
    print("\nWhich playlists should they go in?")
    for i, p in enumerate(lists, 1):
        print(f"  {i:>2}. {p.stem}")
    print("   N. a New playlist")
    print("Type the numbers with spaces (like: 1 4 N), or just press Enter for none.")
    chosen = []
    for bit in input("> ").replace(",", " ").split():
        if bit.lower() == "n":
            name = safe(input("Name for the new playlist: "), "")
            if name:
                new = PLAYLISTS / f"{name}.m3u8"
                if not new.exists():
                    new.write_text("#EXTM3U\n", encoding="utf-8", newline="\n")
                chosen.append(new)
        elif bit.isdigit() and 1 <= int(bit) <= len(lists):
            chosen.append(lists[int(bit) - 1])
    chosen = list(dict.fromkeys(chosen))

    pc = PC_LIBRARY.is_dir() and PC_PLAYLISTS.is_dir()
    copied = reused = added = 0
    print()
    for f in files:
        song, new = copy_song(f, MUSIC)
        copied += new; reused += not new
        line = playlist_line(song, MUSIC)
        names = [pl.stem for pl in chosen if playlist_add(pl, line)]
        added += len(names)
        status = "copied" if new else "already on the iPod"
        print(f"  {song.stem}: {status}" + (f", added to {', '.join(names)}" if names else ""))
        if pc:      # keep the computer's copy the same
            try:
                pc_song, _ = copy_song(f, PC_LIBRARY)
                pc_line = playlist_line(pc_song, PC_LIBRARY)
                for pl in chosen:
                    playlist_add(PC_PLAYLISTS / pl.name, pc_line)
            except OSError as e:
                print("     (couldn't save it on the PC too:", e, ")")

    FLAG.parent.mkdir(parents=True, exist_ok=True)
    FLAG.write_text("new songs\n")
    print(f"\nDone: {copied} copied, {reused} were already on it, {added} playlist adds.")
    if pc:
        print("Also saved to your PC Library and iPod Playlists.")
    print("Eject the iPod - Asher OS adds the new songs to its library when it starts.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Something went wrong:", e)
