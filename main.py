
import curses
import traceback
import blessed
# import mpv


# === SETUP ===

class Model:

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

def init_curses():
    stdscr = curses.initscr()
    curses.noecho()    # turn off default keypress printing
    curses.cbreak()    # react to keys without enter 
    curses.curs_set(0) # hide cursor
    # print('\033[?25l') # or actually hide cursor
    stdscr.clear()
    return stdscr
                                        
def exit_curses(stdscr):
    # print('\033[?25h')
    curses.curs_set(1)
    curses.nocbreak()
    stdscr.keypad(False)
    curses.echo()
    curses.endwin()

def init_mpv(filepath):
    player = mpv.MPV(filepath)
    return player


# === APP DEFINITION ===

def view_model(model, stdscr):
    stdscr.addstr(0,0, 'hello world')
    stdscr.addstr(2,0, f'{model.xmax} {model.ymax}')
    if 'msg' in vars(model):
        stdscr.addstr(1,0, f'{model.msg}')
    else:
        pass
    stdscr.refresh()

def register_observers(model, player):
    
    @player.property_observer('time-pos')
    def time_observer(_name, value):
        model.update( position_ms=int(value*1000) )

# === RUN APP ===

def run():
    try:
        stdscr = init_curses()
        # player = init_mpv(r'C:\Users\jkwon\Desktop\other\mysong.wav')

        model = Model(render=lambda m: view_model(m, stdscr), state={
            'position_ms': 0,
            'duration_ms': 0,
            'is_paused'  : True,
            'xmax'       : 0,
            'ymax'       : 0,
        })

        # updates that must be defined outside event loop
        # register_observers(model, player)

        # event loop containing rest of update behavior and commands
        model.render()
        while True:
            input_ = stdscr.getch()
            if input_ == 27:
                return
            if input_ == ord('q'):
                return
            elif input_ == curses.KEY_RESIZE:
                return
                y,x = stdscr.getmaxyx()
                model.update(xmax=x, ymax=y)
            else:
                model.update(msg=input_)
    except Exception as err:
        exit_curses(stdscr)
        traceback.print_exc()
        



if __name__ == '__main__':
    run()
