#ifndef UPDATE_DB_MODULE_H
#define UPDATE_DB_MODULE_H

#include <QObject>
#include <QString>
#include <QThread>
#include <QList>
#include <QString>
#include <QMutex>
#include <QQueue>
#include <QTimer>
#include <QDateTime>
#include <QFile>
#include <QByteArray>
#include <QLockFile>

#include "globals.h"
#include "partition_information.h"
#include "insert_db_thread.h"

class Update_DB_Object : public QObject  //public QThread
{
    //https://doc.qt.io/qt-5/threads-technologies.html
    // Have an object living in another thread that can perform different tasks upon request and/or
    // can receive new data to work with.	Subclass a QObject to create a worker. Instantiate this
    // worker object and a QThread. Move the worker to the new thread. Send commands or data to the
    // worker object over queued signal-slot connections.

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
public:
    explicit Update_DB_Object( QObject *parent=nullptr );
    ~Update_DB_Object();
    void _init_db();
    bool update_uuid();
    void init_table(QString table_name, bool clear_table=true);
    bool restart_flag;
    bool quit_flag;
    Insert_db_Thread * insert_db_thread;

    void update_table_uuid_from_db();

public slots:
    // TODO: test whether slots/function will block ui thread
    void init_slot();
    void init_start_timer_slot();

    void quit_slot();

    void refresh_mount_state_timer_slot();

    void refresh_rowid_timer_slot();
    void update_db_timer_slot();
    void update_db_slot(QList<QStringList>);
    void save_uuid_flag_slot(QList<QVariantList > uuid_list, bool quit_flag);
    void merge_db_slot();
    void get_table_uuid_slot();


//protected:
//    void run() override;

signals:
    void init_ready_connect_mainWindow_SIGNAL();

    void insert_db_SIGNAL(QString, QList<QString>, int,int,QString );
    void update_progress_SIGNAL( long,long,QString );
    void update_mount_state_SIGNAL( );
    void update_table_uuid_from_db_SIGNAL(QList<QVariantList>);  // -->refresh_table_uuid_from_db_slot(QList<QVariantList> rst)
    void update_rowid_SIGNAL( QList<QPair<QString,QVariant>> );
    void get_table_uuid_sendback_SIGNAL( QList<QVariantList> );
    void show_statusbar_warning_msg_SIGNAL( QString );

private:
    QSqlDatabase database;
    QSqlQuery cur;
    QMutex mutex;
    QQueue<QString> update_path_queue;
    QQueue<QString> sql_insert_queue;


    QTimer * refresh_mount_state_timer;
    QTimer * refresh_rowid_timer;
    qint64 rowid_timestamp=0;

    QLockFile * db_lockfile;

    bool ok;
};

#endif // UPDATE_DB_MODULE_H
