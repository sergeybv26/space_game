import asyncio
import random
import time
import curses


TIC_TIMEOUT = 0.1
STAR_SYMBOLS = ['*', '+', '.', ':']

async def sleep(seconds):
    for _ in range(int(seconds * 1000)):
        await asyncio.sleep(0)

async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):
    """Display animation of gun shot, direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await sleep(1)

    canvas.addstr(round(row), round(column), 'O')
    await sleep(1)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await sleep(1)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed

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

def draw(canvas):
    # row, column = (5, 20)
    canvas.border()
    curses.curs_set(False)
    # while True:
    #     canvas.addstr(row, column, '*', curses.A_DIM)
    #     canvas.refresh()
    #     time.sleep(2)
    #     canvas.addstr(row, column, '*')
    #     canvas.refresh()
    #     time.sleep(0.3)
    #     canvas.addstr(row, column, '*', curses.A_BOLD)
    #     canvas.refresh()
    #     time.sleep(0.5)
    #     canvas.addstr(row, column, '*')
    #     canvas.refresh()
    #     time.sleep(0.3)
    star_quantity = random.randint(1, 100)
    rows, columns = canvas.getmaxyx()
    row_max, column_max = rows - 2, columns - 2
    row_center, column_center = row_max // 2, column_max // 2
    fire_coroutine = fire(canvas, row_center, column_center)
    while True:
        try:
            fire_coroutine.send(None)
            canvas.refresh()
        except StopIteration:
            break
    coroutines = [blink(canvas, random.randint(2, row_max), random.randint(2, column_max),
                        random.choice(STAR_SYMBOLS), random.randint(0, 3)) for _ in range(star_quantity)]

    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
                canvas.refresh()
            except StopIteration:
                coroutines.remove(coroutine)
        if len(coroutines) == 0:
            break
    time.sleep(TIC_TIMEOUT)

if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
