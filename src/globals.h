#ifndef GLOBALS_H
#define GLOBALS_H

#define True true
#define False false
#define HACKED_QT_EDITROLE (Qt::UserRole)
#define APP_RESTART_CODE 1106
#define APP_QUIT_CODE 1000

#include <QString>
#include <QStringList>
#include <QDebug>
#include <QSqlDatabase>
#include <QSqlError>
#include <QSqlQuery>
#include <QSettings>
#include <QDir>
#include <QObject>
#include <QCoreApplication>
#include <QRegularExpression>

#define CONST_SQL_TEXT_FORMAT_CACHE_SIZE  200
#define ICON_TEXT_SHIFT_COEFF 0.8
//extern QString VERSION ;
extern QString COPYRIGHT;
extern QString ORGANIZATION_NAME;
extern QString ALLICATION_NAME ;

extern int MOUNT_STATE_UPDATE_INTERVAL;
extern int ROWID_UPDATE_INTERVAL;
extern int DB_UPDATE_INTERVAL;
extern bool USE_MFT_PARSER_CPP;
extern bool USE_MFT_PARSER;
extern QString DATETIME_FORMAT;

extern long PROGRESS_STEP;

extern bool SKIP_DIFF_DEV;
extern QString SIZE_UNIT;
extern bool INSTANT_SEARCH;
extern QStringList HIDDEN_UUID;
extern QStringList DEFAULT_HIDDEN_UUID;
extern QRegularExpression EXCLUDED_MOUNT_PATH_RE;
extern QString DEFAULT_EXCLUDED_MOUNT_PATH_RE_STRING;

extern QString DATABASE_FILE_NAME;
extern QString PATH_OF_SETTING_FILE;
extern QString TEMP_DB_NAME;
class QUERY_HEADER_class
{
public:
    const int Filename=0;
    const int Path=1;
    const int Size=2;
    const int IsFolder=3;
    const int atime=4;
    const int mtime=5;
    const int ctime=6;

    const int len = 7;

    enum Constants
    {
        Filename_=0,
        Path_=1,
        Size_=2,
        IsFolder_=3,
        atime_=4,
        mtime_=5,
        ctime_=6,

        len_ = 7
    };

};
class DB_HEADER_class
{
public:
    const int Filename=0;
    const int Path=1;
    const int Size=2;
    const int IsFolder=3;
    const int Extension=4;
    const int atime=5;
    const int mtime=6;
    const int ctime=7;
};
class UUID_HEADER_class
{
public:
    const int  included=0;
    const int  path=1;
    const int  label=2;
    const int  uuid=3;
    const int  alias=4;
    const int  fstype=5;
    const int  name=6;
    const int  major_dnum=7;
    const int  minor_dnum=8;
    const int  rows=9;
    const int  updatable=10;
    const int  processbar=11;

    const int len=12;
};
extern QStringList UUID_HEADER_LABEL;
extern QStringList UUID_HEADER_TOOLTIP;

extern const QUERY_HEADER_class QUERY_HEADER;
extern DB_HEADER_class DB_HEADER;
extern UUID_HEADER_class UUID_HEADER;

extern QStringList UUID_HEADER_LIST ;
extern QStringList DB_HEADER_LIST ;
extern QStringList DB_HEADER_LABEL ;
extern QStringList QUERY_HEADER_LIST;

extern int Query_Text_ID;
extern long CURRENT_MODEL_ITEMS;
extern int QUERY_THREAD_NUMBER;
extern unsigned long QUERY_CHUNK_SIZE;
extern unsigned long QUERY_SQL_QUEUE_TOTAL_LENGTH;

extern unsigned int MATCH_OPTION;
extern bool CASE_SENSTITIVE;
extern unsigned long QUERY_LIMIT;
//struct QUERY_HEADER_class QUERY_HEADER;
extern QSet<QPair<bool,QString >>  HIGHLIGHT_WORDS_NAME;
extern QSet<QPair<bool,QString >>  HIGHLIGHT_WORDS_PATH;

extern  long MODEL_MAX_ITEMS;

extern bool COMPRESS_DB_FILE ;
extern bool AUTOFOCUS_SEARCH_WHEN_WIN_ACTIVATED;
extern bool DB_READ_ONLY_FLAG;

#ifdef SNAP_LSBLK_COMPATIBILITY_MODE
extern bool SNAP_LSBLK_COMPATIBILITY_MODE_FLAG;
#endif

#endif // GLOBALS_H
