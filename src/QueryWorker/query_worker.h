#ifndef QUERY_WORKER_H
#define QUERY_WORKER_H

#include <QObject>
#include <QThread>
#include <QMutex>
#include <QWaitCondition>
#include <QQueue>
#include <QMutexLocker>
#include <QTimer>

#include "globals.h"
#include "query_thread.h"
#include "sql_formatter.h"

class DistributeQueryWorker : public QObject
{
    Q_OBJECT
public:
    explicit DistributeQueryWorker(QObject *parent = nullptr);

    QMutex mutex;
    QWaitCondition condition;
    QQueue<QPair<QPair<int,bool>, QString>>  sql_queue;

    QList<QueryThread *> thread_pool_list;
    bool ready_to_quit_flag = false;

signals:
    void update_progress_SIGNAL(int query_text_id, int  queue_size);

public slots:

    void init_slot();
    void distribute_new_query_SLOT(int, QList<QStringList>, QString);
    void quit_slot();
    void timer_update_progress_slot();

private :
    int _query_text_id ;
    QTimer * update_progress_timer;

};

#endif // QUERY_WORKER_H
