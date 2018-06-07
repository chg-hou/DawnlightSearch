#ifndef MAINWINDOWS_H
#define MAINWINDOWS_H


#ifndef USE_GIO_LIB_FOR_OPENWITH_MENU
//    #define USE_GIO_LIB_FOR_OPENWITH_MENU
#endif
// sudo apt install libgtk-3-dev
// TODO: any pure Qt solution?
// ? libqt5glib-2.0-0:  C++ bindings library for GLib and GObject with a Qt-style API - Qt 5 build

#ifndef USE_KDELIBS_LIB_FOR_OPENWITH_MENU
    // sudo apt install kdelibs5-dev
//     #define USE_KDELIBS_LIB_FOR_OPENWITH_MENU
#endif
#ifndef USE_KF5_LIB_FOR_OPENWITH_MENU
    // sudo apt install kio-dev
//    #define USE_KF5_LIB_FOR_OPENWITH_MENU
#endif

#ifdef USE_GIO_LIB_FOR_OPENWITH_MENU
//================================== method 1 : gio =============================================
// https://stackoverflow.com/questions/18240876/qt-creator-does-not-find-functions-inside-library

// CONFIG+=link_pkgconfig
// PKGCONFIG+=gio-2.0

// need put include gio before qt:
// http://gstreamer-devel.966125.n4.nabble.com/rtsp-server-h-qt-integrating-problem-td4676924.html
//extern "C" {
#include <gio/gio.h>
#include <gtk/gtk.h>
//#include <glib.h>
#include <QIcon>
#include <QString>

struct AppLauncher{
    QIcon icon;
    QString appname;
    QString apptooltip;
    GAppInfo * app_info;
};
//}
#endif

//================================== method 2 : kdelibs =============================================
// https://api.kde.org/4.x-api/kdelibs-apidocs/kio/html/classKFileItemActions.html
// can obtain action directly. unfortunately able to compile using qmake.

#ifdef USE_KDELIBS_LIB_FOR_OPENWITH_MENU
   // #include <kfileitemactions.h>
#include <kfileitem.h>

#endif

//================================== method 3 : kio in KDE Framework 5 =============================================
// https://api.kde.org/frameworks/kio/html/classKFileItemActions.html
// can obtain action directly.

#ifdef USE_KF5_LIB_FOR_OPENWITH_MENU
   // #include <kfileitemactions.h>

//#include <KFileItemActions>
//#include <KF5/KIOWidgets/KFileItemActions>
//#include <KFileItemListProperties>
#include <KF5/KIOCore/KFileItemListProperties>
#include <KF5/KIOCore/KFileItem>
#include <KF5/KIOWidgets/KFileItemActions>
#include <KF5/KIOFileWidgets/KFileCopyToMenu>

#endif


//#include <kfileitemactions.h>

#include "ui_Ui_mainwindow.h"
#include <QMainWindow>
#include <QWidget>
#include <QProgressBar>
#include <QStatusBar>
#include <QDebug>
#include <QTimer>
#include <QElapsedTimer>
#include <QDesktopWidget>
#include <QRectF>
#include <QLineEdit>
#include <QTableWidget>
#include <QTableWidgetItem>
#include <Qt>
#include <QThread>
#include <QStandardItemModel>
#include <QToolTip>
#include <QMutex>
#include <QMutexLocker>
#include <QDesktopServices>
#include <QMimeData>
#include <QClipboard>
#include <QMessageBox>
#include <QTranslator>

#include "DB_Builder/update_db_module.h"
#include "QueryWorker/query_worker.h"
#include "globals.h"
#include "QueryWorker/sql_formatter.h"
#include "UI_delegate/html_delegate.h"

#include "ui_change_advanced_setting_dialog.h"
#include "ui_change_excluded_folder_dialog.h"
// (copy from python version) ? qt bug: cannot set different values for display and user roles.

struct ResultTableRow{
    // row_to_insert<< filename << path<< fullpath <<isfolder;
    QString filename;
    QString path;
    QString fullpath;
    bool isfolder;
} ;


namespace Ui {
class MainWindow;
}


class MainWindow : public QMainWindow, public Ui_MainWindow
{
    Q_OBJECT

protected:
      bool eventFilter(QObject *obj, QEvent *event) ;

public slots:

    void _on_push_button_updatedb_clicked();
    void _on_push_button_stopupdatedb_clicked();
    void update_query_result();
    void lazy_tableview_sort_slot();
    void _hide_tooltip_slot();
    void _restore_statusbar_style();

    void _show_dialog_change_excluded_folders();
    void _show_tooltips_change_excluded_folders();

    void action_uuid_show_all(bool);
    void action_uuid_show_uuid();
    void action_uuid_hide_uuid();
    void action_uuid_check_included();
    void action_uuid_uncheck_included();
    void action_uuid_check_updatable();

    void action_uuid_uncheck_updatable();

    void _on_push_button_clicked();

    void _on_push_button_updatedb_only_selected_clicked();

    //    void on_table_header_clicked();
    //    void on_table_uuid_itemChanged();
    void _on_lineedit_enter_pressed();

    void _on_lineedit_text_changed(QString);
    void _on_query_text_changed();
    void _on_update_progress_bar(int, int);
    void _on_tableview_context_menu_requested(QPoint);
    void _on_tableview_double_clicked(QModelIndex);
    void _on_tableview_context_menu_open();
    void _on_tableview_context_menu_open_path();
    void _on_tableview_context_menu_copy_fullpath();
    void _on_tableview_context_menu_copy_filename();
    void _on_tableview_context_menu_copy_path();
    void _on_tableview_context_menu_move_to();
    void _on_tableview_context_menu_copy_to();
    void _on_tableview_context_menu_move_to_trash();
    void _on_tableview_context_menu_delete();


    void _on_toolbutton_casesensitive_toggled(bool checked);
    void _on_match_option_changed(bool);
    // void _on_model_receive_new_row(int, QList<int>);

    void _on_db_progress_update(long,long,QString);

    void show_statusbar_warning_msg_slot(QString msg, long timeout, bool warning_flag);
    //void get_table_widget_uuid_back_slot(QList<int>);
    void refresh_table_uuid_from_db_slot(QList<QVariantList>);
    void refresh_table_uuid_mount_state_slot();
    void refresh_table_uuid_row_id_slot(QList<QPair<QString,QVariant> >);

    long _find_row_number_of_uuid(QString uuid);
    void  _toggle_C_MFT_parser(bool enable_C_MFT_parser);
    void _toggle_use_MFT_parser(bool enable_MFT_parser);

    void _on_tableWidget_uuid_context_menu_requested(QPoint);


    void _show_dialog_about(bool);
    void _show_dialog_about_qt();
    void _about_open_homepage();
    void _about_open_latest_version();
    void _show_dialog_advanced_setting();
    void _open_setting_path();
    void _open_db_path();
    void _open_temp_db_path();
    void change_language_auto();
    void change_language_English();
    void change_language_zh_CN();

    void init_db_module_ready_connect_mainWindow_SLOT();

    // =========================== query
    //void _on_model_receive_new_row(int query_id, QList<QList<QStandardItem *>> list_of_row_to_insert);
    void _on_model_receive_new_row_old(int query_id, QList<QList<QStandardItem *>> list_of_row_to_insert);
    void _on_model_receive_new_row_old_2(int query_id, QList<QList<QStandardItem *>> list_of_row_to_insert);

    void _on_model_receive_new_row(int query_id, QList<QList<QVariant>> list_of_row_to_insert);

signals:
    void init_db_module_SIGNAL();
    void init_db_start_timer_SIGNAL();
    void db_module_quit_SIGNAL();

    void init_query_worker_SIGNAL();
    void query_worker_module_quit_SIGNAL();

    void save_uuid_flag_and_quit_SIGNAL(QList<QVariantList>,bool);
    void update_db_SIGNAL(QList<QStringList>);
    void get_uuid_SIGNAL();
    void merge_db_SIGNAL();

    void send_query_to_worker_SIGNAL(int, QList<QStringList>, QString);

public:


    explicit MainWindow(QWidget *parent = 0);
    ~MainWindow();
    QString _Former_search_text="";

    QTimer * lazy_query_timer, *lazy_sort_timer, * hide_tooltip_timer, * restore_statusbar_timer ;

    QLineEdit * lineEdit_search;

    //QElapsedTimer * elapsedtimer;
    void closeEvent(QCloseEvent *);


    QStandardItemModel * model;
    QStringList header_list;

    int ini_after_show();
    void ini_table();
    void ini_subthread();

    void retranslate_whole_ui();
    void _change_language(QString );

    QList<QStringList> get_search_included_uuid();

private:

    bool FIRST_TIME_LOAD_FLAG = true;

    Ui::MainWindow *ui;

    QProgressBar progressBar;

    void __init_connect_menu_action();

    QIcon query_ok_icon, query_empty_icon,query_error_icon;

    QIcon device_mounted_icon, device_unmounted_icon;

    Update_DB_Object* db_object ;
    QThread  db_update_thread;

    DistributeQueryWorker * query_worker;
    QThread query_worker_thread;

    QMenu * tableWidget_uuid_menu;

    QMutex mutex_table_result;

    //    QStatusBar statusBar;

    QList<ResultTableRow> get_tableview_selected();
    QString _get_filetype_of_selected();


    int last_width = 0;
    int last_height = 0;
#ifdef USE_KF5_LIB_FOR_OPENWITH_MENU
    void get_default_app(QString);
#endif


#ifdef USE_GIO_LIB_FOR_OPENWITH_MENU
    AppLauncher get_default_app(QString file_type);
    QList<GAppInfo *> g_object_ptr_trarsh; // g_clear_object(&pGtkIconTheme) ,  g_object_unref
#endif
};

#endif // MAINWINDOWS_H
