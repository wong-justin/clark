# clark 

(command-line audio/video marking)

[Demo](https://github.com/wong-justin/clark/assets/28441593/3515c933-185c-43fc-b1c0-040d31f8d366)

A TUI for media playback and timestamping, using [mpv](https://mpv.io/).

Designed for when you want to stay in the command line and create timestamps.

## Installation

```
pip install https://github.com/wong-justin/clark/archive/main.zip
```

or a bit slower, cloning the whole repo:

```
pip install git+https://github.com/wong-justin/clark.git
```

Then check that it works, especially concerning `mpv`:

```
clark --version
clark path/to/sample/audio
```

Requirements: `mpv`, `python~3.7`, and optionally `ffmpeg` for `--trim` and `--split`.

Read more about the installation process and other quirks in the <a href="https://wonger.dev/posts/clark">blog post</a>.

## Examples

My most common use cases:

- I have a recording of multiple songs, and I want to crop them out as individual files with millisecond precision (why do people start clapping so early??): `clark concert.mp3 --split`

- I have a screen recording, and the beginning and end have cruft that needs trimming: `clark recording.mp4 --trim`

- If I'm trimming a video and don't want to be bothered by audio, I'll `--start-muted`. If it's a long file, I'll mash `l` to seek forward, or jump to positions like 50% with `5`. When it's close to the point I want to mark, I'll tap `<Down-Arrow>` a bit to slow down in increments of 0.2x. I'll mark a timestamp with `m`, seek back to it with `J`, and replay it again to make sure it sounds exactly right. If it's not good, I'll delete the timestamp with `M` and retry. And then `q` to finish.

- Convert timestamps to `HH:MM:SS:mmm`:

```
clark song.wav | awk '{system("date -u -d @" $0/1000 " +%T.%3N")}' 
```

## Usage

### Controls

Kinda like youtube keyboard shortcuts:

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
```

## Roadmap

From high to low priority:

- Fix current timestamp not matching current seek position

- New TUI widget for speed, eg `x1.0`

- Document any quirky behavior

- Timestamp import option. `clark --import 1000,2000,3000`. Example use case: adjusting automated timestamps that are always a little inaccurate, even >1 second behind.

- New controls: `,/.` to seek -/+ 1 frame for video or 1 ms for audio

- If truly motivated: keep everything in the command-line and remove the gui video window, and the mpv dependency overall, by converting video to ANSI-color unicode blocks. Likely involves porting to high-performance language (rust + batimg?). Seems worthy of a separate project, even if it keeps the same features and interface.

- make a man page, just for fun
