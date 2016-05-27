from __future__ import absolute_import


QUERY_CHUNK_SIZE = 10000
MODEL_MAX_ITEMS = 3000

ORGANIZATION_NAME = "cgHou_soft"
ALLICATION_NAME = "Dawnlight Search"

USING_MFT_PARSER_CPP = True

from PyQt5.QtCore import QSettings

import os

# DATABASE_FILE_NAME = 'files.db'
# TEMP_DB_NAME = 'temp_db.db'

# print os.path.dirname(
#     QSettings(QSettings.IniFormat, QSettings.UserScope, ORGANIZATION_NAME, ALLICATION_NAME).fileName())

DATABASE_FILE_NAME = os.path.join(
    os.path.dirname(QSettings(QSettings.IniFormat, QSettings.UserScope, ORGANIZATION_NAME, ALLICATION_NAME).fileName()),
    'files.db')

TEMP_DB_NAME = os.path.join(
    os.path.dirname(QSettings(QSettings.IniFormat, QSettings.UserScope, ORGANIZATION_NAME, ALLICATION_NAME).fileName()),
    'temp_db.db')
