import sys
import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk
if len(sys.argv)<2:
    file_type = 'unknown'       # "image/jpeg"
else:
    file_type = sys.argv[1]

dialog = Gtk.AppChooserDialog.new_for_content_type(None,
                                                   Gtk.DialogFlags.MODAL, file_type)
response = dialog.run()
app_info = dialog.get_app_info()
dialog.destroy()
if app_info and response == Gtk.ResponseType.OK:
    print(app_info.get_executable(),end='')
else:
    print('',end='')
exit(0)