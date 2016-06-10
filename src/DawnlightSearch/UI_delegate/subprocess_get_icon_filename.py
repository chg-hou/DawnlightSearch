from __future__ import print_function
import sys, os

import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import Gio
DEFAULT_ICON_SIZE=32

ICON_THEME = Gtk.IconTheme.get_default()


input_str = ' '
while 1:
    # TODO: watch parent's status and quit when needed.
    # input_str != '' maybe not garantie

    input_str = sys.stdin.readline()
    if input_str == 'EXIT\n' or input_str == '':
        break
    icon_name = input_str[:-1]#.decode(encoding='UTF-8')

    # https://developer.gnome.org/gtk3/stable/GtkIconTheme.html#gtk-icon-theme-load-icon
    # choose_icon (icon_names): If icon_names contains more than one name, this function tries them all in the given order before falling back to inherited icon themes.
    icon_info = ICON_THEME.lookup_icon(icon_name, DEFAULT_ICON_SIZE,
                                       0)
    if not icon_info:
        icon_info = ICON_THEME.lookup_icon('unknown', DEFAULT_ICON_SIZE, 0)

    print(icon_info.get_filename(),end='\n')
