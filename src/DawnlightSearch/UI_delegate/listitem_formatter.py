#!/usr/bin/env python
# -*- coding: utf-8 -*-

# https://developer.gnome.org/pygobject/stable/
# http://www.pygtk.org/docs/pygobject/gio-class-reference.html
from __future__ import absolute_import
from functools import partial

from .._Global_Qt_import import *
import gtk
import mimetypes
import gio

_qicon_cache_for_build_qicon = {}
DEFAULT_ICON_SIZE = 32


def get_file_type(filename, isPath):
    if isPath:
        type_ = 'folder'
    else:
        type_, encoding = mimetypes.guess_type(filename)
        type_ = 'unknown' if not type_ else type_  # 'empty'
    return type_


def get_app_icon_filename(app_info, size=DEFAULT_ICON_SIZE):
    if not app_info:
        return None
    themed_icon = app_info.get_icon()
    if not themed_icon:
        return None
    ICON_THEME = gtk.icon_theme_get_default()
    if not themed_icon:
        return None
    icon_info = ICON_THEME.choose_icon(themed_icon.get_names(), size, 0)

    return icon_info.get_filename()

def app_launch_files(launch, filename_list):
    try:
        launch(map(gio.File, filename_list),None)
    except:
        print ("Fail to launch: "+str(filename_list))

def get_default_app(file_type):

    default_app_info = gio.app_info_get_default_for_type(file_type, False)
    if not default_app_info:
        return None, None, None, None, None
    icon_filename = get_app_icon_filename(default_app_info)
    app_name = default_app_info.get_name()
    app_tooltip = default_app_info.get_description()
    app_launch_fun = app_launch_files
    # app_launch =  lambda filename_list: default_app_info.launch(
    #                     map(gio.File, filename_list),None)

    # app_launch_list.append(app_name)
    # cv = app_name
    # app_launch = test_print
    return icon_filename, app_name, app_tooltip, app_launch_fun, default_app_info.launch

def get_open_with_app(file_type):
    default_app_info = gio.app_info_get_default_for_type(file_type, False)
    if not default_app_info:
        return
    app_name = default_app_info.get_name()

    app_infos = gio.app_info_get_all_for_type(file_type)
    for app_info in app_infos:
        if app_info.get_name() != app_name:
            icon_filename = get_app_icon_filename(app_info)
            app_name = app_info.get_name()
            app_tooltip = app_info.get_description()
            app_launch_fun = app_launch_files
            yield icon_filename, app_name, app_tooltip, app_launch_fun, app_info.launch

def get_default_app_old(filename, isPath):
    file_type = get_file_type(filename, isPath)
    # http://www.pygtk.org/docs/pygobject/class-gioappinfo.html
    default_app_info = gio.app_info_get_default_for_type(file_type, False)
    app_infos = gio.app_info_get_all_for_type(file_type)

    # print "default_app_info: ", default_app_info.get_display_name(), default_app_info.get_filename()
    print "default_app_info: ", default_app_info.get_commandline()
    print default_app_info.get_description()
    print default_app_info.get_executable()
    print default_app_info.get_icon()
    print default_app_info.get_name()
    # menu_item.connect('activate', lambda *args: do_launch_app(app_info))

    # Open file
    # gfile = gio.File.new_for_path(filename)
    # default_app_info.launch([gfile, ], None)

    for i in app_infos:
        print "app_infos: ", i.get_name()
        print "\t\t", get_app_icon_filename(i)
    print "file_type:", file_type

def get_QIcon_object(filename):
    if not (filename in _qicon_cache_for_build_qicon):
        _qicon_cache_for_build_qicon[filename] = QtGui.QIcon(filename)
    return _qicon_cache_for_build_qicon[filename]

def build_qicon(filename, isPath, size=32):
    # print "-------------------------------------------" + str(_qicon_cache_for_build_qicon)
    if isPath:
        type_ = 'folder'
    else:
        type_, encoding = mimetypes.guess_type(filename)
        type_ = 'unknown' if not type_ else type_  # 'empty'
    icon = gio.content_type_get_icon(type_)
    ICON_THEME = gtk.icon_theme_get_default()
    info = ICON_THEME.choose_icon(icon.get_names(), size, 0)
    if not info:
        type_ = 'unknown'
        icon = gio.content_type_get_icon(type_)
        info = ICON_THEME.choose_icon(icon.get_names(), size, 0)

    return get_QIcon_object(info.get_filename())


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
        print 'aaa'

    if unit is 'B': return '%d B' % value
    if value == 0 and not (unit is None):
        return '0 B'
    try:
        i = 0
        while (value >= 1024 and i < len(suffixes) - 1) or not (unit is None):
            value /= 1024.
            i += 1
            if unit is suffixes[i]:    break
        f = ('%.2f' % value).rstrip('0').rstrip('.')
        return '%s %s' % (f, suffixes[i])
    except:
        print "***************************** Error in format size: ", value

        return value

# def pop_select_app_dialog():
#
#     from gi.repository import Gtk
#
#     file_type = "image/jpeg"
#     print file_type
#     dialog = Gtk.AppChooserDialog.new_for_content_type(None,
#                                                        Gtk.DialogFlags.MODAL, file_type)
#     response = dialog.run()
#     app_info = dialog.get_app_info()
#     dialog.destroy()
