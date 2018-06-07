#include "query_worker.h"

DistributeQueryWorker::DistributeQueryWorker(QObject *parent) : QObject(parent)
{

}

void DistributeQueryWorker::init_slot()
{

    // QUERY_THREAD_NUMBER = 1;
    int thread_for_querying = (QUERY_THREAD_NUMBER>0)?QUERY_THREAD_NUMBER: QThread::idealThreadCount();
    for(int i = 0;i<thread_for_querying;i++)
    {
        thread_pool_list<< (new QueryThread(
                                &mutex,
                                &condition,
                                QString("Query_Connection_%1").arg(i),
                                &sql_queue
                                ));
        thread_pool_list[i]->start();
    }

    update_progress_timer = new QTimer();
//    update_progress_timer->setInterval(50);
    update_progress_timer->setSingleShot(false);
    connect(update_progress_timer, SIGNAL(timeout()),
            this, SLOT(timer_update_progress_slot()));
}

void DistributeQueryWorker::distribute_new_query_SLOT(int query_id,
                                                      QList<QStringList> uuid_path_list,
                                                      QString sql_text)
{
    // query_id, uuid_path_list, sql_text
    // uuid_path_list : uuid<<path<<rows<< alias
    // from : get_search_included_uuid()
    mutex.lock();
    sql_queue.clear();

    unsigned long queue_count = 0;
    for(const QStringList & uuid_path: uuid_path_list  )
    {
        QString uuid =uuid_path[0];
        QString path = uuid_path[1];
        QString alias = uuid_path[3];
        unsigned long rows = uuid_path[2].toLong();
        if (path == "")
            path = alias + "::";
        if (path =="/")
            path = "";

        Format_Sql_Result format_sql_result =
                format_sql_cmd(path, uuid, sql_text, 0,0);

        /*
         * QString sql = sql_mask + " WHERE " + QString(" (ROWID BETWEEN %1 AND %2) AND").arg(rowid_low).arg(rowid_high)
                    + " (" + sql_cmd + ") " + QString(" LIMIT %d").arg(QUERY_LIMIT);

                    sql = sql_mask + where row between  + sql_cmd + Limit
        */

        if (format_sql_result.ok)
        {
            unsigned long rowid_low = 0 ;
            unsigned long rowid_high;
            while(rowid_low<= rows)
            {
                rowid_high = rowid_low + QUERY_CHUNK_SIZE;

                QString sql = format_sql_result.sql_mask + " WHERE " + QString(" (ROWID BETWEEN %1 AND %2) AND").arg(rowid_low).arg(rowid_high)
                        + " (" + format_sql_result.sql_cmd + ") " + QString(" LIMIT %1").arg(QUERY_LIMIT);
                //QPair<int, QString>
                QPair<QPair<int,bool>, QString> tmp;
                tmp.first = QPair<int,bool>({query_id, format_sql_result.case_sensitive_like_flag_ON});
                tmp.second = sql;
                sql_queue.enqueue( tmp );
                rowid_low = rowid_high + 1;

                queue_count++;
            }
        }
    }
    QUERY_SQL_QUEUE_TOTAL_LENGTH  = queue_count;
    //    mutex.unlock();
    //    mutex.lock();

    // sql_queue.enqueue();

    _query_text_id = query_id;
    update_progress_timer->setInterval(50);
    update_progress_timer->start();

    condition.wakeAll();

    mutex.unlock();
//
}
void DistributeQueryWorker::timer_update_progress_slot()
{
    QMutexLocker locker(&mutex);
    int queye_size = sql_queue.size();
    if (_query_text_id == Query_Text_ID)
    {
        emit  update_progress_SIGNAL(_query_text_id, queye_size);
    }
    else
    {
        emit  update_progress_SIGNAL(Query_Text_ID, 0); // hide progress bar
        update_progress_timer->stop();
    }
    if (queye_size ==0)
        update_progress_timer->stop();
    // quick query --> small interval
    // slow query  --> increase interval gradually
    update_progress_timer->setInterval( std::min( 1000, (int)( update_progress_timer->interval() * 1.5) ));
}

void DistributeQueryWorker::quit_slot()
{

    for(QueryThread* thread: thread_pool_list)
    {
        thread->abort=true;
    }
    mutex.lock();
    sql_queue.clear();
    condition.wakeAll();
    mutex.unlock();
    update_progress_timer->stop();
    delete update_progress_timer;

    for(QueryThread* thread: thread_pool_list)
    {
        delete thread; // ~QueryThread() : abort = true; wait();
    }

    ready_to_quit_flag = true;
}

