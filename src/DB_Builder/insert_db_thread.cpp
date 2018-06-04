#include "insert_db_thread.h"


#define CHECK_ABORT_THEN_CLOSE_DB_AND_RETURN if (abort) {database.close();QFile::remove(TEMP_DB_NAME); return;}
#define PRINT_SQL_ERROR(OK) if (!OK) { qDebug()<<"SQL ERROR: "<<__FILE__<< __LINE__<< __FUNCTION__<<"\n\twhen: "<<cur.lastQuery()<<"\n\t"<<cur.lastError(); }
#define PRINT_DB_ERROR(OK) if (!OK) { qDebug()<<"DB ERROR: "<<__FILE__<< __LINE__<< __FUNCTION__<<"\n\t"<<database.lastError(); }

Insert_db_Thread::Insert_db_Thread(QObject *parent) : QThread(parent)
{
    restart = false;
    abort = false;
}

inline void Insert_db_Thread::read_to_stat_buf(QString filename){
    std::string str = filename.toStdString();
    const char* p = str.c_str();
    /* Get file attributes about FILE and put them in BUF.
       If FILE is a symbolic link, do not follow it.  */
    lstat(p, &stat_buf);
}
inline __dev_t Insert_db_Thread::dev_id_of_path(QString filename){
    read_to_stat_buf(filename);
    return stat_buf.st_dev;
    //qDebug()<<stat_buf.st_dev<<major(stat_buf.st_dev)<<minor(stat_buf.st_dev);
}


long Insert_db_Thread::estimate_num_of_files(QString rootpath){
    // https://linux.die.net/man/2/statvfs
    std::string str = rootpath.toStdString();
    const char* p = str.c_str();
    struct statvfs statvfs_buf;
    statvfs(p, &statvfs_buf);
    return statvfs_buf.f_files-statvfs_buf.f_ffree;

    // TODO: windows
}


Insert_db_Thread::~Insert_db_Thread()
{
    mutex.lock();
    abort = true;
    condition.wakeOne();
    mutex.unlock();
    wait();
}
void Insert_db_Thread::run(){

    forever {

        if (restart)
            emit update_progress_SIGNAL(-4,-4,"");

        mutex.lock();
        if (!restart)
            condition.wait(&mutex);
        restart = false;
        mutex.unlock();

        if(abort)
            return;

        if (update_path_queue.isEmpty())
        {
            // empty, used to restart the loop
            continue;
        }


        QFile::remove(TEMP_DB_NAME);
//        qDebug()<< __FILE__<< __LINE__<< __FUNCTION__ << "\n\t"<<"addDatabase";
        if (database.contains("Temp DB Connection"))
            database.removeDatabase("Temp DB Connection");

        database = QSqlDatabase::addDatabase("QSQLITE", "Temp DB Connection");

//        qDebug()<< __FILE__<< __LINE__<< __FUNCTION__ << "\n\t"<<"setDatabaseName";

        database.setDatabaseName(TEMP_DB_NAME);
//        qDebug()<< __FILE__<< __LINE__<< __FUNCTION__ << "\n\t"<<"OPEN";

        if (! (database.open()))
        {
            qDebug()<< ("Fail to open db: "  +TEMP_DB_NAME);
            continue;
        }
        else
            qDebug()<<( "Open db OK: "  +TEMP_DB_NAME);

        QSqlQuery cur(database);

        // ================================improve insert performance============================
        // http://doc.qt.io/archives/qt-4.8/qsqlquery.html#setForwardOnly
        //Forward only mode can be (depending on the driver) more
        // memory efficient since results do not need to be cached.
        // It will also improve performance on some databases.
        cur.setForwardOnly(true);

        if (database.driverName()== "QSQLITE" )
        {
            //https://stackoverflow.com/questions/1711631/improve-insert-per-second-performance-of-sqlite
            // PRAGMA synchronous = OFF;   53,000 inserts 1/s --> 72,000 inserts 1/s--> 79,000 inserts 1/s
            cur.exec("PRAGMA synchronous = OFF;");
            cur.exec("PRAGMA journal_mode = MEMORY;");
            /* ??? Playing with page sizes makes a difference as well (PRAGMA page_size).
             *  Having larger page sizes can make reads and writes go a bit faster as
             * larger pages are held in memory. Note that more memory will be used for
             *  your database.*/
        }

        if ((transaction_supported_flag=database.transaction()))
            qDebug()<< __FILE__<< __LINE__<< __FUNCTION__ << "\n\t"<<"transaction ENABLED";
        else
            qDebug()<< __FILE__<< __LINE__<< __FUNCTION__ << "\n\t"<<"transaction not supported";


        //===================================================================================

        QSettings settings(QSettings::IniFormat,QSettings::UserScope,
                           ORGANIZATION_NAME,ALLICATION_NAME);

        // skip diff dev
        SKIP_DIFF_DEV = settings.value("Database/Skip_Different_Device",
                                       true).toBool();

        QSet<QString> excluded_folders;
        for (QString i_path: settings.value("Excluded_folders",{}).toStringList())
        {
            if (i_path.length()>1 && i_path.endsWith("/"))
                i_path.chop(1);
            excluded_folders.insert(i_path);
        }

        while(!update_path_queue.empty())
        {
            QStringList _item = update_path_queue.takeFirst();
            QString root_path = _item[0];
            QString uuid = _item[1];

            __dev_t root_device_id = dev_id_of_path(root_path);
            QString fstype = Partition_Information::uuid_to_fstype(uuid);
            QString table_name = uuid;


            // init tmp table
            ok = cur.exec(QString("CREATE TABLE \"%1\" (`file_id` INTEGER,`Filename` TEXT, "
                             "`Path`	TEXT,     `Size`	INTEGER, `IsFolder`	BLOB, "
                             "`atime`	INTEGER,  `mtime`	INTEGER, `ctime`	INTEGER, "
                             "PRIMARY KEY(`file_id`) )").arg(table_name));

            PRINT_SQL_ERROR(ok);

            cur.prepare(QString("insert into `%1` (`Filename`,`Path`,`Size`,`IsFolder`, "
                          "   `atime`,`mtime`,`ctime`) "
                          "values (?,  ?,  ?, ?, ?, ?, ?)").arg(table_name));


            emit update_progress_SIGNAL(-1,-1,uuid);
            unsigned long num_records = 0;

            if (false && fstype == "ntfs" && USE_MFT_PARSER)
            {
                // TODO : mft parser
            }else{



                DB_Commit_Step_Optimizer commit_step_optimizer;

                unsigned long estimated_num_of_files = estimate_num_of_files(root_path);
                long progress_step = std::max(estimated_num_of_files / PROGRESS_STEP, 1ul);

                QQueue<QString> dir_queue;
                dir_queue.enqueue(root_path);
                while (!dir_queue.isEmpty())
                {
                    CHECK_ABORT_THEN_CLOSE_DB_AND_RETURN

                    if (restart)
                    {emit update_progress_SIGNAL(-2, -2, uuid);break;}

                    emit update_progress_SIGNAL(num_records, estimated_num_of_files, uuid);

                    QString current_dir = dir_queue.takeFirst();

                    //FIXME: TODO: set the correct path without mounted-dir
                    cur.bindValue(1, current_dir);

                    foreach (const QString& name, QDir(current_dir).entryList(QDir::AllEntries|QDir::NoDotAndDotDot)) {



                        CHECK_ABORT_THEN_CLOSE_DB_AND_RETURN

                        if (restart)
                        {emit update_progress_SIGNAL(-2, -2, uuid);break;}

                        QString fullpath ( current_dir + QDir::separator()+name);
                        fullpath.replace("//","/");
                        read_to_stat_buf(fullpath);

                        if (SKIP_DIFF_DEV && root_device_id!=stat_buf.st_dev)
                        {
                            qDebug()<<"Skip. In different device: "<<current_dir<<fullpath;
                            continue;
                        }

                        ++num_records;

                        if (S_ISDIR(stat_buf.st_mode))
                        {
                            // TODO: check whether it ends with /
                            if(excluded_folders.contains(fullpath))
                            {
                                qDebug()<<"Dir skipped:"<< fullpath;
//                                continue;  // use continue to skip folder also
                            }
                            else if (!S_ISLNK(stat_buf.st_mode))
                                dir_queue.enqueue(fullpath);

                            //cur.bindValue(0, name);
                            //cur.bindValue(1, current_dir);
                            cur.bindValue(2, QVariant(QVariant::LongLong));
                            cur.bindValue(3, true);
                            //cur.bindValue(4, stat_buf.st_atim.tv_sec);
                            //cur.bindValue(5, stat_buf.st_mtim.tv_sec);
                            //cur.bindValue(6, stat_buf.st_ctim.tv_sec);
                        }
                        else if (S_ISREG(stat_buf.st_mode))
                        {
                            //cur.bindValue(0, name);
                            //cur.bindValue(1, current_dir);
                            cur.bindValue(2, (long long)stat_buf.st_size);
                            cur.bindValue(3, false);
                            //cur.bindValue(4, stat_buf.st_atim.tv_sec);
                            //cur.bindValue(5, stat_buf.st_mtim.tv_sec);
                            //cur.bindValue(6, stat_buf.st_ctim.tv_sec);
                        }
                        else if (S_ISSOCK(stat_buf.st_mode))
                        {
                            // TODO
                        }else if (S_ISFIFO(stat_buf.st_mode))
                        {

                        }
                        else
                        {

                        }
                        cur.bindValue(0, name);
                        //cur.bindValue(1, current_dir);
                        //cur.bindValue(2, QVariant(QVariant::LongLong));
                        //cur.bindValue(3, true);
                        cur.bindValue(4, (long long) stat_buf.st_atim.tv_sec);
                        cur.bindValue(5, (long long) stat_buf.st_mtim.tv_sec);
                        cur.bindValue(6, (long long) stat_buf.st_ctim.tv_sec);

                        ok = cur.exec();
                        PRINT_SQL_ERROR(ok);

                        if (
                                ( estimated_num_of_files>0 &&
                                  (num_records % progress_step )==0 )
                                )
                            emit update_progress_SIGNAL(num_records, estimated_num_of_files, uuid);

                    } // one dir done

                    if (transaction_supported_flag)
                    {
                        if( commit_step_optimizer.ready_to_commit(num_records))
                        {
                            commit_step_optimizer.timer_start();

                            ok = database.commit();
                            PRINT_DB_ERROR(ok);

                            // TODO: really need this?
                            // Can we start just once at the beginning?
                            ok = database.transaction();
                            PRINT_DB_ERROR(ok);

                            commit_step_optimizer.optimize_step();

                        }

                    }



                }
            }// one path ended
            //emit 100%
            emit update_progress_SIGNAL(num_records ,num_records,uuid);

            CHECK_ABORT_THEN_CLOSE_DB_AND_RETURN

            if (restart)
                break;
//            _item
//            root_path =

        }// path queue ended

        CHECK_ABORT_THEN_CLOSE_DB_AND_RETURN
        database.commit();
        database.close();

        if (!restart)
        {

             // emit finished signal
            emit tmp_db_ready_to_merge_SIGNAL();
        }
        else
        {
            QFile::remove(TEMP_DB_NAME);
        }



    }

}

void Insert_db_Thread::set_scan_queue_and_restart_run(QList<QStringList> path_lists)
{
    // call directly without signal-slot, due to that
    /*
     *
     *  QThread instance lives in the old thread that instantiated it,
     *  not in the new thread that calls run(). This means that all of
     *  QThread's queued slots will execute in the old thread. Thus, a
     *  developer who wishes to invoke slots in the new thread must use
     *  the worker-object approach; new slots should not be implemented
     *  directly into a subclassed QThread.
     *
     * */
    QMutexLocker locker(&mutex);

    update_path_queue.clear();

    qDebug()<< __FILE__<< __LINE__<< __FUNCTION__ << "\n\tpath_lists"<<path_lists;

    foreach (QStringList _item, path_lists) {
        update_path_queue.enqueue(_item);
    }

    if(!this->isRunning())
    {
        this->start(LowPriority);
    }
    else
    {
        qDebug()<< __FILE__<< __LINE__<< __FUNCTION__ << "\n\trestart run loop";

        restart = true;     
        condition.wakeOne();
    }
}

