#include "query_thread.h"
int QueryThread::ERROR_QUERY_ID=-1;
QueryThread::QueryThread(QMutex * mutex_in, QWaitCondition * condition_in,
                         QString db_connection_name_in, QQueue<QPair<QPair<int,bool>, QString>> * sql_queue_in,
                         QObject *)
{
    mutex = mutex_in;
    condition = condition_in;
    db_connection_name = db_connection_name_in;
    sql_queue = sql_queue_in;

    restart = false;
    abort = false;
}

QueryThread::~QueryThread()
{
    //    mutex.lock();
    abort = true;
    //    condition.wakeOne();
    //    mutex.unlock();
    wait();
}



void QueryThread::run()
{
    bool ok;
    QSqlDatabase database;
    database = QSqlDatabase::addDatabase("QSQLITE", db_connection_name);
    database.setDatabaseName(DATABASE_FILE_NAME);
    if (! (database.open()))
    {
        qDebug()<< ("Fail to open db: "  +db_connection_name);
        return;
    }
    else
        qDebug()<<( "Open db OK: "  +db_connection_name);
    QSqlQuery cur(database);
    cur.setForwardOnly(true);

    // TODO: pragma for dbs other than sqlite
    cur.exec("PRAGMA case_sensitive_like=ON;");

    QPair<QPair<int, bool>, QString> pair;
    // open db
    forever {
        mutex->lock();
        while(sql_queue->isEmpty())
        {
            condition->wait(mutex);
            if (abort) break;
        }
        if (! sql_queue->isEmpty())
            pair = sql_queue->dequeue();
        else
            pair.second = "";

        mutex->unlock();

        if(abort)
            break;
        if (pair.second == "")
            continue;
        // QPair<int,QString> pair
        int query_id = pair.first.first;
        bool case_sensitive_like_flag_ON = pair.first.second;
        QString sql = pair.second;

        if (query_id==Query_Text_ID && query_id>ERROR_QUERY_ID )
        {
            // TODO: other than sqlite
            if (case_sensitive_like_flag_ON)
                ok = cur.exec("PRAGMA case_sensitive_like=ON;");
            else
                ok = cur.exec("PRAGMA case_sensitive_like=OFF;");
            if(!ok)
            {
                qDebug()<<"SQL ERROR: "<<__FILE__<< __LINE__<< __FUNCTION__<<
                          "\n\twhen: "<<cur.lastQuery()<<"\n\t"<<cur.lastError();
            }

            ok = cur.exec(sql);
            if (!ok) {
                ERROR_QUERY_ID = query_id;
                qDebug()<<"SQL ERROR: "<<__FILE__<< __LINE__<< __FUNCTION__<<
                          "\n\twhen: "<<cur.lastQuery()<<"\n\t"<<cur.lastError();
            }else
            {
                // return result
                // self.add_row_to_model_SIGNAL.emit(query_id, row)
                // add_row_to_model_SIGNAL(int query_id, QList<QList<QStandardItem *> > list_of_row_to_insert)

                if (query_id==Query_Text_ID &&  CURRENT_MODEL_ITEMS<MODEL_MAX_ITEMS)
                {
                    // build rows_of_item
                    QList<QList<QVariant> > list_of_row_to_insert;

                    while(cur.next())
                    {
                        if (query_id!=Query_Text_ID )
                            break;
                        /*SELECT
                         * Filename,"/devpath/"||Path,Size,IsFolder,atime,mtime,ctime FROM `UUID`
                         * WHERE  (ROWID BETWEEN 1 AND 2) AND ((ctime<1453527153))  LIMIT 10  */
                        QList<QVariant> row_to_insert;

                        for(int idx=0; idx< QUERY_HEADER.len;idx++){
                            row_to_insert  << cur.value(idx);

                        }// END per row loop
                        //                        qDebug()<<"emit row: "<<row_to_insert[0]->data(HACKED_QT_EDITROLE).toString()
                        //                                  <<row_to_insert[1]->data(HACKED_QT_EDITROLE).toString();

                          list_of_row_to_insert<<row_to_insert;
                    }// END whole list loop
                    if (list_of_row_to_insert.length()>0)
                    {
                        if (query_id!= Query_Text_ID)
                        {
                        }
                        else
                        {
//                            qDebug()<<"emit list";
                            emit  add_row_to_model_by_qvariant_SIGNAL( query_id, list_of_row_to_insert);

                        }
                    }
                }
            }
        }

        if(abort)
            break;

    }

    // close db
    database.close();
}

//===================================================================================

// ?? create item in this thread may sometime crash the main thread, when access data(Role)
void QueryThread::run_old_2()
{
    bool ok;
    QSqlDatabase database;
    database = QSqlDatabase::addDatabase("QSQLITE", db_connection_name);
    database.setDatabaseName(DATABASE_FILE_NAME);
    if (! (database.open()))
    {
        qDebug()<< ("Fail to open db: "  +db_connection_name);
        return;
    }
    else
        qDebug()<<( "Open db OK: "  +db_connection_name);
    QSqlQuery cur(database);
    cur.setForwardOnly(true);

    // TODO: pragma for dbs other than sqlite
    cur.exec("PRAGMA case_sensitive_like=ON;");

    QPair<QPair<int, bool>, QString> pair;
    // open db
    forever {
        mutex->lock();
        while(sql_queue->isEmpty())
        {
            condition->wait(mutex);
            if (abort) break;
        }
        if (! sql_queue->isEmpty())
            pair = sql_queue->dequeue();
        else
            pair.second = "";

        mutex->unlock();

        if(abort)
            break;
        if (pair.second == "")
            continue;
        // QPair<int,QString> pair
        int query_id = pair.first.first;
        bool case_sensitive_like_flag_ON = pair.first.second;
        QString sql = pair.second;

        if (query_id==Query_Text_ID && query_id>ERROR_QUERY_ID )
        {
            // TODO: other than sqlite
            if (case_sensitive_like_flag_ON)
                ok = cur.exec("PRAGMA case_sensitive_like=ON;");
            else
                ok = cur.exec("PRAGMA case_sensitive_like=OFF;");
            if(!ok)
            {
                qDebug()<<"SQL ERROR: "<<__FILE__<< __LINE__<< __FUNCTION__<<
                          "\n\twhen: "<<cur.lastQuery()<<"\n\t"<<cur.lastError();
            }

            ok = cur.exec(sql);
            if (!ok) {
                ERROR_QUERY_ID = query_id;
                qDebug()<<"SQL ERROR: "<<__FILE__<< __LINE__<< __FUNCTION__<<
                          "\n\twhen: "<<cur.lastQuery()<<"\n\t"<<cur.lastError();
            }else
            {
                // return result
                // self.add_row_to_model_SIGNAL.emit(query_id, row)
                // add_row_to_model_SIGNAL(int query_id, QList<QList<QStandardItem *> > list_of_row_to_insert)

                if (query_id==Query_Text_ID &&  CURRENT_MODEL_ITEMS<MODEL_MAX_ITEMS)
                {
                    // build rows_of_item
                    QList<QList<QStandardItem *> > list_of_row_to_insert;

                    QStandardItem * newitem;
                    QStandardItem * extension_item;
                    while(cur.next())
                    {
                        if (query_id!=Query_Text_ID )
                            break;
                        /*SELECT
                         * Filename,"/devpath/"||Path,Size,IsFolder,atime,mtime,ctime FROM `UUID`
                         * WHERE  (ROWID BETWEEN 1 AND 2) AND ((ctime<1453527153))  LIMIT 10  */
                        QList<QStandardItem *> row_to_insert;

                        for(int idx=0; idx< QUERY_HEADER.len;idx++){
                            //newitem = new QStandardItem(QString::number(idx));
                            newitem = new QStandardItem();
                            QVariant current_value = cur.value(idx);
                            if (current_value.isNull() || (!current_value.isValid()))
                                current_value = QVariant(1);
                            //                            newitem->setData(cur.value(idx), Qt::DisplayRole);
                            //                            newitem->setData(cur.value(idx), HACKED_QT_EDITROLE);
                            switch (idx) {
                            case QUERY_HEADER_class::Filename_:
                            {
                                QString pathname = current_value.toString();
                                newitem->setData(pathname, Qt::DisplayRole);
                                newitem->setData(pathname, HACKED_QT_EDITROLE);
                                row_to_insert << newitem;}
                                break;
                            case QUERY_HEADER_class::Path_:
                                //                                newitem->setData(cur.value(idx), HACKED_QT_EDITROLE);
                            {QString pathname = current_value.toString();
                                if(pathname.mid(0,2)=="//")  // modify path  like    //usr/bin
                                    pathname = pathname.mid(1);
                                newitem->setData(pathname, Qt::DisplayRole);
                                newitem->setData(pathname, HACKED_QT_EDITROLE);
                                row_to_insert << newitem;}
                                break;
                            case QUERY_HEADER_class::Size_:
                            case QUERY_HEADER_class::atime_:
                            case QUERY_HEADER_class::ctime_:
                            case QUERY_HEADER_class::mtime_:
                                //                                newitem->setData(cur.value(idx), HACKED_QT_EDITROLE);
                                newitem->setData(current_value, Qt::DisplayRole);
                                newitem->setData(current_value, HACKED_QT_EDITROLE);
                                row_to_insert << newitem;
                                break;
                            case QUERY_HEADER_class::IsFolder_:
                                // Alignment is controled by html_delegate, no effect here
//                                newitem->setTextAlignment(Qt::AlignHCenter|Qt::AlignVCenter);
                                newitem->setData(current_value.toBool(), Qt::DisplayRole);
                                newitem->setData(current_value.toBool(), HACKED_QT_EDITROLE);
                                //                                newitem->setData(cur.value(idx), HACKED_QT_EDITROLE);
                                row_to_insert << newitem;
                                extension_item =new QStandardItem();
                                if (current_value.toBool())
                                {
                                }
                                else{
                                    QString extension = cur.value(QUERY_HEADER_class::Filename_).toString();
                                    if (extension.contains("."))
                                        extension = extension.split(".").last();
                                    else
                                        extension = "";
                                    extension_item->setData(extension, HACKED_QT_EDITROLE);
                                    extension_item->setData(extension, Qt::DisplayRole);
                                }
                                row_to_insert << extension_item;
                                break;
                            default:
                                Q_ASSERT(false);
                                break;
                            }
                            QVariant test =  newitem->data(Qt::DisplayRole);
                            Q_ASSERT((row_to_insert.last() != nullptr));
                        }// END per row loop
                        //                        qDebug()<<"emit row: "<<row_to_insert[0]->data(HACKED_QT_EDITROLE).toString()
                        //                                  <<row_to_insert[1]->data(HACKED_QT_EDITROLE).toString();


                        for(int col=0; col < row_to_insert.length(); col++)
                        {

                            // FIXME
                            QVariant aaa = row_to_insert[col]->data(Qt::DisplayRole);
                        }


                        list_of_row_to_insert<<row_to_insert;
                    }// END whole list loop
                    if (list_of_row_to_insert.length()>0)
                    {
                        if (query_id!= Query_Text_ID)
                        {
                            // free memory
                            for(const QList<QStandardItem *>& list: list_of_row_to_insert)
                            {
                                for(QStandardItem * item: list)
                                    delete item;
                            }
                        }
                        else
                            emit  add_row_to_model_SIGNAL( query_id, list_of_row_to_insert);
                    }
                }
            }
        }

        if(abort)
            break;

    }

    // close db
    database.close();
}
