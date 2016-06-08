from __future__ import absolute_import

ORGANIZATION_NAME = "Dawnlight_Search"
ALLICATION_NAME = "Dawnligh_Search"
from PyQt5.QtCore import QSettings
import os
import sqlite3

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

DB_HEADER_LIST = ['Filename', 'Path', 'Size', 'IsFolder',
                  'atime', 'mtime', 'ctime']

class GlobalVar(object):
    QUERY_CHUNK_SIZE = 10000
    MODEL_MAX_ITEMS = 3000
    QUERY_LIMIT = 100
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

    GET_ICON_PROCRESS = None
    SKIP_DIFF_DEV = False


class MainCon(object):
    con = None
    cur = None
