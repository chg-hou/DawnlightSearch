#include "MainWindow.h"


MainWindow::MainWindow(QWidget *parent) :
    QMainWindow(parent),
    ui(new Ui::MainWindow)
{
    ui->setupUi(this);
//    ui->centralWidget->hide();
    device_mounted_icon = QIcon(QPixmap(":/icon/ui/icon/dev-harddisk.png"));
    device_unmounted_icon = QIcon(QPixmap(":/icon/ui/icon/tab-close-other.png"));


    QSettings settings(QSettings::IniFormat,QSettings::UserScope,
                       ORGANIZATION_NAME,ALLICATION_NAME);


    progressBar.setRange(0, 10000);

    progressBar.setValue(400);

    ui->statusBar->addPermanentWidget(&progressBar);

    progressBar.show();
    progressBar.setVisible(false);


    connect(ui->actionUpdatedb, SIGNAL(triggered()),
            SLOT(_on_push_button_updatedb_clicked(void))
            );
    connect(ui->actionStop_Updating, SIGNAL(triggered()),
            SLOT(_on_push_button_stopupdatedb_clicked(void))
            );

    lazy_query_timer = new QTimer(this);
    lazy_query_timer->setSingleShot(true);
    connect(lazy_query_timer,SIGNAL(timeout()),
            SLOT(update_query_result()));
    lazy_query_timer->setInterval(settings.value("Start_Querying_after_Typing_Finished",
                                                 50).toInt()
                                  );

    lazy_sort_timer = new QTimer(this);
    lazy_sort_timer->setSingleShot(true);
    connect(lazy_sort_timer,SIGNAL(timeout()),
            SLOT(lazy_tableview_sort_slot()));
    lazy_sort_timer->setInterval(settings.value("Restor_Sort_after_New_Row_Inserted",
                                                50).toInt()
                                 );

    hide_tooltip_timer = new QTimer(this);
    hide_tooltip_timer->setSingleShot(true);
    connect(hide_tooltip_timer,SIGNAL(timeout()),
            SLOT(_hide_tooltip_slot()));
    hide_tooltip_timer->setInterval(2000);

    restore_statusbar_timer = new QTimer(this);
    restore_statusbar_timer->setSingleShot(true);
    connect(restore_statusbar_timer,SIGNAL(timeout()),
            SLOT(_restore_statusbar_style()));
    restore_statusbar_timer->setInterval(2000 );


    QRectF screen_size = QRectF(
                QDesktopWidget().screenGeometry(
                    QDesktopWidget().primaryScreen()
                    )
                );
    auto screen_w = screen_size.x() + screen_size.width();
    auto screen_h = screen_size.y() + screen_size.height();

    int x = settings.value("Main_Window/x",screen_w / 4).toInt();
    int y = settings.value("Main_Window/y", screen_h / 4).toInt();
    int  w = settings.value("Main_Window/width", -1).toInt();
    int  h = settings.value("Main_Window/height", -1).toInt();

    MOUNT_STATE_UPDATE_INTERVAL = settings.value("Mount_State_Update_Interval",3000).toInt();
    ROWID_UPDATE_INTERVAL = settings.value("Rowid_Update_Interval",3000).toInt();
    DB_UPDATE_INTERVAL = settings.value("Database_Update_Interval", 1000).toInt();

    if (w>0)
        this->resize(w,h);
    this->move(x,y);

    last_width = width();
    last_height = height();

    __init_connect_menu_action();

    lineEdit_search = ui->comboBox_search->lineEdit();

    connect(lineEdit_search, SIGNAL(textChanged(QString)),
            SLOT(_on_lineedit_text_changed(QString)));
    lineEdit_search->setClearButtonEnabled(True);

    query_ok_icon.addPixmap(QPixmap(":/icon/ui/icon/dialog-ok.png"));
    query_error_icon.addPixmap(QPixmap(":/icon/ui/icon/hint.png"),
                               QIcon::Normal,QIcon::Off);
    query_error_icon.addPixmap(QPixmap(":/icon/ui/icon/hint.png"),
                               QIcon::Disabled,QIcon::Off);

    connect(lineEdit_search,SIGNAL(returnPressed()),
            this, SLOT(_on_lineedit_enter_pressed()));

    //# search setting
    connect(ui->actionCase_Sensitive,SIGNAL(triggered(bool)),
            this, SLOT(_on_toolbutton_casesensitive_toggled(bool)));

    ui->toolButton_casesensitive->setChecked(
                settings.value("Search/Case_Sensitive", False).toBool()
                );

    //TODO: typo
    ui->toolButton_avd_setting->setChecked(
                settings.value("Main_Window/Show_Search_Setting_Panel", true).toBool()
                );
    ui->dockWidget_search_settings->setVisible(
                settings.value("Main_Window/Show_Search_Setting_Panel", true).toBool()
                );
    DATETIME_FORMAT = settings.value("Search/Date_Format","d/M/yyyy h:m:s").toString();


    connect(ui->radioButton_1,SIGNAL(toggled(bool)),
            SLOT(_on_match_option_changed(bool)));
    connect(ui->radioButton_2,SIGNAL(toggled(bool)),
            SLOT(_on_match_option_changed(bool)));
    connect(ui->radioButton_3,SIGNAL(toggled(bool)),
            SLOT(_on_match_option_changed(bool)));
    connect(ui->radioButton_4,SIGNAL(toggled(bool)),
            SLOT(_on_match_option_changed(bool)));
    connect(ui->radioButton_5,SIGNAL(toggled(bool)),
            SLOT(_on_match_option_changed(bool)));

    switch (settings.value("Search/Match_Mode",1).toInt()-1) {
    case 1:
        ui->radioButton_2->setChecked(True);
        break;
    case 2:
        ui->radioButton_3->setChecked(True);
        break;
    case 3:
        ui->radioButton_4->setChecked(True);
        break;
    case 4:
        ui->radioButton_5->setChecked(True);
        break;
    default: // case 0
        ui->radioButton_1->setChecked(True);
        break;
    }

    //# skip diff dev
    SKIP_DIFF_DEV = settings.value("Database/Skip_Different_Device",True).toBool();

    //# size unit
    SIZE_UNIT = settings.value("Size_Unit","KB").toString();

    //# instant search
    INSTANT_SEARCH = settings.value("Search/Instant_Search", True).toBool();

    //# load excluded UUID
    EXCLUDED_UUID = settings.value("Excluded_UUID",DEFAULT_EXCLUDED_UUID).toStringList();
    ui->actionShow_All->setChecked(settings.value("Excluded_UUID_Visible", True).toBool());

    // threads used for querying
    QUERY_THREAD_NUMBER =  settings.value("Search/Threads", QThread::idealThreadCount()).toInt();
    QUERY_THREAD_NUMBER =  std::min( std::max(0, QUERY_THREAD_NUMBER) ,  QThread::idealThreadCount());

    QUERY_CHUNK_SIZE = settings.value("Query_Chunk_Size", (unsigned long long) QUERY_CHUNK_SIZE).toInt();
    MODEL_MAX_ITEMS = settings.value("Max_Items_in_List", (unsigned long long)MODEL_MAX_ITEMS).toInt();


    // compress db
    COMPRESS_DB_FILE = settings.value("Compress_DB_File", COMPRESS_DB_FILE).toBool();

    CASE_SENSTITIVE = settings.value("Search/Case_Sensitive",CASE_SENSTITIVE).toBool();


}



void MainWindow::ini_after_show(){


    qDebug() << "ini table.";

    ui->statusBar->showMessage(QCoreApplication::translate("statusbar","Loading..."));
    ini_table();
    qDebug() << "ini_subthread";
    ini_subthread();
    qDebug() << "ini done.";
    QSettings settings(QSettings::IniFormat,QSettings::UserScope,
                       ORGANIZATION_NAME,ALLICATION_NAME);
    if (settings.contains("Main_Window/DOCK_LOCATIONS"))
    {
        try{
            restoreState(settings.value("Main_Window/DOCK_LOCATIONS").toByteArray());
        }
        catch (...)
        {
            qDebug() << "Fail to restore dock states.";
        }
    }
    else
        ui->dockWidget_sqlcmd->close();
//    ui->centralWidget->hide();
    // MainWindow::setCentralWidget(NULL);
//    ui->dockWidget_result->titleBarWidget()->setHidden(true);
}
void MainWindow::ini_table(){
    ui->tableWidget_uuid->setColumnCount(UUID_HEADER_LABEL.length() );
    QStringList UUID_HEADER_LABEL_tr;
    for(const QString & str: UUID_HEADER_LABEL){
        std::string s2 = str.toStdString();
        const char * c3 = s2.c_str();
        UUID_HEADER_LABEL_tr<<QCoreApplication::translate("ui",c3);
    }
    ui->tableWidget_uuid->setHorizontalHeaderLabels(UUID_HEADER_LABEL_tr);

    ui->tableWidget_uuid->horizontalHeader()->setSectionsMovable(true);
    ui->tableWidget_uuid->setContextMenuPolicy(Qt::CustomContextMenu);

    connect(ui->tableWidget_uuid,
            SIGNAL(customContextMenuRequested(QPoint)),
            this, SLOT(_on_tableWidget_uuid_context_menu_requested(QPoint)));

    tableWidget_uuid_menu = new QMenu(this);
    tableWidget_uuid_menu->addAction(ui->actionShow_All );
    tableWidget_uuid_menu->addSeparator( );
    tableWidget_uuid_menu->addAction(ui->actionShow_UUID );
    tableWidget_uuid_menu->addAction(ui->actionHide_UUID );
    tableWidget_uuid_menu->addSeparator( );
    tableWidget_uuid_menu->addAction(ui->actionUpdatedb_onlyselected );
    tableWidget_uuid_menu->addSeparator( );
    tableWidget_uuid_menu->addAction(ui->actionUpdatedb );
    tableWidget_uuid_menu->addAction(ui->actionStop_Updating );

    tableWidget_uuid_menu->addSeparator( );
    tableWidget_uuid_menu->addAction(ui->actionCheck_Included );
    tableWidget_uuid_menu->addAction(ui->actionUncheck_Included );
    tableWidget_uuid_menu->addSeparator( );
    tableWidget_uuid_menu->addAction(ui->actionCheck_Updatable );
    tableWidget_uuid_menu->addAction(ui->actionUncheck_Updatable );

    connect(ui->actionShow_All,SIGNAL(triggered(bool)),
            this,SLOT(action_uuid_show_all(bool)));
    connect(ui->actionShow_UUID,SIGNAL(triggered(bool)),
            this,SLOT(action_uuid_show_uuid()));
    connect(ui->actionHide_UUID,SIGNAL(triggered(bool)),
            this,SLOT(action_uuid_hide_uuid()));

    connect(ui->actionCheck_Included,SIGNAL(triggered(bool)),
            this,SLOT(action_uuid_check_included()));
    connect(ui->actionUncheck_Included,SIGNAL(triggered(bool)),
            this,SLOT(action_uuid_uncheck_included()));
    connect(ui->actionCheck_Updatable,SIGNAL(triggered(bool)),
            this,SLOT(action_uuid_check_updatable()));
    connect(ui->actionUncheck_Updatable,SIGNAL(triggered(bool)),
            this,SLOT(action_uuid_uncheck_updatable()));
    connect(ui->actionUpdatedb_onlyselected,SIGNAL(triggered(bool)),
            this,SLOT(_on_push_button_updatedb_only_selected_clicked()));


    // Recovery column width
    QSettings settings(QSettings::IniFormat, QSettings::UserScope,
                       ORGANIZATION_NAME, ALLICATION_NAME);
    //qRegisterMetaTypeStreamOperators<QList<int>>("QList<int>");
    //    QList<QVariant> width_list_result = settings.value("Column_width_of_reslut_list",{}).toList();
    //QList<int> width_list_uuid = settings.value("Column_width_of_uuid_list").value<QList<int>>();
    int width_list_uuid_size = settings.beginReadArray("Column_width_of_uuid_list");
    width_list_uuid_size = std::min( width_list_uuid_size, ui->tableWidget_uuid->columnCount() );
    QList<int> width_list_uuid;
    for(int i=0; i<  width_list_uuid_size;i++)
    {
        settings.setArrayIndex(i);
        width_list_uuid << settings.value("width").toInt();
    }settings.endArray();

    qDebug()<<" width_list_uuid: " <<width_list_uuid;
//    qDebug()<<" width_list_uuid: " <<settings.value("Column_width_of_uuid_list");
//    qDebug()<<" width_list_uuid: " <<settings.value("Column_width_of_uuid_list").value<QList<int>>();
    if (width_list_uuid.length()==0)
    {
        // load default width
        width_list_uuid = {59, 193, 77, 49, 88, 72, 67, 49, 49, 78, 49, 100};
    }
    try{
        for(int i =0; i < width_list_uuid.length();i++)
        {
            ui->tableWidget_uuid->setColumnWidth(i,
                                                 width_list_uuid[i]);
        }
    }catch(...)
    {

    }
    // ======================================result table start here ========================================================
    model = new QStandardItemModel();
    model->setSortRole(HACKED_QT_EDITROLE);
    header_list = DB_HEADER_LIST;
    model->setColumnCount(header_list.length());

    QStringList DB_HEADER_LABEL_tr;
    for(const QString & str: DB_HEADER_LABEL){
        std::string s2 = str.toStdString();
        const char * c3 = s2.c_str();
        DB_HEADER_LABEL_tr<<QCoreApplication::translate("ui",c3);
    }
    model->setHorizontalHeaderLabels(DB_HEADER_LABEL_tr);

    //TODO: HTMLDelegate = HTMLDelegate_VC_HL
    // html hightlight : self.tableView.setItemDelegate( HTMLDelegate())

    ui->tableView->setModel(model);

    HTMLDelegate * delegate = new HTMLDelegate(model);
    ui->tableView->setItemDelegate(delegate);
    ui->tableView->horizontalHeader()->setSectionsMovable(true);
    ui->tableView->setContextMenuPolicy(Qt::CustomContextMenu);
    connect(ui->tableView,SIGNAL(customContextMenuRequested(QPoint)),
            this, SLOT(_on_tableview_context_menu_requested(QPoint)));
    connect(ui->tableView,SIGNAL(doubleClicked(QModelIndex)),
            this, SLOT(_on_tableview_double_clicked(QModelIndex)));
    ui->tableView->verticalHeader()->hide();
    ui->tableView->setSortingEnabled(true);
    ui->tableView->sortByColumn(0, Qt::AscendingOrder);

    int width_list_tableview_size = settings.beginReadArray("Column_width_of_reslut_list");
    width_list_tableview_size = std::min( width_list_tableview_size, ui->tableView->model()->columnCount() );
    QList<int> width_list_result;
    for(int i=0; i<  width_list_tableview_size;i++)
    {
        settings.setArrayIndex(i);
        width_list_result << settings.value("width").toInt();
    }settings.endArray();
    qDebug()<<" width_list_result: " <<width_list_result;
    if (width_list_result.length()==0)
    {
        // load default width
        width_list_result = {157, 100, 49, 49, 62, 100, 100, 100};
    }
    try{
        for(int i =0; i < width_list_result.length();i++)
            ui->tableView->setColumnWidth(i,width_list_result[i]);
    }catch(...)
    {
    }
}
void MainWindow::ini_subthread(){

    qDebug()<<"Update_DB_Object init...";
    db_object = new Update_DB_Object();
    db_object->moveToThread(&db_update_thread);
    //    connect(ui->actionUpdatedb, SIGNAL(triggered()),
    //            db_object,SLOT(update_db_timer_slot()),
    //            Qt::QueuedConnection
    //            );
    db_update_thread.start();

    query_worker = new DistributeQueryWorker();
    query_worker->moveToThread(&query_worker_thread);
    query_worker_thread.start();

    connect(db_object, SIGNAL(update_rowid_SIGNAL(QList<QPair<QString,QVariant> >)),
            this, SLOT(refresh_table_uuid_row_id_slot(QList<QPair<QString,QVariant> >)));


    connect(this, SIGNAL(init_db_module_SIGNAL()),
            db_object, SLOT(init_slot()));
    connect(this,SIGNAL(init_db_start_timer_SIGNAL()),
            db_object,SLOT(init_start_timer_slot()));
    connect(db_object,SIGNAL(init_ready_connect_mainWindow_SIGNAL()),
            this,SLOT(init_db_module_ready_connect_mainWindow_SLOT()));
    connect(db_object,SIGNAL(show_statusbar_warning_msg_SIGNAL(QString)),
            this, SLOT(show_statusbar_warning_msg_slot(QString)));


    connect(this, SIGNAL(init_query_worker_SIGNAL()),
            query_worker, SLOT(init_slot()));
    connect(this,SIGNAL(query_worker_module_quit_SIGNAL()),
            query_worker, SLOT(quit_slot()));

    emit init_db_module_SIGNAL();
    emit init_query_worker_SIGNAL();

}
void MainWindow::init_db_module_ready_connect_mainWindow_SLOT(){

    connect(this,SIGNAL(save_uuid_flag_and_quit_SIGNAL(QList<QVariantList >,bool)),
            db_object, SLOT(save_uuid_flag_slot(QList<QVariantList> ,bool)));
    connect(this,SIGNAL(get_uuid_SIGNAL()),
            db_object,SLOT(get_table_uuid_slot()));
    connect(this,SIGNAL(merge_db_SIGNAL()),
            db_object,SLOT(merge_db_slot()));

    connect(this,SIGNAL(db_module_quit_SIGNAL()),
            db_object, SLOT(quit_slot()));

    connect(db_object,SIGNAL(update_mount_state_SIGNAL()),
            this, SLOT(refresh_table_uuid_mount_state_slot()));
    connect(db_object,SIGNAL(update_table_uuid_from_db_SIGNAL(QList<QVariantList>)),
            this, SLOT(refresh_table_uuid_from_db_slot(QList<QVariantList>)));

    connect(this,SIGNAL(update_db_SIGNAL(QList<QStringList>)),
            db_object,SLOT(update_db_slot(QList<QStringList>)));

    // update progressbar signal  : _on_db_progress_update

    connect(db_object,SIGNAL(update_progress_SIGNAL(long,long,QString)),
            this, SLOT(_on_db_progress_update(long,long,QString)));
    connect(db_object->insert_db_thread,SIGNAL(update_progress_SIGNAL(long,long,QString)),
            this, SLOT(_on_db_progress_update(long,long,QString)));

    connect(db_object->insert_db_thread,SIGNAL(show_statusbar_warning_msg_SIGNAL(QString)),
            this, SLOT(show_statusbar_warning_msg_slot(QString)));


    emit init_db_start_timer_SIGNAL();

    connect(this,SIGNAL(send_query_to_worker_SIGNAL(int,QList<QStringList>,QString)),
                 query_worker,     SLOT(distribute_new_query_SLOT(int,QList<QStringList>,QString))   );

//    for (int i=0; i< query_worker->thread_pool_list.length();i++)
//        connect(query_worker->thread_pool_list.at(i), SIGNAL(add_row_to_model_SIGNAL(int,QList<QList<QStandardItem*> >)),
//                this, SLOT(_on_model_receive_new_row(int,QList<QList<QStandardItem*> >)));

    for (int i=0; i< query_worker->thread_pool_list.length();i++)
    {
        connect(query_worker->thread_pool_list.at(i), SIGNAL(add_row_to_model_by_qvariant_SIGNAL(int,QList<QList<QVariant> >)),
                this, SLOT(_on_model_receive_new_row(int,QList<QList<QVariant> >)));
//        connect(query_worker->thread_pool_list.at(i), SIGNAL(update_progress_SIGNAL(int,int)),
//                this, SLOT(_on_update_progress_bar(int,int)));
    }
    connect(query_worker, SIGNAL(update_progress_SIGNAL(int,int)),
            this, SLOT(_on_update_progress_bar(int,int)));
}




MainWindow::~MainWindow()
{
    delete ui;
}
void MainWindow::closeEvent(QCloseEvent *event){

    // TODO: send closing message
    QSettings settings(QSettings::IniFormat,QSettings::UserScope,
                       ORGANIZATION_NAME,ALLICATION_NAME);

    QList<QVariantList> uuid_list;
    for (int row=0; row< ui->tableWidget_uuid->rowCount(); row++)
    {
        QVariantList tmp;
        QVariant uuid = ui->tableWidget_uuid->item(row,UUID_HEADER.uuid)->data(Qt::DisplayRole);
        QVariant included = ui->tableWidget_uuid->item(row, UUID_HEADER.included)->data(Qt::CheckStateRole) ;
        //== QtCore.Qt.Checked
        QVariant updatable = ui->tableWidget_uuid->item(row, UUID_HEADER.updatable)->data(Qt::CheckStateRole);
        //== QtCore.Qt.Checked
        QVariant alias = ui->tableWidget_uuid->item(row, UUID_HEADER.alias)->data(Qt::DisplayRole);
        tmp << uuid<<included<<updatable<<alias;
        uuid_list<<tmp;
    }
    emit save_uuid_flag_and_quit_SIGNAL(uuid_list, True);

    emit db_module_quit_SIGNAL();
    emit query_worker_module_quit_SIGNAL();

    qDebug()<<"db_update_thread send quit";
    db_update_thread.quit();
    qDebug()<<"query_worker_thread send quit";
    query_worker_thread.quit();

    qDebug()<<"db_update_thread wait";
    db_update_thread.wait();
    qDebug()<<"db_update_thread closed";

    qDebug()<<"query_worker_thread wait";
    query_worker_thread.wait();
    qDebug()<<"query_worker_thread closed";

    qDebug()<<"delete db_object;";
    delete db_object;
     qDebug()<<"query_worker";
    delete query_worker;

    // TODO: fix
    /*
     * query_worker_thread closed
        QObject::killTimer: Timers cannot be stopped from another thread
        QObject::~QObject: Timers cannot be stopped from another thread
        QObject::killTimer: Timers cannot be stopped from another thread
        QObject::~QObject: Timers cannot be stopped from another thread
        db_update_thread.isRunning(); false
     */


    //     //delete db_update_thread;
    qDebug()<<"db_update_thread.isRunning();" << db_update_thread.isRunning();
    qDebug()<<"db_update_thread.isFinished()" << db_update_thread.isFinished();

    //return;

    qDebug() << "MainWindow::closeEvent";
    // TODO : self.distribute_query_thread.quit()


    settings.setValue("Excluded_UUID", EXCLUDED_UUID);
    settings.setValue("Excluded_UUID_Visible", ui->actionShow_All->isChecked());

    QList<int> width_list_result;
    for (int i=0; i<model->columnCount();i++){
        width_list_result.append(ui->tableView->columnWidth(i));
    }
    settings.beginWriteArray("Column_width_of_reslut_list");
    for(int i=0;i< width_list_result.length();i++)
    {
        settings.setArrayIndex(i);settings.setValue("width", width_list_result[i]);
    }
    settings.endArray();

    QList<int> width_list_uuid;
    for (int i=0; i<ui->tableWidget_uuid->columnCount();i++){
        width_list_uuid.append(ui->tableWidget_uuid->columnWidth(i));
    }


    // https://stackoverflow.com/questions/2452893/save-qlistint-to-qsettings
    // settings.setValue("Column_width_of_reslut_list", QVariant::fromValue(width_list_result));
    // NOT WORK ...
 //   qDebug()<<  "  width_list_uuid:"<<width_list_uuid;

//    qRegisterMetaTypeStreamOperators<QList<int>>("QList<int>");
//    settings.setValue("Column_width_of_uuid_list", QVariant::fromValue(width_list_uuid));
    settings.beginWriteArray("Column_width_of_uuid_list");
    for(int i=0;i< width_list_uuid.length();i++)
    {
        settings.setArrayIndex(i);settings.setValue("width", width_list_uuid[i]);
    }
    settings.endArray();

    settings.setValue("Main_Window/Show_Search_Setting_Panel", ui->dockWidget_search_settings->isVisible());

    settings.setValue("Main_Window/x", this->x());
    settings.setValue("Main_Window/y", this->y());
    settings.setValue("Main_Window/width", this->width());
    settings.setValue("Main_Window/height", this->height());

    //    QRectF screen_size = QRectF(QDesktopWidget().screenGeometry(QDesktopWidget().primaryScreen()));
    //    x = screen_size.x() + screen_size.width();
    //    y = screen_size.y() + screen_size.height();

    // event.accept()

    restore_statusbar_timer->stop();
    lazy_query_timer->stop();
    lazy_sort_timer->stop();
    hide_tooltip_timer->stop();
    delete restore_statusbar_timer;
    delete lazy_query_timer;
    delete lazy_sort_timer;
    delete hide_tooltip_timer;

    settings.setValue("Main_Window/DOCK_LOCATIONS", this->saveState());

    QWidget::closeEvent(event);


}









void MainWindow::_restore_statusbar_style(){
    ui->statusBar->setStyleSheet("QStatusBar{}");
}


void MainWindow::__init_connect_menu_action(){


    ui->actionChange_excluded_folders->setStatusTip(QCoreApplication::translate("statusbar","Exclude folders from indexing."));
    connect(ui->actionChange_excluded_folders,SIGNAL(triggered(bool)),
            SLOT(_show_dialog_change_excluded_folders()));
    connect(ui->actionChange_excluded_folders,SIGNAL(hovered()),
            SLOT(_show_tooltips_change_excluded_folders()));

    connect(ui->actionEnable_C_MFT_parser, SIGNAL(triggered(bool)),
            SLOT(_toggle_C_MFT_parser(bool)));

    QSettings settings(QSettings::IniFormat,QSettings::UserScope,
                       ORGANIZATION_NAME,ALLICATION_NAME);

    USE_MFT_PARSER_CPP = settings.value("Use_CPP_MFT_parser",  True).toBool();
    ui->actionEnable_C_MFT_parser->setChecked(USE_MFT_PARSER_CPP);
    connect(ui->actionEnable_C_MFT_parser, SIGNAL(triggered(bool)),
            this,SLOT(_toggle_use_MFT_parser(bool)));

    USE_MFT_PARSER = settings.value("Use_MFT_parser", True).toBool();
    ui->actionUse_MFT_parser->setChecked(USE_MFT_PARSER);
    ui->actionEnable_C_MFT_parser->setEnabled(USE_MFT_PARSER);


    connect(ui->actionAbout, &QAction::triggered,
            this, &MainWindow::_show_dialog_about);


    connect(ui->actionAbout_Qt, &QAction::triggered,
            this, &MainWindow::_show_dialog_about_qt);

    connect(ui->actionOpen_Project_Homepage, SIGNAL(triggered(bool)),
            this, SLOT(_about_open_homepage()));

    connect(ui->actionLatest_Version, SIGNAL(triggered(bool)),
            this, SLOT(_about_open_latest_version()));
    connect(ui->actionAdvanced_settings, SIGNAL(triggered(bool)),
            this, SLOT(_show_dialog_advanced_setting()));

    connect(ui->actionOpen_setting_path, SIGNAL(triggered(bool)),
            this, SLOT(_open_setting_path()));

    connect(ui->actionOpen_db_path, SIGNAL(triggered(bool)),
            this, SLOT(_open_db_path()));

    connect(ui->actionOpen_temp_db_path, SIGNAL(triggered(bool)),
            this, SLOT(_open_temp_db_path()));

    connect(ui->actionLanguage_Auto, SIGNAL(triggered(bool)),
            this, SLOT(change_language_auto()));
    connect(ui->actionLanguage_English, SIGNAL(triggered(bool)),
            this, SLOT(change_language_English()));
    connect(ui->actionLanguage_Simplified_Chinese, SIGNAL(triggered(bool)),
            this, SLOT(change_language_zh_CN()));


    ui->comboBox_search->installEventFilter(this);
    ui->comboBox_search->lineEdit()->installEventFilter(this);
//    this->installEventFilter(this);
//    ui->dockWidget_result->installEventFilter(this);

}






void MainWindow::action_uuid_show_all(bool checked){
    for(int row=0; row< ui->tableWidget_uuid->rowCount(); row++)
    {
        if (checked)
            ui->tableWidget_uuid->setRowHidden(row,false);
        else{
            QString uuid = ui->tableWidget_uuid->item(row,
                                                      UUID_HEADER.uuid)->text();
            if (EXCLUDED_UUID.contains(uuid))
                ui->tableWidget_uuid->setRowHidden(row, true);
        }
    }
};
void MainWindow::action_uuid_show_uuid(){
    foreach (QTableWidgetItem  * item, ui->tableWidget_uuid->selectedItems()) {
        item->setForeground(Qt::black);
        QFont temp_font = item->font();
        temp_font.setItalic(false);
        item->setFont(temp_font);
        if (item->column() == UUID_HEADER.uuid)
            if (EXCLUDED_UUID.contains(item->text()))
                EXCLUDED_UUID.removeAll(item->text());
    }
}

void MainWindow::action_uuid_hide_uuid(){
    foreach (QTableWidgetItem  * item, ui->tableWidget_uuid->selectedItems()) {
        item->setForeground(Qt::gray);
        QFont temp_font = item->font();
        temp_font.setItalic(true);
        item->setFont(temp_font);
        if (item->column() == UUID_HEADER.uuid)
        {
            QString uuid = item->text();
            EXCLUDED_UUID.append(uuid);
            if (! ui->actionShow_All->isChecked())
                ui->tableWidget_uuid->setRowHidden(item->row(),true);
        }
    }
}
void MainWindow::action_uuid_check_included(){
    foreach(const QTableWidgetSelectionRange & i,  ui->tableWidget_uuid->selectedRanges())
    {
        for(int row = i.topRow(); row<= i.bottomRow(); row++)
        {
            ui->tableWidget_uuid->item(row,UUID_HEADER.included)->setCheckState(Qt::Checked);
        }
    }
}
void MainWindow::action_uuid_uncheck_included(){
    foreach(const QTableWidgetSelectionRange & i,  ui->tableWidget_uuid->selectedRanges())
    {
        for(int row = i.topRow(); row<= i.bottomRow(); row++)
        {
            ui->tableWidget_uuid->item(row,UUID_HEADER.included)->setCheckState(Qt::Unchecked);
        }
    }
}
void MainWindow::action_uuid_check_updatable(){
    foreach(const QTableWidgetSelectionRange & i,  ui->tableWidget_uuid->selectedRanges())
    {
        for(int row = i.topRow(); row<= i.bottomRow(); row++)
        {
            ui->tableWidget_uuid->item(row,UUID_HEADER.updatable)->setCheckState(Qt::Checked);
        }
    }
}

void MainWindow::action_uuid_uncheck_updatable(){
    foreach(const QTableWidgetSelectionRange & i,  ui->tableWidget_uuid->selectedRanges())
    {
        for(int row = i.topRow(); row<= i.bottomRow(); row++)
        {
            ui->tableWidget_uuid->item(row,UUID_HEADER.updatable)->setCheckState(Qt::Unchecked);
        }
    }
}

void MainWindow::_on_push_button_clicked(){

       qDebug()<< "_on_push_button_clicked ";
};



//    void MainWindow::on_table_header_clicked();
//    void MainWindow::on_table_uuid_itemChanged();




void MainWindow::_on_tableview_double_clicked(QModelIndex index ){
    int row = index.row();
    if (index.column()== DB_HEADER.Filename)
    {
        QString filename =  model->item(row, DB_HEADER.Filename)->data(HACKED_QT_EDITROLE).toString();
        QString path   =  model->item(row, DB_HEADER.Path)->data(HACKED_QT_EDITROLE).toString();
        QString fullpath = path + QDir::separator() + filename;
        QDesktopServices::openUrl(QUrl::fromLocalFile(fullpath));
    }
    else if (index.column()== DB_HEADER.Path)
    {
        QString path   =  model->item(row, DB_HEADER.Path)->data(HACKED_QT_EDITROLE).toString();
        QDesktopServices::openUrl(QUrl::fromLocalFile(path));
    }


};



void MainWindow::_on_tableWidget_uuid_context_menu_requested(QPoint ){
    QPoint point = QCursor::pos();
    tableWidget_uuid_menu->exec(point);
}



void MainWindow::show_statusbar_warning_msg_slot(QString msg){
    //        if msg == 'UNIQUE constraint failed: UUID.uuid':
    //          msg += translate('statusbar','Duplicate UUID found.')
    ui->statusBar->setStyleSheet("QStatusBar{color:red;font-weight:bold;}");
    ui->statusBar->showMessage(msg, 8000);
    restore_statusbar_timer->setInterval(8000);
    restore_statusbar_timer->start();
    //QApplication::processEvents();
};






