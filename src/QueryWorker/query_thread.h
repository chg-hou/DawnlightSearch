#ifndef QUERY_THREAD_H
#define QUERY_THREAD_H

#include <QObject>
#include <QThread>
#include <QMutex>
#include <QWaitCondition>
#include <QQueue>
#include <QMutexLocker>
#include <QStandardItem>

#include "globals.h"

class QueryThread : public QThread
{
    Q_OBJECT

protected:
    void run() override;
    void run_old_2() ;


public:
    QueryThread(QMutex * mutex_in, QWaitCondition * condition_in,
                QString db_connection_name_in, QQueue<QPair<QPair<int,bool>, QString>> * sql_queue_in,
               QObject *parent = 0);
    ~QueryThread();

signals:
//    void update_progress_SIGNAL(int query_text_id, int  queue_size);
    //void add_row_to_model_SIGNAL(int,QList<QVariant>);

    void add_row_to_model_SIGNAL(int query_id, QList<QList<QStandardItem *> > list_of_row_to_insert);
    void add_row_to_model_by_qvariant_SIGNAL(int query_id, QList<QList<QVariant> > list_of_row_to_insert);

public:
    bool restart;
    bool abort;
    QQueue<QStringList> update_path_queue;
    QString db_connection_name;
    static int ERROR_QUERY_ID ;

private:

    bool ok;

    //QSqlDatabase database;

    QMutex * mutex;
    QWaitCondition * condition;
    QQueue<QPair<QPair<int,bool>,QString>>  * sql_queue;

};


#endif // QUERY_THREAD_H
