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
BORDER_SIZE = 2


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

    while BORDER_SIZE < row < max_row and BORDER_SIZE < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed

async def move_spaceship(canvas, frames):
    rows, columns = canvas.getmaxyx()
    row_max, column_max = rows - BORDER_SIZE, columns - BORDER_SIZE
    row, column = row_max // 2, column_max // 2
    frame_generator = cycle(frames)

    while True:
        rows_direction, columns_direction, space_pressed = read_controls(canvas)
        current_frame = next(frame_generator)

        frame_rows, frame_columns = get_frame_size(current_frame)
        row, column = row + rows_direction, column + columns_direction

        row = max(1, min(row, row_max - frame_rows))
        column = max(1, min(column, column_max - frame_columns))

        draw_frame(canvas, row, column, current_frame)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, current_frame, negative=True)

async def blink(canvas, row, column, symbol='*', init_delay=0):
    rendering_modes = [
        (curses.A_DIM, 2),
        (curses.A_NORMAL, 0.3),
        (curses.A_BOLD, 0.5),
        (curses.A_NORMAL, 0.3)
    ]
    canvas.addstr(row, column, symbol, curses.A_DIM)
    await sleep(2 + init_delay)

    rendering_modes_generator = cycle(rendering_modes)

    while True:
        effect, delay = next(rendering_modes_generator)
        canvas.addstr(row, column, symbol, effect)
        await sleep(delay)

def draw(canvas, frames):
    coroutines = []
    canvas.border()
    canvas.nodelay(True)
    curses.curs_set(False)
    star_quantity = random.randint(1, 100)
    rows, columns = canvas.getmaxyx()
    row_max, column_max = rows - BORDER_SIZE, columns - BORDER_SIZE
    row_center, column_center = row_max // 2, column_max // 2
    fire_coroutine = fire(canvas, row_center, column_center)
    move_spaceship_coroutine = move_spaceship(canvas, frames)

    coroutines.append(fire_coroutine)
    coroutines.append(move_spaceship_coroutine)
    coroutines.extend(
        [
            blink(
                canvas,
                random.randint(2, row_max),
                random.randint(2, column_max),
                random.choice(STAR_SYMBOLS),
                random.randint(0, 10)
            ) for _ in range(star_quantity)
        ]
    )

    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        if len(coroutines) == 0:
            break
        canvas.refresh()
        time.sleep(TIC_TIMEOUT)

def main():
    env = Env()
    env.read_env()
    frames_path = env('FRAMES_PATH')
    frames = []
    with open(f'{frames_path}rocket_frame_1.txt', 'r') as f:
        frame = f.read()
        frames.append(frame)
        frames.append(frame)
    with open(f'{frames_path}rocket_frame_2.txt', 'r') as f:
        frame = f.read()
        frames.append(frame)
        frames.append(frame)
    draw_partial = partial(draw, frames=frames)
    curses.update_lines_cols()
    curses.wrapper(draw_partial)

if __name__ == '__main__':
    main()
