#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
VERSION = "0.1.1.0"
COPYRIGHT = '\nDawnlight Search ' + VERSION + '\n\n' + 'Copyright © 2016 ChG Hou\n'
ORGANIZATION_NAME = "Dawnlight_Search"
ALLICATION_NAME = "Dawnligh_Search"
from PyQt5.QtCore import QSettings, QCoreApplication
import os
import sqlite3

translate = QCoreApplication.translate

PATH_OF_SETTING_FILE = os.path.dirname(QSettings(QSettings.IniFormat, QSettings.UserScope, ORGANIZATION_NAME,
                                                 ALLICATION_NAME).fileName())

DATABASE_FILE_NAME = QSettings(QSettings.IniFormat, QSettings.UserScope,
                               ORGANIZATION_NAME, ALLICATION_NAME).value('Database_File_Name',
                                                                         type=str,
                                                                         defaultValue=os.path.join(PATH_OF_SETTING_FILE,
                                                                                                   'files.db'))

TEMP_DB_NAME = QSettings(QSettings.IniFormat, QSettings.UserScope,
                         ORGANIZATION_NAME, ALLICATION_NAME).value('Temp_Database_File_Name',
                                                                   type=str, defaultValue=os.path.join(
        PATH_OF_SETTING_FILE,
        'temp_db.db'))

# The QUERY_HEADER_LIST MUST be be consistent with DB_HEADER_LIST except 'Extension'.
QUERY_HEADER_LIST = ['Filename', 'Path', 'Size', 'IsFolder',
                  'atime', 'mtime', 'ctime']
DB_HEADER_LIST = ['Filename', 'Path', 'Size', 'IsFolder','Extension',
                  'atime', 'mtime', 'ctime']
QUERY_TO_DSP_MAP = [DB_HEADER_LIST.index(x) for x in QUERY_HEADER_LIST]
UUID_HEADER_LIST = ['included', 'path', 'label', 'uuid','alias', 'fstype', 'name',
                    'major_dnum', 'minor_dnum', 'rows', 'updatable']


class QUERY_HEADER():
    Filename, Path, Size, IsFolder, atime, mtime, ctime = range(len(QUERY_HEADER_LIST))
    # 0          1   2       3       4      5       6
class DB_HEADER():
    Filename, Path, Size, IsFolder, Extension, atime, mtime, ctime = range(len(DB_HEADER_LIST))
    #0          1   2       3       4           5       6       7
class UUID_HEADER():
    included, path, label, uuid, alias, fstype, name, major_dnum, minor_dnum, rows, updatable, processbar = range(len(UUID_HEADER_LIST) + 1)
    #0          1   2       3       4       5   6           7           8       9       10          11

# DB_HEADER_LABEL = ['Filename', 'Path', 'Size', 'Is Folder',
#                        'Extension', 'Access Time', 'Modify Time',
#                        'Change Time']
#
# UUID_HEADER_LABEL = ['Search', 'Mount Path', 'Label', 'UUID',
#                      'Alias', 'FS Type', 'Dev name',
#                      'Major Device Num', 'Minor Device Num', 'Items',
#                      'Update', 'Progress']

# translate is necessary for pylupdate5 detecting the string, although it has no effect before translator loaded.
DB_HEADER_LABEL= [translate('ui','Filename'), translate('ui','Path'), translate('ui','Size'), translate('ui','Is Folder'),
                  translate('ui','Extension'), translate('ui','Access Time'), translate('ui','Modify Time'),
                  translate('ui','Change Time')]
UUID_HEADER_LABEL = [translate('ui','Search'), translate('ui','Mount Path'), translate('ui','Label'), translate('ui','UUID'),
                     translate('ui','Alias'), translate('ui','FS Type'), translate('ui','Dev name'),
                    translate('ui','Major Device Num'), translate('ui','Minor Device Num'), translate('ui','Items'),
                     translate('ui','Update'),translate('ui','Progress')]

class GlobalVar(object):


    QUERY_CHUNK_SIZE = 10000
    MODEL_MAX_ITEMS = 3000
    QUERY_LIMIT = 100
    CURRENT_MODEL_ITEMS = 0

    # settings = QSettings(QSettings.IniFormat, QSettings.UserScope, ORGANIZATION_NAME, ALLICATION_NAME)
    # query_limit = settings.value('Query_limit', type=int, defaultValue=100)

    USE_MFT_PARSER = True
    USE_MFT_PARSER_CPP = True

    CASE_SENSTITIVE = False
    MATCH_OPTION = 1

    # http://doc.qt.io/qt-5/qdatetime.html#fromString-1
    DATETIME_FORMAT = 'd/M/yyyy h:m:s'
    HIGHLIGHT_WORDS = {'Name':[],'Path':[]}

    Query_Text_ID = 0

    EXCLUDED_UUID = set()

    SKIP_DIFF_DEV = False

    SIZE_UNIT = 'KB'

    INSTANT_SEARCH = True

    MOUNT_STATE_UPDATE_INTERVAL = 3000
    ROWID_UPDATE_INTERVAL = 3000
    DB_UPDATE_INTERVAL = 1000

    # GlobalVar.MOUNT_STATE_UPDATE_INTERVAL = settings.value('Mount_State_Update_Interval', type=int, defaultValue=3000)
    # GlobalVar.ROWID_UPDATE_INTERVAL = settings.value('Rowid_Update_Interval', type=int, defaultValue=3000)
    # GlobalVar.DB_UPDATE_INTERVAL = settings.value('Database_Update_Interval', type=int, defaultValue=1000)


    # constant
    PROGRESS_STEP = 1000
    DEFAULT_EXCLUDED_UUID = ['0:' + str(x) for x in range(50)]
    #flag
    QUERY_READY_FLAG = [False, ]

class MainCon(object):
    con = None
    cur = None
