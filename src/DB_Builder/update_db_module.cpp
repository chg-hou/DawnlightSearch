#include "update_db_module.h"
#include <QDataStream>

#define PRINT_SQL_ERROR(OK) if (!OK) { qDebug()<<"SQL ERROR: "<<__FILE__<< __LINE__<< __FUNCTION__<<"\n\twhen: "<<cur.lastQuery()<<"\n\t"<<cur.lastError();(emit show_statusbar_warning_msg_SIGNAL(cur.lastError().text())); }


bool zip(QString filename , QString zip_filename)
{
    // http://www.antonioborondo.com/2014/10/22/zipping-and-unzipping-files-with-qt/
    QFile infile(filename);
    QFile outfile(zip_filename);
    bool ok1 = infile.open(QIODevice::ReadOnly);
    bool ok2 = outfile.open(QIODevice::WriteOnly);
    if (ok1 && ok2)
    {
        QDataStream  out(&outfile);
        while(!infile.atEnd())
        {
            QByteArray uncompressed_data = infile.read(1048576*5); // 5MB
            // TODO : adjust zip ratio
            QByteArray compressed_data = qCompress(uncompressed_data,1);
            out<<compressed_data;
        }
    }
    infile.close();
    outfile.close();
    return ok1 && ok2  ;
}

bool unZip(QString zip_filename , QString filename)
{QFile infile(zip_filename);
    QFile outfile(filename);
    bool ok1 = infile.open(QIODevice::ReadOnly);
    bool ok2 = outfile.open(QIODevice::WriteOnly);
    if (ok1 && ok2)
    {
        QDataStream  instream(&infile);
        while(!instream.atEnd())
        {
            QByteArray compressed_data;
            instream >> compressed_data;
            QByteArray uncompressed_data = qUncompress(compressed_data);
            outfile.write(uncompressed_data);
        }
    }
    infile.close();
    outfile.close();
    return ok1 && ok2;
}
bool fileExists(QString path) {
    QFileInfo check_file(path);
    // check if file exists and if yes: Is it really a file and no directory?
    if (check_file.exists() && check_file.isFile()) {
        return true;
    } else {
        return false;
    }
}


//====================================================================================================================
//====================================================================================================================

Update_DB_Object::Update_DB_Object(QObject *parent)
    :QObject(parent)
{
    refresh_mount_state_timer = new QTimer(this);
    refresh_rowid_timer = new QTimer(this);
}

void Update_DB_Object::init_slot()
{
    QString compressed_db_file = DATABASE_FILE_NAME +".zip";
    if (COMPRESS_DB_FILE && ! fileExists(DATABASE_FILE_NAME)
            &&  fileExists(compressed_db_file)  )
    {
        qDebug()<<" Uncompressing db file...";
        unZip(compressed_db_file, DATABASE_FILE_NAME);
        qDebug()<< "Uncompression Done.";
    }
    //QThread::sleep(15);


    database =  QSqlDatabase::addDatabase("QSQLITE", "Main DB Connection");
    //database.addDatabase("QSQLITE", "Main DB Connection");
    database.setDatabaseName(DATABASE_FILE_NAME);

    //    database.setUserName("1");
    //    database.setPassword("2");
    //TODO : check open ok
    bool ok =  database.open();
    if (!ok)
        qDebug()<< ("Fail to open db: "  +DATABASE_FILE_NAME);
    else
        qDebug()<<( "Open db OK: "  +DATABASE_FILE_NAME);

    db_lockfile = new QLockFile(DATABASE_FILE_NAME+".lock");

    if (!db_lockfile->tryLock())
    {
        DB_READ_ONLY_FLAG = true;
        qint64 pid; QString hostname; QString appname;
        db_lockfile->getLockInfo(&pid, &hostname, &appname);
        QString warning_string;
        warning_string =  QString("DB locked by") + "appname:" + appname +" PID:" + QString::number(pid)+
                " hostname:" + hostname;
        qDebug()<< warning_string;
        emit show_statusbar_warning_msg_SIGNAL(warning_string);
    }

    cur = QSqlQuery(database);


    // http://doc.qt.io/archives/qt-4.8/qsqlquery.html#setForwardOnly
    //Forward only mode can be (depending on the driver) more
    // memory efficient since results do not need to be cached.
    // It will also improve performance on some databases.
    cur.setForwardOnly(true);
    qDebug()<<"Update_DB_Object created";


    //refresh_mount_state_timer = new QTimer(this);
    refresh_mount_state_timer->setSingleShot(false);
    refresh_mount_state_timer->setInterval(MOUNT_STATE_UPDATE_INTERVAL);
    // TODO: set timer schedule

    connect(refresh_mount_state_timer, SIGNAL(timeout()),
            this,SLOT(refresh_mount_state_timer_slot()));

    //refresh_rowid_timer = new QTimer(this);
    refresh_rowid_timer->setSingleShot(false);
    refresh_rowid_timer->setInterval(ROWID_UPDATE_INTERVAL);

    connect(refresh_rowid_timer, SIGNAL(timeout()),
            this,SLOT(refresh_rowid_timer_slot()));

    insert_db_thread = new Insert_db_Thread(this);
    insert_db_thread->start();
    connect(insert_db_thread, SIGNAL(tmp_db_ready_to_merge_SIGNAL()),
            this, SLOT(merge_db_slot()));
    // connect signal-slot back to mainWindow

    emit init_ready_connect_mainWindow_SIGNAL();

}
void Update_DB_Object::init_start_timer_slot()
{
    _init_db();
    update_table_uuid_from_db();


    refresh_mount_state_timer_slot();

    // FIXME
    refresh_mount_state_timer->start();
    refresh_rowid_timer->start();

    qDebug()<<"Update_DB_Object init done.";
}
void Update_DB_Object::quit_slot()
{

    qDebug()<<"db module quit_slot: ---";
    refresh_mount_state_timer->stop();
    refresh_rowid_timer->stop();


    delete insert_db_thread;

    database.close();
    qDebug()<<"db module quit_slot: database.close()";

    QString compressed_db_file = DATABASE_FILE_NAME +".zip";
    if ( COMPRESS_DB_FILE )
    {
        qDebug()<<" Compressing db file...";
        if (zip( DATABASE_FILE_NAME, compressed_db_file)
                && fileExists(compressed_db_file) )
            QFile::remove(DATABASE_FILE_NAME);
        else
            qDebug()<<"Compression ERROR: "<<__FILE__<< __LINE__<< __FUNCTION__<<"\n\t"<<"Something wrong.";
        qDebug()<< "Compression Done.";
    }
    if (! DB_READ_ONLY_FLAG)
        db_lockfile->unlock();

}


Update_DB_Object::~Update_DB_Object()
{
    delete refresh_mount_state_timer;
    delete refresh_rowid_timer;
    delete db_lockfile;
    //    refresh_mount_state_timer->stop();
    //    refresh_rowid_timer->stop();

    //    delete refresh_mount_state_timer;
    //    delete refresh_rowid_timer;


    //    delete insert_db_thread;

    //    qDebug()<<"database.close()";
    //    database.close();

}
// TODO: commit

void Update_DB_Object::refresh_mount_state_timer_slot(){
    if (refresh_mount_state_timer->interval()!=MOUNT_STATE_UPDATE_INTERVAL)
        refresh_mount_state_timer->setInterval(MOUNT_STATE_UPDATE_INTERVAL);
    if (update_uuid())//(Partition_Information::refresh_state())
    {
        emit update_mount_state_SIGNAL();
        qDebug()<<"emit update_mount_state_SIGNAL();";
    }
    //qDebug()<<"Same. not emit update_mount_state_SIGNAL();";
}
void Update_DB_Object::update_table_uuid_from_db(){
    QMutexLocker locker(&mutex);

    ok = cur.exec("select  " + UUID_HEADER_LIST.join(",") + " from `UUID` ");

    PRINT_SQL_ERROR(ok);

    QList<QVariantList> rst;
    while(cur.next())
    {
        QVariantList tmp;
        for(int i=0; i < UUID_HEADER_LIST.length(); i++)
        {
            tmp<<cur.value(i);
        }

        rst<<tmp;
    }
    //qDebug()<< __FILE__<< __LINE__<< __FUNCTION__ << "\n\t"<<rst;
    emit update_table_uuid_from_db_SIGNAL(rst);
}
void Update_DB_Object::refresh_rowid_timer_slot(){
    if (refresh_rowid_timer->interval()!=ROWID_UPDATE_INTERVAL)
        refresh_rowid_timer->setInterval(ROWID_UPDATE_INTERVAL);
    qint64 db_mtime =  QFileInfo(TEMP_DB_NAME).lastModified().toMSecsSinceEpoch();

    if (rowid_timestamp == db_mtime)
        return;
    rowid_timestamp = db_mtime;


    QMutexLocker locker(&mutex);
    QStringList  uuid_in_db;
    ok = cur.exec("SELECT uuid FROM `UUID` ;");
    PRINT_SQL_ERROR(ok);

    while(cur.next())
    {
        uuid_in_db<<cur.value(0).toString();
    }
    QList<QPair<QString,QVariant>> result;
    foreach (const QString& uuid, uuid_in_db) {
        ok =  cur.exec(QString("SELECT COALESCE(MAX(rowid),0) FROM `%1`  ; ").arg(uuid));
        PRINT_SQL_ERROR(ok);

        cur.next();
        result << QPair<QString,QVariant>(uuid,  cur.value(0)  );
    }

    emit update_rowid_SIGNAL(result);

    //
    //    QStringList header_lsit  = UUID_HEADER_LIST;
    //    cur.exec( "select  " + header_lsit.join(",") + "   from `UUID`  ");

    //    QList<QVariantList> rst;
    //    while(cur.next())
    //    {
    //        QVariantList tmp;
    //        for(int i=0; i < header_lsit.length();i++)
    //            tmp<< cur.value(i);
    //        rst << tmp;
    //    }
    //    emit get_table_uuid_sendback_SIGNAL(rst);




}
void Update_DB_Object::update_db_timer_slot(){
    //  FIXME: test block

    qDebug()<<"update_db_timer_slot";
    qDebug()<<"block start";
//    QThread:: sleep(5);
    qDebug()<<"block end";
}
void Update_DB_Object::update_db_slot(QList<QStringList> path_lists){

    //    update_path_queue.clear();
    //    sql_insert_queue.clear();

    //    foreach (QString _item, path_lists) {
    //        update_path_queue.enqueue(_item);
    //    }
    ////    if (this->isRunning())
    ////        this->start();
    //    restart_flag = true;

    // QStringList({path, uuid})

    QList<QStringList> update_path_list;
    for(const QStringList& path_uuid: path_lists)
    {
        if (QDir(path_uuid[0]).exists())
            update_path_list<< QStringList({path_uuid[0],path_uuid[1] });
        else
        {
            qDebug()<<"Path not exists: "<<__FILE__<< __LINE__<< __FUNCTION__<<"\n\t"<<path_uuid;
        }
    }
    qDebug()<<"update_db_slot: "<<__FILE__<< __LINE__<< __FUNCTION__<<"\n\t"<<update_path_list;

    // call directly without signal-slot
    insert_db_thread->set_scan_queue_and_restart_run(update_path_list);
}
void Update_DB_Object::save_uuid_flag_slot(QList<QVariantList > uuid_list,
                                           bool quit_flag){

    if (quit_flag)
        this->quit_flag = true;
    QMutexLocker locker(&mutex);

    //qDebug()<<"db module: save_uuid_flag_slot()";
    //qDebug()<<"\tUPDATE  UUID SET included=?, updatable=?, alias=? WHERE uuid=? ";
    //qDebug()<<"\t"<<uuid_list;

    if ( DB_READ_ONLY_FLAG)
        return;

    foreach (const QVariantList & row, uuid_list) {
        // uuid<<included<<updatable<<alias
        QVariant uuid = row[0];
        QVariant included = row[1];
        QVariant updatable = row[2];
        QVariant alias = row[3];

        cur.prepare("UPDATE  UUID SET included=?, updatable=?, alias=? "
                    "  WHERE uuid=? ");
        //qDebug()<<" uuid<<included<<updatable<<alias"<<uuid<<included<<updatable<<alias;
        cur.bindValue(0,included);
        cur.bindValue(1,updatable);
        cur.bindValue(2,alias);
        cur.bindValue(3,uuid);
        ok = cur.exec();
        PRINT_SQL_ERROR(ok);

    }

    //    if (quit_flag)
    //        this->quit();


}
void Update_DB_Object::merge_db_slot(){

    qDebug()<< __FILE__<< __LINE__<< __FUNCTION__ << "\n\t mergeing db";

    // Merge temp db into main db
    QMutexLocker locker(&mutex);

    ok = cur.exec(QString(" ATTACH \"%1\" AS SecondaryDB;")
                  .arg(TEMP_DB_NAME));

    PRINT_SQL_ERROR(ok);

    ok = cur.exec(QString(" SELECT name FROM SecondaryDB.sqlite_master WHERE type='table' ; "));

    PRINT_SQL_ERROR(ok);

    QStringList table_lsit;
    while(cur.next())
    {
        table_lsit << cur.value(0).toString();
    }
    foreach (const QString & table, table_lsit) {

        emit update_progress_SIGNAL(-2,-2, table); // Merging...

        // Creating index first is slow :  https://stackoverflow.com/questions/1711631/improve-insert-per-second-performance-of-sqlite
        // we will drop it before merging and creat a new one after merging.
        ok = cur.exec(QString(" DROP INDEX `%1` ;")
                      .arg(table+"_idx"));
        PRINT_SQL_ERROR(ok);

        ok = cur.exec(QString(" DELETE FROM `%1` ;")
                      .arg(table));
        PRINT_SQL_ERROR(ok);

        ok = cur.exec(QString(" INSERT OR REPLACE INTO \"%1\" SELECT * FROM %2   ;")
                      .arg(table).arg(
                          QString(" SecondaryDB.\"%1\" ").arg(table)
                          ));
        PRINT_SQL_ERROR(ok);

        // TODO: calculate time cosuming. Will index help?
        ok = cur.exec(QString("CREATE INDEX `%1` ON `%2` (Filename, Size, atime, mtime, ctime) ").arg(table+"_idx").arg(table));
        PRINT_SQL_ERROR(ok);

        emit update_progress_SIGNAL(-3,-3, table); // Done

    }
    ok = cur.exec(" DETACH DATABASE SecondaryDB ");
    PRINT_SQL_ERROR(ok);
    // TODO: handle fails

    QFile::remove(TEMP_DB_NAME);

}
void Update_DB_Object::get_table_uuid_slot(){

    QMutexLocker locker(&mutex);

    QStringList header_lsit  = UUID_HEADER_LIST;

    ok = cur.exec( "select  " + header_lsit.join(",") + "   from `UUID`  ");
    PRINT_SQL_ERROR(ok);

    QList<QVariantList> rst;
    while(cur.next())
    {
        QVariantList tmp;
        for(int i=0; i < header_lsit.length();i++)
            tmp<< cur.value(i);
        rst << tmp;
    }
    emit get_table_uuid_sendback_SIGNAL(rst);

}

void Update_DB_Object::_init_db(){

    if ( DB_READ_ONLY_FLAG)
        return;

    QMutexLocker locker(&mutex);

    ok = cur.exec("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='UUID';");
    PRINT_SQL_ERROR(ok);
    cur.next();
    if ( cur.value(0).toInt() ==0 )
    {
        ok = cur.exec("CREATE TABLE \"UUID\" ("
                      "`included`  BLOB,"
                      "`id`	INTEGER NOT NULL PRIMARY KEY  ,"
                      "`uuid`	TEXT NOT NULL UNIQUE,"
                      "`alias` TEXT,"
                      "`fstype`	TEXT,"
                      "`name`	TEXT,"
                      "`label`	TEXT,"
                      "`major_dnum`	INTEGER,"
                      "`minor_dnum`	INTEGER,"
                      "`path`      TEXT,"
                      "`rows` INTEGER DEFAULT 0,"
                      "`updatable` BLOB DEFAULT 0"
                      ")");
        PRINT_SQL_ERROR(ok);
    }
}

bool Update_DB_Object::update_uuid(){

    if (! Partition_Information::refresh_state())
        return false;

    if ( DB_READ_ONLY_FLAG)
        return true;

    mutex.lock();

    QStringList uuids;
    ok = cur.exec(QString("SELECT uuid FROM `UUID` ;"));
    PRINT_SQL_ERROR(ok);
    while(cur.next())
    {
        uuids.append(cur.value(0).toString());
    }
    qDebug()<<"update_uuid: table contains: "<<uuids;
    foreach (const Mnt_Info_Struct & dev, Partition_Information::mnt_info) {
        if (dev.uuid =="")
        {
            qDebug()<<" Warning: Empty uuid "<<dev.fstype<<dev.maj<<dev.min;
            continue;
        }
        if (uuids.contains(dev.uuid))
        {
            cur.prepare("UPDATE  UUID SET fstype=?,name=?,label=?,major_dnum=?,minor_dnum=?,path=? "
                        " WHERE uuid=?");
            cur.bindValue(0,dev.fstype);
            cur.bindValue(1,dev.name);
            cur.bindValue(2,dev.label);
            cur.bindValue(3,dev.maj);
            cur.bindValue(4,dev.min);
            cur.bindValue(5,dev.path);
            cur.bindValue(6,dev.uuid);
            ok = cur.exec();
            qDebug()<<"SQL UPDATE UUID "<< dev.uuid<<dev.maj<<dev.min;
            PRINT_SQL_ERROR(ok);
        }
        else{
            cur.prepare("INSERT INTO UUID (included, uuid, alias, fstype,name,label,major_dnum,minor_dnum, path) "
                        "  VALUES (?, ?,   ?,  ?,   ?,    ?,    ?,   ?, ?)");
            cur.bindValue(0,false);
            cur.bindValue(1,dev.uuid);
            cur.bindValue(2,dev.path);
            cur.bindValue(3,dev.fstype);
            cur.bindValue(4,dev.name);
            cur.bindValue(5,dev.label);
            cur.bindValue(6,dev.maj);
            cur.bindValue(7,dev.min);
            cur.bindValue(8,dev.path);
            ok = cur.exec();
            PRINT_SQL_ERROR(ok);
            qDebug()<<"SQL INSERT INTO UUID "<< dev.uuid<<dev.maj<<dev.min;
            uuids << dev.uuid;
        }
    }
    mutex.unlock();

    foreach (QString uuid,uuids) {
        qDebug()<<"init_table "<<uuid;
        init_table(uuid,false);
    }
    qDebug()<<"init_table END";
    return true;
}
void Update_DB_Object::init_table(QString table_name, bool clear_table){

    if ( DB_READ_ONLY_FLAG)
        return;

    QMutexLocker locker(&mutex);
    quint64 maxrowid=0;
    ok = cur.exec(QString(" SELECT count(*) FROM sqlite_master WHERE type='table' AND name='%1';").arg(table_name));
    PRINT_SQL_ERROR(ok);
    cur.next();
    if ( cur.value(0).toInt() ==0 )
    {
        ok = cur.exec(QString("CREATE TABLE \"%1\" ( "
                              "   `file_id` INTEGER, "
                              " `Filename`	TEXT, "
                              " `Path`	TEXT, "
                              " `Size`	INTEGER, "
                              " `IsFolder`	BLOB, "
                              " `atime`	INTEGER, "
                              " `mtime`	INTEGER, "
                              " `ctime`	INTEGER, "
                              " PRIMARY KEY(`file_id`)) ").arg(table_name));
        PRINT_SQL_ERROR(ok);

        // Creating index first is slow :  https://stackoverflow.com/questions/1711631/improve-insert-per-second-performance-of-sqlite
        // we will drop it before merging and creat a new one after merging.
        ok = cur.exec(QString("CREATE INDEX `%1` ON `%2` (Filename, Size, atime, mtime, ctime) ").arg(table_name+"_idx").arg(table_name));
        PRINT_SQL_ERROR(ok);
    }
    else if (clear_table) {
        ok = cur.exec(QString("DELETE FROM `%1`").arg(table_name));
        PRINT_SQL_ERROR(ok);
        ok = cur.exec(QString("VACUUM `%1`").arg(table_name));
        PRINT_SQL_ERROR(ok);
    }
    else
    {
        ok = cur.exec(QString("SELECT COALESCE(MAX(rowid),0) FROM `%1` ").arg(table_name));
        PRINT_SQL_ERROR(ok);
        ok = cur.next();
        maxrowid = cur.value(0).toLongLong();
    }
    cur.prepare("UPDATE  UUID SET rows=? WHERE uuid=?");
    cur.bindValue(0,maxrowid);
    cur.bindValue(1,table_name);
    ok = cur.exec();
    PRINT_SQL_ERROR(ok);
}

