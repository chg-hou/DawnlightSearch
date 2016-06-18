#!/usr/bin/env python
# -*- coding: utf-8 -*-

# https://developer.gnome.org/pygobject/stable/
# http://www.pygtk.org/docs/pygobject/gio-class-reference.html

# https://developer.gnome.org/gtk3/stable/GtkIconTheme.html#gtk-icon-theme-lookup-icon
# http://lazka.github.io/pgi-docs/
from __future__ import print_function
from __future__ import absolute_import
from functools import partial
from gi.repository import Gio
try:
    from .._Global_Qt_import import *
    from .._Global_DawnlightSearch import *
except:
    class ddd:
        pass
    GlobalVar = ddd()

import mimetypes
import sys, os
import subprocess

_qicon_cache_for_build_qicon = {}
_iconfilename_cache_for_get_icon_filename = {}
DEFAULT_ICON_SIZE = 32


def get_file_type(filename, isPath):
    if isPath:
        type_ = 'folder'
    else:
        type_, encoding = mimetypes.guess_type(filename)
        type_ = 'unknown' if not type_ else type_  # 'empty'
    return type_

def _get_icon_filename(icon_name):
    if not (icon_name in _iconfilename_cache_for_get_icon_filename):
        try:
            python_exe = sys.executable
            py_path = os.path.dirname(os.path.abspath(__file__))
            subprocess_path = os.path.join(py_path, 'subprocess_get_icon_filename.py')
            icon_path = subprocess.check_output([python_exe, subprocess_path, icon_name])
            _iconfilename_cache_for_get_icon_filename[icon_name] = icon_path.decode(encoding='UTF-8')
        except Exception as e:
            _iconfilename_cache_for_get_icon_filename[icon_name] = ''
            print('_get_icon_filename ERROR: '+str(e))
    return _iconfilename_cache_for_get_icon_filename[icon_name]

def get_app_icon_filename(app_info, size=DEFAULT_ICON_SIZE):

    if not app_info:
        return None
    themed_icon = app_info.get_icon()
    if not themed_icon:
        return None
    icon_name = themed_icon.get_names()[0]

    return _get_icon_filename(icon_name)

def app_launch_files(launch, filename_list):
    from gi.repository import Gio
    try:
        filename_list = [x for x in filename_list if os.path.exists(x)]
        if filename_list:
            launch(list(map(Gio.File.new_for_path, filename_list)), None)
    except:
        print ("Fail to launch: " + str(filename_list))

def get_default_app(file_type):
    default_app_info = Gio.app_info_get_default_for_type(file_type, False)
    if not default_app_info:
        return None, None, None, None, None
    icon_filename = get_app_icon_filename(default_app_info)
    app_name = default_app_info.get_name()
    app_tooltip = default_app_info.get_description()
    app_launch_fun = app_launch_files

    # https://developer.gnome.org/pygobject/stable/class-gioappinfo.html#method-gioappinfo--get-commandline
    cmd_line = default_app_info.get_commandline()       # mousepad %F'
    # %f %F
    # https://specifications.freedesktop.org/desktop-entry-spec/desktop-entry-spec-latest.html
    executable = default_app_info.get_executable()      # 'mousepad'

    # app_launch =  lambda filename_list: default_app_info.launch(
    #                     map(gio.File, filename_list),None)

    # app_launch_list.append(app_name)
    # cv = app_name
    # app_launch = test_print
    return icon_filename, app_name, app_tooltip, app_launch_fun, default_app_info.launch


def get_open_with_app(file_type):
    from gi.repository import Gio
    default_app_info = Gio.app_info_get_default_for_type(file_type, False)
    if not default_app_info:
        return
    app_name = default_app_info.get_name()

    app_infos = Gio.app_info_get_all_for_type(file_type)
    for app_info in app_infos:
        if app_info.get_name() != app_name:
            icon_filename = get_app_icon_filename(app_info)
            app_name = app_info.get_name()
            app_tooltip = app_info.get_description()
            app_launch_fun = app_launch_files
            yield icon_filename, app_name, app_tooltip, app_launch_fun, app_info.launch


def get_QIcon_object(filename):
    if not (filename in _qicon_cache_for_build_qicon):
        _qicon_cache_for_build_qicon[filename] = QtGui.QIcon(filename)
    return _qicon_cache_for_build_qicon[filename]


def build_qicon(filename, isPath, size=DEFAULT_ICON_SIZE):

    from gi.repository import Gio
    # print "-------------------------------------------" + str(_qicon_cache_for_build_qicon)
    if isPath:
        type_ = 'folder'
    else:
        type_, encoding = mimetypes.guess_type(filename)
        type_ = 'unknown' if not type_ else type_  # 'empty'
    icon = Gio.content_type_get_icon(type_)

    icon_filename = _get_icon_filename(icon.get_names()[0])

    return get_QIcon_object(icon_filename)


def set_qicon(qstandarditem, filename, isPath, size=32):
    qstandarditem.setIcon(build_qicon(filename, isPath, size=32))


def size_to_str(value, unit='KB'):
    if (not value) and (value != 0) and (value != '0'):
        return ''
    suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    if not unit in suffixes:
        unit = None
    try:
        value = int(value)
    except:
        print('aaa')

    if unit == 'B': return '%d B' % value
    if value == 0 and not (unit is None):
        return '0 B'
    try:
        i = 0
        while (value >= 1024 and i < len(suffixes) - 1) or not (unit is None):
            value /= 1024.
            i += 1
            if unit == suffixes[i]:    break
        f = ('%.2f' % value).rstrip('0').rstrip('.')
        return '%s %s' % (f, suffixes[i])
    except:
        print("***************************** Error in format size: ", value)

        return value

def pop_select_app_dialog_and_open(file_type,filename_list):
    python_exe = sys.executable
    py_path = os.path.dirname(os.path.abspath(__file__))
    subprocess_path = os.path.join(py_path, 'subprocess_pop_select_app_dialog.py')

    app_executable = subprocess.check_output( [python_exe, subprocess_path, file_type] ,
            stderr = subprocess.PIPE)
    if app_executable:
        for filename in filename_list:
            try:
                if os.path.exists(filename):
                    subprocess.Popen([app_executable, filename])
            except Exception as e:
                print(str(e))

if __name__ == '__main__':
    pass
    file_type = get_file_type('a.txt', False)
    print(file_type)

    print(get_default_app(file_type))

    # build_qicon('a.txt', False, size=DEFAULT_ICON_SIZE)
    # print(build_qicon('a.txt',False))

    file_type = get_file_type('a.txt', False)
    print(file_type)

    pop_select_app_dialog_and_open(file_type, ['/home/cg/Desktop/test.txt'])
