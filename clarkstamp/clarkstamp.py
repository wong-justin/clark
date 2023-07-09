from blessed import Terminal
import mpv
from docopt import docopt

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
  M           delete timestamp 
  J/L         seek to prev/next timestamp
  q/esc       quit

Examples:
  clark file.mp4 --trim --start-paused
  clark file.mp3 --split
  
Usage: 
  clark <filepath> [--trim | --split]
                   [--start-paused]
  clark (-h | --version)

Options:
  --trim          Extract between two timestamps
  --split         Cut at each timestamp
  --start-paused  Disable autoplay
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
    # player.pause = True
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

def register_player_observers(*, model, player):
    '''Define callbacks given an mpv instance'''
    # position updates about every 0.06 seconds
    @player.property_observer('playback-time')
    def time_observer(_name, value):
        # None when not loaded, negative when looping to beginning
        value = 0 if value is None or value < 0 else value
        model.update(position_ms=int(1000*value))

    @player.property_observer('duration')
    def time_observer(_name, value):
        value = 0 if value is None else value
        model.update(duration_ms=int(1000*value))

    @player.property_observer('pause')
    def time_observer(_name, value):
        model.update(is_paused=value)

def run_app():
    '''Starts TUI. Returns list of timestamps on quit.'''
    term = Terminal()
    # player = init_player(r'C:\Users\jkwon\Desktop\other\mysong.wav')
    player = init_player(r'C:\Users\jkwon\Desktop\other\fantastic_mr_fox.mp4')
    model = Model(render=lambda m: view_model(m, term), state={
        'position_ms': 0,
        'duration_ms': 0,
        'is_paused'  : True,
        'timestamps' : [],
        'timestamp_index': None,
    })
    register_player_observers(model=model, player=player)

    with term.fullscreen(), term.cbreak(), term.hidden_cursor():
        model.render()
        while True:
            input_ = term.inkey()
            if input_.code == term.KEY_ESCAPE or input_ == 'q':
                break
            # toggle play/pause
            elif input_ == ' ':
                player.pause = not player.pause
            # change playback speed
            elif input_.code == term.KEY_DOWN:
                player.speed -= 0.2
            elif input_.code == term.KEY_UP:
                player.speed += 0.2
            # seek +/- increments
            elif input_ == 'l':
                player.playback_time += 15
            elif input_ == 'j':
                player.playback_time -= 15
            elif input_.code == term.KEY_RIGHT:
                player.playback_time += 5
            elif input_.code == term.KEY_LEFT:
                player.playback_time -= 5
            elif input_ == '.':
                player.playback_time += 0.001
            elif input_ == ',':
                player.playback_time -= 0.001

            # seek 0-90%
            elif '0' <= input_ <= '9':
                player.percent_pos = int(input_) * 10
            # note: hard to seek to final millisecond, so go to final second instead
            elif input_ == ')':  # <S-0>
                # player.playback_time = (model.duration_ms - 1) / 1000
                player.playback_time = model.duration_ms // 1000
            # make a timestamp at current position
            elif input_ == 'm':
                timestamps = [*model.timestamps, model.position_ms]
                model.update(timestamps=timestamps, timestamp_index=len(timestamps)-1)
            # delete selected timestamp
            elif input_ == 'M':
                if model.timestamp_index is None:
                    continue
                i = model.timestamp_index
                updated_timestamps = [
                    *model.timestamps[:i],
                    *model.timestamps[i+1:]
                ]
                updated_index = max(i-1, 0) if len(updated_timestamps) > 0 else None
                model.update(timestamps=updated_timestamps, timestamp_index=updated_index)

            # seek to prev timestamp and pause
            elif input_ == 'J':
                prev_timestamp_ms = _nearest_item_below(
                    sorted(model.timestamps), 
                    model.position_ms - 1)
                if prev_timestamp_ms is None:
                    continue
                player.playback_time = prev_timestamp_ms / 1000
                i = sorted(model.timestamps).index(prev_timestamp_ms)
                player.pause = True
                model.update(timestamp_index=i)

            # seek to next timestamp and pause
            elif input_ == 'L':
                next_timestamp_ms = _nearest_item_above(
                    sorted(model.timestamps), 
                    model.position_ms + 1)
                if next_timestamp_ms is None:
                    continue
                player.playback_time = next_timestamp_ms / 1000
                i = sorted(model.timestamps).index(next_timestamp_ms)

                player.pause = True
                model.update(timestamp_index=i)
            model.render()
    return sorted(model.timestamps)

def run_cli():
    arguments = docopt(doc, version='clark 0.1.0')
    # print(arguments)
    # arguments = {
    #   '--start-paused': False,
    #   '<filepath>': '/path/to/file/',
    #   '--help'
    #   '--version'
    timestamps = run_app()
    for timestamp in timestamps:
        print(timestamp)

if __name__ == '__main__':
    run_cli()
