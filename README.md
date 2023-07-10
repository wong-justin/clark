# clark 

(command-line audio/video marking)

[Demo](https://github.com/wong-justin/clark/assets/28441593/3515c933-185c-43fc-b1c0-040d31f8d366)

A TUI for interactive media playback and timestamping, using MPV.

Perfect when you want to stay in the command line and create timestamps while scripting.

## Examples

- Trim away content from the ends of a video:

```
clark video.mp4 --trim
```

- Choose where to split a concert recording into songs, and don't autoplay:

```
clark concert.mp3 --split --start-paused
```

- Timestamp using only audio from a video to avoid the extra window:

```
ffmpeg -i video.mkv -map 0:a -acodec copy /tmp/audio.mp4
clark /tmp/audio.mp4
```

- Convert timestamps to `HH:MM:SS:mmm`:

```
clark song.wav | awk '{system("date -u -d @" $0/1000 " +%T.%3N")}' 
```


## Installation

One way, something like: `git clone`, `pip install`, then `alias clark='python /path/to/clark.py'`

Or:

```
pip install -e git+https://github.com/wong-justin/clark-mpv.git#egg=clark-mpv
```

Requirements: [`mpv`](https://mpv.io/), `python~3.7`, and optionally `ffmpeg` for `--trim` and `--split`.

### Windows

#### Quick and dirty:

- `pip install clark-py`
- Extract `mpv-2.dll` from the [libmpv package](https://sourceforge.net/projects/mpv-player-windows/files/libmpv/) and place next to `clark`, wherever it is (eg: `%APPDATA%/Local/Programs/Python/Python3x/Lib/site-packages/clark-py/`), or anywhere else on `$PATH`.

#### Or more responsibly:

- Activate a virtual environment (eg. `python -m venv clark-env`) before `pip install clark-py`
- Extract `mpv-2.dll` from the [libmpv package](https://sourceforge.net/projects/mpv-player-windows/files/libmpv/) into `clark-env/Scripts/`
- Create a global alias that references `clark` in the venv, eg `clark.bat` = `call C:/path/to/clark-env/Scripts/activate && clark %*`

### Troubleshooting

The most common errors are related to `mpv` installation, so check the [`instructions`](https://github.com/jaseg/python-mpv#requirements) for `python-mpv`. See also [the context](https://github.com/jaseg/python-mpv/issues/60#issuecomment-352719773) for the extra Windows `.dll`.


## Usage

### Controls

```
| Keypress      | Description                            |
|---------------|----------------------------------------|
|  space        | play/pause                             |
|  j/l          | -/+ 15 secs                            |
|  left/right   | -/+ 5 secs                             |
|  down/up      | -/+ speed x0.2                         |
|  0-9          | seek to 0,10,...90%                    |
|  m            | mark timestamp at curr position        |
|  M            | delete timestamp                       |
|  J/L          | seek to prev/next timestamp and pause  |
|  q/esc        | quit and print timestamps in millis    |
```


### The TUI, a breakdown

```
                                           
 position  duration  timestamp...idx/total 
 ┌─┵──────────┵──────────┵─────────┵─┵─┐   
 │ 43:19 / 1:26:44     52:06.438   3/6 │   
 │ =================|                  ├──┐
 │       |      |       |    |   |     ├┐ │
 └─────────────────────────────────────┘│ │
                     timestamp markers  ┘ │ 
    seekbar, playing (>) or paused (|)  ──┘

```                                 

Note: timestamps clustered together will appear under one marker. In this case, the total timestamp count will not match the number of markers on screen. 


### Command-line

```
Usage: 
  clark <filepath> [--trim | --split]
                   [--start-paused]
                   [--start-muted]
  clark (-h | --version)

Options:

  The first two options cover common use cases for convenience.
  They create and execute ffmpeg commands so that you 
  don't have to make ugly scripts.
  Both cannot be executed at the same time.
  Input files remain unmodified.

  --trim          Extract between two timestamps
                  file.mp3 -> file_0.mp3

  --split         Cut at each timestamp
                  file.mp4 -> file_0.mp4, file_1.mp4, ...

  --start-paused  Disable autoplay

  --start-muted   Set volume to 0

  -h --help       Show this screen
  --version       Show version
```


### Offline docs 

```
clark --help

man clark
```

## Roadmap

From high to low priority:

- Timestamp import option. 

`clark --import 1000,2000,3000`. Example use case: adjusting automated timestamps that are always a little inaccurate, even >1 second behind.

- New controls: `,/.` to seek -/+ 1 frame for video or 1 ms for audio

- New TUI widget if necessary: speed, eg `x1.0`

- If truly motivated: keep everything in the command-line by converting video to ANSI-color unicode blocks. Likely involves porting to high-performance language (rust + batimg?) and discarding MPV. Seems worthy of a separate project, even if it keeps the same features and interface.


