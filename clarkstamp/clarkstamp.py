from blessed import Terminal
import mpv
from docopt import docopt
import subprocess
import sys
from pathlib import Path

doc = '''
Command-line audio/video marking.
A TUI for interactive timestamping.

clark /path/to/media_file

On start, media autoplays and will loop.
Video files spawn a window on start.
Audio files do not.
See keys for playback and timestamp control.
clark outputs timestamps, separated by newlines.
Timestamps are in milliseconds.

clark requires a valid mpv installation.
Options --trim and --split require ffmpeg.

See more details at:
https://github.com/wong-justin/clark

Controls:
  space       play/pause
  j/l         -/+ 15 secs
  left/right  -/+ 5 secs
  down/up     -/+ speed x0.2
  0-9         seek to 0,10,...90%
  m           make a new timestamp
  M           delete current timestamp 
  J/L         seek to prev/next timestamp
  q/esc       quit

Examples:
  clark file.mp4 --trim --start-paused
  clark file.mp3 --split
  
Usage: 
  clark <filepath> [--trim | --split]
                   [--start-paused]
                   [--start-muted]
  clark (-h | --version)

Options:
  --trim          Extract between two timestamps
  --split         Cut at each timestamp
  --start-paused  Disable autoplay
  --start-muted   Set volume to 0
  -h --help       Show this screen
  --version       Show version
'''

# === SETUP / HELPERS === 

class Model:
    '''Simple state object holding keyval pairs. Updates make re-renders.'''
    def __init__(self, *, state, render):
        for k,v in state.items():
            setattr(self, k, v)
        self._render = render

    def update(self, **state):
        for k,v in state.items():
            setattr(self, k, v)
        self.render()

    def render(self):
        self._render(self)

    def __repr__(self):
        return f'{vars(self)}'

def init_player(filepath):
    player = mpv.MPV()
    player.loop = True
    player.play(filepath)
    return player

def _format_time(millis, show_ms=False):
    mins = millis // (1000 * 60)
    secs = (millis // 1000) - (mins * 60)
    hours = None
    if mins >= 60:
        hours = mins // 60
        mins = mins % 60
    result = f'{hours}:{mins:02d}:{secs:02d}' if hours else f'{mins}:{secs:02d}'
    if show_ms:
        result += f'.{millis%1000}'
    return result

def _nearest_item_above(list_, value):
    if len(list_) == 0:
        return None
    for item in list_:
        if item > value:
            return item
    return None  # if value is less than all items

def _nearest_item_below(list_, value):
    if len(list_) == 0:
        return None
    for item in list_[::-1]:
        if item < value:
            return item
    return None  # if value is greater than all items

def print_row(term, numrow, line_contents):
    print(term.move_xy(0, numrow) + line_contents + term.clear_eol)

def _iter_pairs(iterable):
    iterable = iter(iterable)
    prev = next(iterable)
    for curr in iterable:
        yield prev, curr
        prev = curr

def _format_ffmpeg_timestamp(ms):
    # 12345 -> 12.345
    # not sure how it compares to HH:MM:SS.mmm in terms of ffmpeg support
    secs = ms // 1000
    remainder_ms = ms % 1000
    return f'{secs}.{remainder_ms:<03d}'

def _filename_incrementer(fp):
    i = 0
    path = Path(fp)
    while True:
        newpath = path.parent / (path.stem + f'_{i}' + path.suffix)
        yield str(newpath)
        i += 1

def ffmpeg_cut(*, fp_in, fp_out, start=0, end=None):
    ffmpeg_cmd = ''
    start_time = _format_ffmpeg_timestamp(start)
    if end is None:
        ffmpeg_cmd = f'ffmpeg -ss {start_time} -i {fp_in} {fp_out}'
    else:
        end_time = _format_ffmpeg_timestamp(end)
        ffmpeg_cmd = f'ffmpeg -ss {start_time} -to {end_time} -i {fp_in} {fp_out}'

    print(ffmpeg_cmd)
    p = subprocess.Popen(ffmpeg_cmd, 
                         shell=True, 
                         stdout=subprocess.PIPE)
    for line in p.stdout.readlines():
        sys.stdout.buffer.write(line)

# === UI / VIEW ===

def view_model(model, term):
    '''Example render:
    0:12 / 0:20             0:03.324      3/10
    ==========================>
        | ||   |    |||               |
    '''
    pt = player_times(model)
    ts = timestamp_stats(model)
    gap = term.width - len(pt) - len(ts) - 1
    print_row(term, 0, pt + ' ' * gap + ts)
    print_row(term, 1, player_progress_bar(model, term.width))
    print_row(term, 2, timestamp_bar(model, term.width))
    print(term.clear_eof)  # clear any overflow from resizes

def player_times(model):
    '''Current time and duration, eg 1:30 / 2:45'''
    position = _format_time(model.position_ms)
    duration = _format_time(model.duration_ms)
    return f'{position} / {duration}'

def player_progress_bar(model, total_cols):
    '''Progress bar representing playerhead position, eg =======>'''
    if model.duration_ms == 0:
        return '|'
    percent_completed = model.position_ms / model.duration_ms
    cols_filled = int( percent_completed * (total_cols - 1) )
    player_head = '|' if model.is_paused else '>'
    return '=' * cols_filled + player_head

def timestamp_bar(model, total_cols):
    '''Row of markers spaced corresponding to timestamps, eg  |   ||      |'''
    col_width_ms = model.duration_ms / (total_cols - 1)
    line = ''
    for timestamp in sorted(model.timestamps):
        i = int(timestamp / col_width_ms)
        if i == len(line) - 1:  # skip when overlapping existing marker,
            continue            #  allowing 'hidden' timestamps
        gap = i - len(line)
        line += ' ' * gap + '|'
    return line

def timestamp_stats(model):
    '''
    Text of most recent timestamp and its index when sorted, eg
    12:45.987    12/13
    '''
    if len(model.timestamps) == 0:
        return '0/0'
    selected_timestamp = model.timestamps[model.timestamp_index] 
    timestamp_formatted = _format_time(selected_timestamp, show_ms=True) 
    count = len(model.timestamps)
    i = sorted(model.timestamps).index(selected_timestamp)
    return f'{timestamp_formatted}      {i+1}/{count}'

# === BEHAVIOR / COMMANDS ===

class Commands:
    '''Groups behavior and interactions between media player and data model.
    Commands update the player, which will update the model.
    That order is necessary because of observer pattern in python-mpv.'''

    def __init__(self, *, model, player):
        self.model = model
        self.player = player
        self.command_for_keypress = {
            'q': lambda: False,
            361: lambda: False, # esc key
            ' ': self.toggle_paused,
            'm': self.mark_timestamp,
            'M': self.delete_timestamp,
            'J': self.seek_prev_timestamp,
            'L': self.seek_next_timestamp,
            258: lambda: self.change_speed(-0.2),  # down arrow
            259: lambda: self.change_speed(0.2),  # up arrow
            'j': lambda: self.seek(-15),
            'l': lambda: self.seek(15),
            260: lambda: self.seek(-5),  # left arrow
            261: lambda: self.seek(5),  # right arrow
            ',': lambda: self.seek(-0.016),  # seek backward 1 frame is broken; player rounds up i guess
            '.': lambda: self.seek(0.016),  # seek forward 1 frame
            '0': lambda: self.seek_percent(0),
            '1': lambda: self.seek_percent(10),
            '2': lambda: self.seek_percent(20),
            '3': lambda: self.seek_percent(30),
            '4': lambda: self.seek_percent(40),
            '5': lambda: self.seek_percent(50),
            '6': lambda: self.seek_percent(60),
            '7': lambda: self.seek_percent(70),
            '8': lambda: self.seek_percent(80),
            '9': lambda: self.seek_percent(90),
            ')': self.seek_end,  # Shift-0
        }

        # register callbacks
        @player.property_observer('playback-time')
        def time_observer(_name, value):
            # None when not loaded, negative when looping to beginning
            # position updates about every 0.06 seconds
            value = 0 if value is None or value < 0 else value
            model.update(position_ms=int(1000*value))

        @player.property_observer('duration')
        def time_observer(_name, value):
            value = 0 if value is None else value
            model.update(duration_ms=int(1000*value))

        @player.property_observer('pause')
        def time_observer(_name, value):
            model.update(is_paused=value)

    def toggle_paused(self):
        self.player.pause = not self.player.pause

    def seek(self, seconds_forward):
        self.player.playback_time += seconds_forward

    def seek_percent(self, percent):
        # probably only safe for ints 0-99
        # note: to implement 100, it's hard to seek to final millisecond.
        #  try going to final second instead.
        self.player.percent_pos = percent

    def change_speed(self, factor):
        self.player.speed += factor

    def mark_timestamp(self):
        timestamps = [*self.model.timestamps, self.model.position_ms]
        self.model.update(timestamps=timestamps, timestamp_index=len(timestamps)-1)

    def delete_timestamp(self):
        # TODO: fix unintuitive current timestamp model
        # deletes current timestamp index, which may be far away or wrong
        # intended to be used after navigating with J/L
        if self.model.timestamp_index is None:
            return
        i = self.model.timestamp_index
        updated_timestamps = [
            *self.model.timestamps[:i],
            *self.model.timestamps[i+1:]
        ]
        updated_index = max(i-1, 0) if len(updated_timestamps) > 0 else None
        self.model.update(timestamps=updated_timestamps, timestamp_index=updated_index)

    def seek_prev_timestamp(self):
        # pauses too
        prev_timestamp_ms = _nearest_item_below(
            sorted(self.model.timestamps), 
            self.model.position_ms - 1)
        if prev_timestamp_ms is None:
            return
        self.player.playback_time = prev_timestamp_ms / 1000
        i = sorted(self.model.timestamps).index(prev_timestamp_ms)
        self.player.pause = True
        self.model.update(timestamp_index=i)

    def seek_next_timestamp(self):
        # pauses too
        next_timestamp_ms = _nearest_item_above(
            sorted(self.model.timestamps), 
            self.model.position_ms + 1)
        if next_timestamp_ms is None:
            return
        self.player.playback_time = next_timestamp_ms / 1000
        i = sorted(self.model.timestamps).index(next_timestamp_ms)
        self.player.pause = True
        self.model.update(timestamp_index=i)

    def seek_end(self):
        # player.playback_time = (model.duration_ms - 1) / 1000
        self.player.playback_time = self.model.duration_ms // 1000


def run_app(start_paused, start_muted, filepath):
    '''Starts TUI. Returns list of timestamps on quit.'''
    term = Terminal()
    # TODO: throw readable error if bad filepath
    player = init_player(filepath)
    model = Model(render=lambda m: view_model(m, term), state={
        'position_ms': 0,
        'duration_ms': 0,
        'is_paused'  : False,
        'timestamps' : [],
        'timestamp_index': None,
    })
    if start_paused:
        player.pause = True
    if start_muted:
        player.volume = 0
    cmds = Commands(model=model, player=player)

    with term.fullscreen(), term.cbreak(), term.hidden_cursor():
        while True:
            model.render()
            input_ = term.inkey()
            # special int/constant or plain char
            key_input = input_.code or input_
            if key_input in cmds.command_for_keypress:
                result = cmds.command_for_keypress[key_input]()
                if result is False:
                    break

    player.terminate()  # stop playing audio/video. TODO: close player when parent process closes, ie on error
    print(term.clear, end='')  # remove any screen artifacts from last render
    return sorted(model.timestamps)

def run_cli():
    arguments = docopt(doc, version='clark 0.1.0')
    # arguments = {
    #   '--start-paused': False,
    #   '<filepath>': 'path/to/file',
    #   '--help'
    #   '--version'
    fp = arguments['<filepath>']
    if not Path(fp).is_file():
        print(f'Error: \'{fp}\' is not a valid filepath.', file=sys.stderr)
        return

    timestamps = run_app(
        start_paused=arguments['--start-paused'], 
        start_muted=arguments['--start-muted'],
        filepath=fp
    )
    for timestamp in timestamps:
        print(timestamp)

    fp_out = _filename_incrementer(fp)
    if arguments['--split'] is True and len(timestamps) > 0:
        ffmpeg_cut(fp_in=fp, fp_out=next(fp_out), end=timestamps[0])
        for start, end in _iter_pairs(timestamps):
            ffmpeg_cut(fp_in=fp, fp_out=next(fp_out), start=start, end=end)
        ffmpeg_cut(fp_in=fp, fp_out=next(fp_out), start=timestamps[-1])

    elif arguments['--trim'] is True:
        if len(timestamps) != 2:
            print(f'Error: expected exactly 2 timestamps to trim between; received {len(timestamps)}.', file=sys.stderr)
            return

        ffmpeg_cut(fp_in=fp, fp_out=next(fp_out), start=timestamps[0], end=timestamps[1])

if __name__ == '__main__':
    run_cli()
