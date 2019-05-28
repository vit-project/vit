import re
BRIGHT_REGEX = re.compile('.*bright.*')

def task_256_to_urwid_256():
    manual_map = {
        'red': 'dark red',
        'green': 'dark green',
        'blue': 'dark blue',
        'cyan': 'dark cyan',
        'magenta': 'dark magenta',
        'gray': 'light gray',
        'yellow': 'brown',
        'color0': 'black',
        'color1': 'dark red',
        'color2': 'dark green',
        'color3': 'brown',
        'color4': 'dark blue',
        'color5': 'dark magenta',
        'color6': 'dark cyan',
        'color7': 'light gray',
        'color8': 'dark gray',
        'color9': 'light red',
        'color10': 'light green',
        'color11': 'yellow',
        'color12': 'light blue',
        'color13': 'light magenta',
        'color14': 'light cyan',
        'color15': 'white',
    }
    manual_map.update(task_color_gray_to_g())
    manual_map.update(task_color_to_h())
    manual_map.update(task_rgb_to_h())
    return manual_map

def task_bright_to_color(color_string):
    color_map = {
        'bright black': 'color8',
        'bright red': 'color9',
        'bright green': 'color10',
        'bright yellow': 'color11',
        'bright blue': 'color12',
        'bright magenta': 'color13',
        'bright cyan': 'color14',
        'bright white': 'color15',
    }
    if BRIGHT_REGEX.match(color_string):
        for bright_color in color_map:
            color_string = color_string.replace(bright_color, color_map[bright_color])
    return color_string

def task_color_gray_to_g():
    color_map = {}
    for i in range(0, 24):
        gray_key = 'gray%d' % i
        color_key = 'color%d' % (i + 232)
        # NOTE: This is an approximation of the conversion, close enough!
        value = 'g%d' % (i * 4)
        color_map[gray_key] = value
        color_map[color_key] = value
    return color_map

def task_color_to_h():
    color_map = {}
    for i in range(16, 232):
        key = 'color%d' % i
        value = 'h%d' % i
        color_map[key] = value
    return color_map

def task_rgb_to_h():
    index_to_hex = [
        '0',
        '6',
        '8',
        'a',
        'd',
        'f',
    ]
    color_map = {}
    count = 0
    for r in range(0, 6):
        for g in range(0, 6):
            for b in range(0, 6):
                key = 'rgb%d%d%d' % (r, g, b)
                value = '#%s%s%s' % (index_to_hex[r], index_to_hex[g], index_to_hex[b])
                color_map[key] = value
                count += 1
    return color_map
