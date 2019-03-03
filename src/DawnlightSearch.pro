#-------------------------------------------------
#
# Project created by QtCreator 2018-05-21T16:25:57
#
#-------------------------------------------------

VERSION = "$$cat(VERSION)"
DEFINES += VERSION_STRING=\\\"$${VERSION}\\\"

#-------------------------------------------------
# compressed db file
#   https://www.zlibc.linux.lu/faq.html                     read-only compressed file-system emulation
#   https://en.wikipedia.org/wiki/Archivemount              read-write. too slow
#   https://www.systutorials.com/docs/linux/man/1-fuse-zip/ read-write, use ram, fast enough
#  use-zip Dawnlight_Search.zip Dawnlight_Search -d
#  fusermount -u /home/cg/.config/Dawnlight_Search
#-------------------------------------------------

CONFIG += c++11
DEFINES += SNAP_LSBLK_COMPATIBILITY_MODE

# CONFIG += no-opengl

#
QT       += core gui widgets sql

greaterThan(QT_MAJOR_VERSION, 4): QT += widgets

#TARGET = DawnlightSearch
TARGET = dawnlightsearch
TEMPLATE = app

# The following define makes your compiler emit warnings if you use
# any feature of Qt which has been marked as deprecated (the exact warnings
# depend on your compiler). Please consult the documentation of the
# deprecated API in order to know how to port your code away from it.
DEFINES += QT_DEPRECATED_WARNINGS

# You can also make your code fail to compile if you use deprecated APIs.
# In order to do so, uncomment the following line.
# You can also select to disable deprecated APIs only up to a certain version of Qt.
#DEFINES += QT_DISABLE_DEPRECATED_BEFORE=0x060000    # disables all the APIs deprecated before Qt 6.0.0


SOURCES += \
        main.cpp \
    MainWindow.cpp \
    DB_Builder/update_db_module.cpp \
    DB_Builder/partition_information.cpp \
    DB_Builder/insert_db_thread.cpp \
    globals.cpp \
    mainwindow_slots.cpp \
    mainwindow_uuid_table_slots.cpp \
    mainwindow_update_db_action.cpp \
    DB_Builder/db_commit_step_optimizer.cpp \
    mainwindow_query.cpp \
    QueryWorker/query_worker.cpp \
    QueryWorker/query_thread.cpp \
    QueryWorker/sql_formatter.cpp \
    UI_delegate/html_delegate.cpp \
    mainwindow_table_action.cpp \
    ui_change_advanced_setting_dialog.cpp \
    ui_change_excluded_folder_dialog.cpp \
    DB_Builder/mft_parser.cpp \
    Result_Item_Model/my_qstandarditemmodel.cpp

HEADERS += \
    MainWindow.h \
    globals.h \
    DB_Builder/update_db_module.h \
    DB_Builder/partition_information.h \
    DB_Builder/insert_db_thread.h \
    DB_Builder/db_commit_step_optimizer.h \
    QueryWorker/query_worker.h \
    QueryWorker/query_thread.h \
    QueryWorker/sql_formatter.h \
    UI_delegate/html_delegate.h \
    ui_change_advanced_setting_dialog.h \
    ui_change_excluded_folder_dialog.h \
    DB_Builder/mft_parser.h \
    Result_Item_Model/my_qstandarditemmodel.h

FORMS += \
        Ui_mainwindow.ui \
    Ui_advanced_setting_dialog.ui \
    Ui_edit_exclued_folder.ui

RESOURCES += \
    resource_file.qrc

STATECHARTS +=


# translation guide:
# 1. edit following output file
# 2. click Tools > External > Linguist > Update
# 3. translate .ts file in /lang
# 4. click Tools > External > Linguist > Release
TRANSLATIONS    =     \
    lang/translate_en_US.ts \
    lang/translate_zh_CN.ts

#DISTFILES += \
#RESOURCES += \
#    lang/translate_en_US.qm \
#    lang/translate_zh_CN.qm

QTPLUGIN     +=  qsqlite
# CONFIG += static

# CONFIG+=link_pkgconfig
# PKGCONFIG+=gio-2.0
# PKGCONFIG+=gtk+-3.0

# sudo apt install kio-dev
# https://stackoverflow.com/questions/42879952/starting-with-kde-frameworks-5-and-qt-creator
DEFINES += USE_KF5_LIB_FOR_OPENWITH_MENU
QT += KIOCore KIOFileWidgets KIOWidgets KNTLM

# ubuntu 16.04 cannot find the correct kio lib
LIBS += -lKF5KIOWidgets
INCLUDEPATH += /usr/include/KF5/KIOFileWidgets/
LIBS += -lKF5KIOFileWidgets
LIBS += -L/usr/lib/x86_64-linux-gnu/


lessThan(QT_VERSION, QT_VERSION_CHECK(5, 10, 0))
{
    LIBS += -lsqlite3
    DEFINES += QT_CUSTOM_SQLITE_REGEXP
    # QTBUG-18084, before Qt 5.10.0
    # libsqlite3-dev
    # #include <sqlite3.h>
    # query_thread.cpp
    # https://stackoverflow.com/questions/34415351/adding-a-custom-sqlite-function-to-a-qt-application/34415352
    # https://blog.minidump.info/2016/06/qt-sqlite-plugin-supports-regexp-select/
}

DISTFILES += \
    uml.txt \
    model_chart_close_event.qmodel \
    model_chart_update_db.qmodel \
    model_chart_update_db_copy.qmodel \
    model_chart_query.qmodel \
    model_chart_start.qmodel \
    lang/translate_en_US.qm \
    lang/translate_zh_CN.qm \
    lang/translate_en_US.ts \
    lang/translate_zh_CN.ts

# Recognized as shared library and won't run it by clicking
# Thanks revast@github for the solution
# ? no work in gcc 4.8
QMAKE_LFLAGS += -no-pie
