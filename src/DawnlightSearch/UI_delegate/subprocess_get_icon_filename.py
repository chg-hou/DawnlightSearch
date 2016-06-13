from __future__ import print_function
import sys, os

import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import Gio

DEFAULT_ICON_SIZE = 32

ICON_THEME = Gtk.IconTheme.get_default()

icon_name = sys.argv[1]
# https://developer.gnome.org/gtk3/stable/GtkIconTheme.html#gtk-icon-theme-load-icon
# choose_icon (icon_names): If icon_names contains more than one name, this function tries them all in the given order before falling back to inherited icon themes.
icon_info = ICON_THEME.lookup_icon(icon_name, DEFAULT_ICON_SIZE,
                                   0)
if not icon_info:
    icon_info = ICON_THEME.lookup_icon('unknown', DEFAULT_ICON_SIZE, 0)

print(icon_info.get_filename(), end='')
exit(0)