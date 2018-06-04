#include "MainWindow.h"
#include <QApplication>

#include <QStorageInfo>

//#include <QFileInfoList>
//#include <mntent.h>
#include "DB_Builder/partition_information.h"

#include <QDir>
#include <QString>
#include <QTranslator>
#include <QFile>
#include <QStack>



// TODO: add filter lineedit above col header

// TODO: table uuid widget: You can try to disable signal emitting before starting inserts and activate them afterwards (blockSignals). You can do that as well with the model.

int main(int argc, char *argv[])
{


    qRegisterMetaType<QList<QPair<QString,QVariant>>>("QList<QPair<QString,QVariant>>");
    qRegisterMetaType<QList<QVariantList>>("QList<QVariantList>");
    qRegisterMetaType<QList<QStringList>>("QList<QStringList>");
    qRegisterMetaType<QList<QList<QVariant>>>("QList<QList<QVariant>>");

    //qRegisterMetaTypeStreamOperators<QList<int> >("QList<int>");

    QSettings settings(QSettings::IniFormat, QSettings::UserScope,
                       ORGANIZATION_NAME, ALLICATION_NAME);

    {
        QDir settings_dir(  QFileInfo(settings.fileName()).path() );
        QDir db_dir(  QFileInfo(DATABASE_FILE_NAME).path() );
        QDir tmp_db_dir(  QFileInfo(TEMP_DB_NAME).path() );

        for(const QDir & dir: QList<QDir>({ settings_dir, db_dir ,tmp_db_dir }))
        {
            if(!dir.exists())
                dir.mkpath(".");
        }
    }


    QTranslator translator;
    QString lang = settings.value("Language/language","auto").toString();
    if (lang =="auto")
        lang = QLocale::system().name();

    QString lang_path = ":/lang/"+ lang+ ".qm";
    //                 ":/lang/zh_CN.qm"
    if (!QFile(lang_path).exists())
        qDebug()<<"lang file missing: " + lang_path;
    translator.load(lang_path);


    QApplication a(argc, argv);

    // ===========
    a.installTranslator(&translator);
    // ===========

    MainWindow w;
    w.show();

    // ===========
    w.ini_after_show();
    // ===========
    //    QIcon accc(QPixmap(":/icon/ui/icon/dev-harddisk.png"));
    //    qDebug()<< "ddddddddddddddddddd  "<< accc.isNull();

    //    try{
    int ok = a.exec();
    return ok;
    //    }
    //    catch (const std::exception &exc)
    //    {
    //        qDebug()<<"ERROR: "<<__FILE__<< __LINE__<< __FUNCTION__<<
    //                                  "\n\t Exception:"<<exc.what();
    //    }
    //    catch (...)
    //    {
    //        qDebug()<<"ERROR: "<<__FILE__<< __LINE__<< __FUNCTION__<<
    //                                  "\n\t unknown Exception:";
    //    }
    return 1;
}


// debug sql_formatter

/*
#include "QueryWorker/query_worker.h"

    QStringList sql_test_list = {" \"a\" ",
                                 " a ",
                                 "a b c",
                                 "a <b | c> d e",
                                 "a  <  b  > e",
                                 "a < <  b  > < e | d > > e",
                                 "  a b nocase: c case: d  \"cd*v\" ",
                                 "a b",
                                 "\"a\" \"b\"",
                                 " ctime:<\"23/1/2016 13:32:33\" ",
                                 " a c atime:>=\"23123423\" ",
                                 "   nocase: c   ",
                                 "  a sdf ctime:<\"1/3/1980 1:13:22\"  ",
                                 "\"cd\" ctime:>\"3423d4\"",
                                 " a folder: a  size:>=34G ",
                                 " a folder: d",
                                 " a folder: p:d",
                                 "reg:\"\\d\""
                                };
    for(  QString sqltext : sql_test_list)

    {
        Format_Sql_Result format_sql_result =
            format_sql_cmd("/devpath/", "UUID", sqltext, 1,2);
    QString sql = format_sql_result.sql_mask + " WHERE " + QString(" (ROWID BETWEEN %1 AND %2) AND").arg(1).arg(2)
                        + " (" + format_sql_result.sql_cmd + ") " + QString(" LIMIT %1").arg(10);
    qDebug().noquote()<<sqltext;
    if (format_sql_result.ok)
        qDebug().noquote()<<sql;
}
    // OUTPUT shout be:

 "a"
 SELECT Filename,"/devpath/"||Path,Size,IsFolder,atime,mtime,ctime FROM `UUID`  WHERE  (ROWID BETWEEN 1 AND 2) AND ((Filename LIKE "a" ESCAPE "\"  COLLATE  nocase ))  LIMIT 10
 a
 SELECT Filename,"/devpath/"||Path,Size,IsFolder,atime,mtime,ctime FROM `UUID`  WHERE  (ROWID BETWEEN 1 AND 2) AND ((Filename LIKE "%a%" ESCAPE "\"  COLLATE  nocase ))  LIMIT 10
a b c
 SELECT Filename,"/devpath/"||Path,Size,IsFolder,atime,mtime,ctime FROM `UUID`  WHERE  (ROWID BETWEEN 1 AND 2) AND ((Filename LIKE "%a%" ESCAPE "\"  COLLATE  nocase ) AND (Filename LIKE "%b%" ESCAPE "\"  COLLATE  nocase ) AND (Filename LIKE "%c%" ESCAPE "\"  COLLATE  nocase ))  LIMIT 10
a <b | c> d e
 SELECT Filename,"/devpath/"||Path,Size,IsFolder,atime,mtime,ctime FROM `UUID`  WHERE  (ROWID BETWEEN 1 AND 2) AND ((Filename LIKE "%a%" ESCAPE "\"  COLLATE  nocase ) AND  ( (Filename LIKE "%b%" ESCAPE "\"  COLLATE  nocase ) )  OR (Filename LIKE "%c%" ESCAPE "\"  COLLATE  nocase ) AND (Filename LIKE "%d%" ESCAPE "\"  COLLATE  nocase ) AND (Filename LIKE "%e%" ESCAPE "\"  COLLATE  nocase ))  LIMIT 10
a  <  b  > e
 SELECT Filename,"/devpath/"||Path,Size,IsFolder,atime,mtime,ctime FROM `UUID`  WHERE  (ROWID BETWEEN 1 AND 2) AND ((Filename LIKE "%a%" ESCAPE "\"  COLLATE  nocase ) AND  ( (Filename LIKE "%b%" ESCAPE "\"  COLLATE  nocase ) )  AND (Filename LIKE "%e%" ESCAPE "\"  COLLATE  nocase ))  LIMIT 10
a < <  b  > < e | d > > e
 SELECT Filename,"/devpath/"||Path,Size,IsFolder,atime,mtime,ctime FROM `UUID`  WHERE  (ROWID BETWEEN 1 AND 2) AND ((Filename LIKE "%a%" ESCAPE "\"  COLLATE  nocase ) AND  (  ( (Filename LIKE "%b%" ESCAPE "\"  COLLATE  nocase ) )  AND  ( (Filename LIKE "%e%" ESCAPE "\"  COLLATE  nocase ) OR (Filename LIKE "%d%" ESCAPE "\"  COLLATE  nocase ) )  )  AND (Filename LIKE "%e%" ESCAPE "\"  COLLATE  nocase ))  LIMIT 10
  a b nocase: c case: d  "cd*v"
 SELECT Filename,"/devpath/"||Path,Size,IsFolder,atime,mtime,ctime FROM `UUID`  WHERE  (ROWID BETWEEN 1 AND 2) AND (( UPPER(Filename) LIKE "%A%" ESCAPE "\"  COLLATE  nocase ) AND ( UPPER(Filename) LIKE "%B%" ESCAPE "\"  COLLATE  nocase ) AND ( UPPER(Filename) LIKE "%C%" ESCAPE "\"  COLLATE  nocase ) AND (Filename LIKE "%d%" ESCAPE "\" ) AND (Filename LIKE "cd%v" ESCAPE "\" ))  LIMIT 10
a b
 SELECT Filename,"/devpath/"||Path,Size,IsFolder,atime,mtime,ctime FROM `UUID`  WHERE  (ROWID BETWEEN 1 AND 2) AND ((Filename LIKE "%a%" ESCAPE "\"  COLLATE  nocase ) AND (Filename LIKE "%b%" ESCAPE "\"  COLLATE  nocase ))  LIMIT 10
"a" "b"
 SELECT Filename,"/devpath/"||Path,Size,IsFolder,atime,mtime,ctime FROM `UUID`  WHERE  (ROWID BETWEEN 1 AND 2) AND ((Filename LIKE "a" ESCAPE "\"  COLLATE  nocase ) AND (Filename LIKE "b" ESCAPE "\"  COLLATE  nocase ))  LIMIT 10
 ctime:<"23/1/2016 13:32:33"
 SELECT Filename,"/devpath/"||Path,Size,IsFolder,atime,mtime,ctime FROM `UUID`  WHERE  (ROWID BETWEEN 1 AND 2) AND ((ctime<1453527153))  LIMIT 10
 a c atime:>="23123423"
 SELECT Filename,"/devpath/"||Path,Size,IsFolder,atime,mtime,ctime FROM `UUID`  WHERE  (ROWID BETWEEN 1 AND 2) AND ((Filename LIKE "%a%" ESCAPE "\"  COLLATE  nocase ) AND (Filename LIKE "%c%" ESCAPE "\"  COLLATE  nocase ) AND (atime>=23123423))  LIMIT 10
   nocase: c
 SELECT Filename,"/devpath/"||Path,Size,IsFolder,atime,mtime,ctime FROM `UUID`  WHERE  (ROWID BETWEEN 1 AND 2) AND ((Filename LIKE "%c%" ESCAPE "\"  COLLATE  nocase ))  LIMIT 10
  a sdf ctime:<"1/3/1980 1:13:22"
 SELECT Filename,"/devpath/"||Path,Size,IsFolder,atime,mtime,ctime FROM `UUID`  WHERE  (ROWID BETWEEN 1 AND 2) AND ((Filename LIKE "%a%" ESCAPE "\"  COLLATE  nocase ) AND (Filename LIKE "%sdf%" ESCAPE "\"  COLLATE  nocase ) AND (ctime<320694202))  LIMIT 10
"cd" ctime:>"3423d4"
 a folder: a  size:>=34G
 SELECT Filename,"/devpath/"||Path,Size,IsFolder,atime,mtime,ctime FROM `UUID`  WHERE  (ROWID BETWEEN 1 AND 2) AND ((Filename LIKE "%a%" ESCAPE "\"  COLLATE  nocase ) AND ( IsFolder) AND (Filename LIKE "%a%" ESCAPE "\"  COLLATE  nocase ) AND (Size>=36507222016))  LIMIT 10
 a folder: d
 SELECT Filename,"/devpath/"||Path,Size,IsFolder,atime,mtime,ctime FROM `UUID`  WHERE  (ROWID BETWEEN 1 AND 2) AND ((Filename LIKE "%a%" ESCAPE "\"  COLLATE  nocase ) AND ( IsFolder) AND (Filename LIKE "%d%" ESCAPE "\"  COLLATE  nocase ))  LIMIT 10
 a folder: p:d
 SELECT Filename,"/devpath/"||Path,Size,IsFolder,atime,mtime,ctime FROM `UUID`  WHERE  (ROWID BETWEEN 1 AND 2) AND ((Filename LIKE "%a%" ESCAPE "\"  COLLATE  nocase ) AND ( IsFolder) AND (Path LIKE "%d%" ESCAPE "\"  COLLATE  nocase ))  LIMIT 10
reg:"\d"
 SELECT Filename,"/devpath/"||Path,Size,IsFolder,atime,mtime,ctime FROM `UUID`  WHERE  (ROWID BETWEEN 1 AND 2) AND ((Filename REGEXP "\d"  COLLATE  nocase ))  LIMIT 10
     */

