#ifndef INSERT_DB_THREAD_H
#define INSERT_DB_THREAD_H

#include <QObject>
#include <QThread>
#include <QMutex>
#include <QWaitCondition>
#include <QQueue>
#include <QMutexLocker>
#include <QDir>
#include <QSet>
#include <QSqlDatabase>
#include <QElapsedTimer>

#include "partition_information.h"
#include "db_commit_step_optimizer.h"

#include <sys/stat.h>
#include <sys/statvfs.h>

class Insert_db_Thread : public QThread
{
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

    Q_OBJECT

protected:
    void run() override;

public:
    Insert_db_Thread(QObject *parent = 0);
    void set_scan_queue_and_restart_run(QList<QStringList>);
    ~Insert_db_Thread();

signals:
    void update_progress_SIGNAL(long, long , QString);
    void tmp_db_ready_to_merge_SIGNAL();

public slots:

private:
    QMutex mutex;
    QWaitCondition condition;

    bool restart;
    bool abort;
    bool ok;

    bool transaction_supported_flag = false;

    QQueue<QStringList> update_path_queue;

    struct stat stat_buf;
    inline __dev_t dev_id_of_path(QString filename);
    inline void read_to_stat_buf(QString filename);
    long estimate_num_of_files(QString rootpath);

    QSqlDatabase database;

    QElapsedTimer elapsed_timer;

};

#endif // INSERT_DB_THREAD_H
