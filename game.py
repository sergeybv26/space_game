import asyncio
from functools import partial
from itertools import cycle
import random
import time
import curses

from environs import Env


TIC_TIMEOUT = 0.1
STAR_SYMBOLS = ['*', '+', '.', ':']
SPACE_KEY_CODE = 32
LEFT_KEY_CODE = 260
RIGHT_KEY_CODE = 261
UP_KEY_CODE = 259
DOWN_KEY_CODE = 258
STATES = {
    "spaceship_state": ""
}


def get_frame_size(text):
    """Calculate size of multiline text fragment, return pair — number of rows and colums."""

    lines = text.splitlines()
    rows = len(lines)
    columns = max([len(line) for line in lines])
    return rows, columns

def read_controls(canvas):
    """Read keys pressed and returns tuple witl controls state."""

    rows_direction = columns_direction = 0
    space_pressed = False

    while True:
        pressed_key_code = canvas.getch()

        if pressed_key_code == -1:
            # https://docs.python.org/3/library/curses.html#curses.window.getch
            break

        if pressed_key_code == UP_KEY_CODE:
            rows_direction = -1

        if pressed_key_code == DOWN_KEY_CODE:
            rows_direction = 1

        if pressed_key_code == RIGHT_KEY_CODE:
            columns_direction = 1

        if pressed_key_code == LEFT_KEY_CODE:
            columns_direction = -1

        if pressed_key_code == SPACE_KEY_CODE:
            space_pressed = True

    return rows_direction, columns_direction, space_pressed

def draw_frame(canvas, start_row, start_column, text, negative=False):
    """Draw multiline text fragment on canvas, erase text instead of drawing if negative=True is specified."""

    rows_number, columns_number = canvas.getmaxyx()

    for row, line in enumerate(text.splitlines(), round(start_row)):
        if row < 0:
            continue

        if row >= rows_number:
            print('ERROR')
            break

        for column, symbol in enumerate(line, round(start_column)):
            if column < 0:
                continue

            if column >= columns_number:
                break

            if symbol == ' ':
                continue

            # Check that current position it is not in a lower right corner of the window
            # Curses will raise exception in that case. Don`t ask why…
            # https://docs.python.org/3/library/curses.html#curses.window.addch
            if row == rows_number - 1 and column == columns_number - 1:
                continue

            symbol = symbol if not negative else ' '
            canvas.addch(row, column, symbol)

async def sleep(seconds):
    for _ in range(int(seconds * 10)):
        await asyncio.sleep(0)

async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):
    """Display animation of gun shot, direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed

async def animate_spaceship(frames):
    for frame in cycle(frames):
        STATES['spaceship_state'] = frame
        await asyncio.sleep(0)

async def move_spaceship(canvas):
    rows, columns = canvas.getmaxyx()
    row_max, column_max = rows - 1, columns - 1
    row, column = row_max // 2, column_max // 2

    while True:
        rows_direction, columns_direction, space_pressed = read_controls(canvas)
        frame = STATES['spaceship_state']
        frame_rows, frame_columns = get_frame_size(frame)
        row, column = row + rows_direction, column + columns_direction

        if row + frame_rows // 2 >= row_max - 5:
            row = row_max - frame_rows // 2 - 5
        elif column + frame_columns // 2 >= column_max - 2:
            column = column_max - frame_columns // 2 - 3
        elif row - frame_rows // 2 <= - 3:
            row = frame_rows // 2 - 3
        elif column - frame_columns // 2 <= 0:
            column = frame_columns // 2 + 1
        draw_frame(canvas, row, column, frame)
        previos_frame = frame
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, previos_frame, negative=True)

async def blink(canvas, row, column, symbol='*', state=0):
    while True:
        match state:
            case 0:
                canvas.addstr(row, column, symbol, curses.A_DIM)
                state = 1
                await sleep(2)

            case 1:
                canvas.addstr(row, column, symbol)
                state = 2
                await sleep(0.3)

            case 2:
                canvas.addstr(row, column, symbol, curses.A_BOLD)
                state = 3
                await sleep(0.5)

            case 3:
                canvas.addstr(row, column, symbol)
                state = 0
                await sleep(0.3)

def draw(canvas, frames):
    coroutines = []
    canvas.border()
    curses.curs_set(False)
    star_quantity = random.randint(1, 100)
    rows, columns = canvas.getmaxyx()
    row_max, column_max = rows - 2, columns - 2
    row_center, column_center = row_max // 2, column_max // 2
    fire_coroutine = fire(canvas, row_center, column_center)
    spaceship_coroutine = animate_spaceship(frames)
    move_spaceship_coroutine = move_spaceship(canvas)

    coroutines.append(fire_coroutine)
    coroutines.append(spaceship_coroutine)
    coroutines.append(move_spaceship_coroutine)
    coroutines.extend([blink(canvas, random.randint(2, row_max), random.randint(2, column_max),
                       random.choice(STAR_SYMBOLS), random.randint(0, 3)) for _ in range(star_quantity)])

    while True:
        canvas.border()
        canvas.nodelay(True)
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
                canvas.refresh()
            except StopIteration:
                coroutines.remove(coroutine)
        if len(coroutines) == 0:
            break
        time.sleep(TIC_TIMEOUT)

def main():
    env = Env()
    env.read_env()
    frames_path = env('FRAMES_PATH')
    frames = []
    with open(f'{frames_path}rocket_frame_1.txt', 'r') as f:
        frame = f.read()
        frames.append(frame)
    with open(f'{frames_path}rocket_frame_2.txt', 'r') as f:
        frame = f.read()
        frames.append(frame)
    draw_partial = partial(draw, frames=frames)
    curses.update_lines_cols()
    curses.wrapper(draw_partial)

if __name__ == '__main__':
    main()
