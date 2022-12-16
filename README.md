# clark 

(command-line audio/video marking)

[Demo/Features]

A TUI for interactive media playback and timestamping, using MPV.

Perfect when you want to stay in the command line and create timestamps while scripting.

## Installation

```
pip install -e git+https://github.com/wong-justin/clark.git#egg=clarkstamps
```

Requirements: [`mpv`](https://mpv.io/), `python~3.7`

### Windows

Regular mpv player binaries on Windows are missing a necessary library. Read about [the solution](https://github.com/jaseg/python-mpv/issues/60#issuecomment-352719773) if you want, and choose between the following:

#### Quick and dirty:
- `pip install clarkstamp` globally
- Extract `mpv-2.dll` from the [libmpv package](https://sourceforge.net/projects/mpv-player-windows/files/libmpv/) and place next to `clark`, wherever it is (eg: `%APPDATA%/Local/Programs/Python/Python3x/Lib/site-packages/clarkstamp/`)

#### Seems more responsible:
- Activate a virtual environment (eg. `python -m venv clark-env`) before `pip install clarkstamp`
- Extract `mpv-2.dll` from the [libmpv package](https://sourceforge.net/projects/mpv-player-windows/files/libmpv/) into `clark-env/Scripts/`
- create a global alias that references `clark` in the venv, eg `clark.bat` = `call C:/path/to/clark-env/Scripts/activate && clark %*`

### Troubleshooting

The most common  errors come from getting `mpv` working with the script, so read the [`installation instructions`](https://github.com/jaseg/python-mpv#requirements) for `python-mpv`.


## Usage

### Command-line

```
  clark <filepath> [--start-paused]
  clark -h | --help
  clark --version
```

### Controls

| Keypress      | Description                            |
|---------------|----------------------------------------|
| `space`       | play/pause                             |
| `j/l `        | -/+ 15 secs                            |
| `left/right ` | -/+ 5 secs                             |
| `down/up `    | -/+ speed x0.2                         |
| `0-9 `        | seek to 0,10,...90%                    |
| `m `          | mark timestamp at curr position        |
| `M `          | delete timestamp                       |
| `J/L `        | seek to prev/next timestamp and pause  |
| `q/esc `      | quit and print timestamps in millis    |


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


### Useful scripts

- Trim a video between two timestamps ([clarktrim](./examples/trim):

- Avoid a video player window by using an audio stream instead:

- Convert millisecond timestamps to `HH:MM:SS` (useful for ffmpeg)
<br />

```
clark file | xargs -I _ date -u -d @_ +"%T"
```

- Quickly find and cut a portion of video:
<br />

```
clark video.mp4 | xargs -I _ date -u -d @_ +"%T" | xargs printf "-ss %s -to %s"
```

- Split a concert into separate songs, precisely where you feel is best:
<br />

```
clark | ffmpeg --cut-at 0,1,2,3
```

- Manually count occurrences of some event, especially when you want easy backtracking as a safety net when you mess up:
<br />

```
clark how_many_blinks.mp4 | xargs countlines echo
```

- Use `clark` simply as a media player, because there aren't many command-line options for viewing and controlling playback:
<br />

```
clark song.mp3
```

### Anti-use cases 

- Captioning/subtitling. Incorporating text editing feels beyond the scope of the tool.

- Advanced audio/video editing. GUIs shine here because the extra visual feedback is really important. The command-line doesn't do everything well, sadly. Unless someone makes a terminal video editor that uses [ANSI-color converted video](https://github.com/kugge/batimg)...

- Timestamping worthy of automation. It may be easier to make the computer detect the timestamps than it is to find them all manually (eg. automatic captioning, cutting on silence, computer vision, or a custom algorithm). But I always find it a hassle to set up even the simplest audio detection, so my threshold is near N = 1000.

- Requiring alternatives to python/mpv. These made it easy to implement `clark`, but feel free to port it to another language or media player.


### Offline docs 

```
clark --help

man clark
```

## Roadmap

- New command-line option: importing timestamps, `clark --import /path/to/timestamps`. Example use case: adjusting automated timestamps that are always a little inaccurate, ~1 second off.
- New controls: `,/.` to seek -/+ 1 frame for video or 1 ms for audio
- New TUI widget: speed, eg `x1.0`
- Less important options: `--format-time`, `--from --to`
- If truly motivated: keep everything in the command-line by converting video to ANSI-color unicode blocks. Likely involves porting to high-performance language (rust + batimg?) and discarding MPV. Seems worthy of a separate project, even if it keeps the same features and interface.


