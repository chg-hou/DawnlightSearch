from __future__ import absolute_import

ORGANIZATION_NAME = "Dawnlight_Search"
ALLICATION_NAME = "Dawnligh_Search"
from PyQt5.QtCore import QSettings
import os
import sqlite3
PATH_OF_SETTING_FILE = os.path.dirname(  QSettings(      QSettings.IniFormat,       QSettings.UserScope,    ORGANIZATION_NAME,
        ALLICATION_NAME).fileName())

DATABASE_FILE_NAME = QSettings(QSettings.IniFormat, QSettings.UserScope,
                               ORGANIZATION_NAME, ALLICATION_NAME).value('Database_File_Name',
                                                                         type=str, defaultValue=os.path.join(PATH_OF_SETTING_FILE,
                                                                                                  'files.db'))

TEMP_DB_NAME = QSettings(QSettings.IniFormat, QSettings.UserScope,
                               ORGANIZATION_NAME, ALLICATION_NAME).value('Temp_Database_File_Name',
                                                                         type=str, defaultValue=os.path.join(
                                                                             PATH_OF_SETTING_FILE,
                                                                             'temp_db.db'))



class GlobalVar(object):
    QUERY_CHUNK_SIZE = 10000
    MODEL_MAX_ITEMS = 3000
    QUERY_LIMIT = 100
    # settings = QSettings(QSettings.IniFormat, QSettings.UserScope, ORGANIZATION_NAME, ALLICATION_NAME)
    # query_limit = settings.value('Query_limit', type=int, defaultValue=100)

    USE_MFT_PARSER = True
    USE_MFT_PARSER_CPP = True



class MainCon(object):
    con = None
    cur = None

