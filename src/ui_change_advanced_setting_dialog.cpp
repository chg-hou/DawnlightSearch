#include "ui_change_advanced_setting_dialog.h"
#include <QThread>

Dialog_Advanced_Setting::Dialog_Advanced_Setting(QWidget *parent):QDialog(parent)
{
    setupUi(this);

    QSettings settings(QSettings::IniFormat,QSettings::UserScope,
                       ORGANIZATION_NAME,ALLICATION_NAME);

    this->spinBox_label_query_chunk_size->setValue(
                settings.value("Query_Chunk_Size",10000).toInt());

    this->spinBox_model_max_items->setValue(
                settings.value("Max_Items_in_List",3000).toInt()
                );
    this->spinBox_query_limit->setValue(
                settings.value("Query_limit", 100).toInt()
                );

    this->spinBox_mount_state_update_interval->setValue(
                settings.value("Mount_State_Update_Interval", 3000).toInt()
                );
    this->spinBox_rowid_update_interval->setValue(
                settings.value("Rowid_Update_Interval",3000).toInt()
                );
    this->spinBox_db_update_interval->setValue(
                settings.value("Database_Update_Interval", 1000).toInt()
                );

    this->spinBox_lazy_query_interval->setValue(
                settings.value("Start_Querying_after_Typing_Finished", 50).toInt()
                );

    this->lineEdit_Database_File_Name->setText(DATABASE_FILE_NAME);
    this->lineEdit_Temp_Database_File_Name->setText(TEMP_DB_NAME);
    connect(this->lineEdit_Database_File_Name, SIGNAL(textEdited(QString)),
            this, SLOT(_on_lineEdit_Database_File_Name_edited(QString)));

    connect(this->lineEdit_Temp_Database_File_Name, SIGNAL(textEdited(QString)),
            this, SLOT(_on_Temp_lineEdit_Database_File_Name_edited(QString)));



    connect(this->toolButton_Database_File_Name, SIGNAL(released()),
            this, SLOT(_on_change_Database_File()));

    connect(this->toolButton_Temp_Database_File_Name, SIGNAL(released()),
            this, SLOT(_on_change_Temp_Database_File()));

    this->lineEdit_datetime_format->setText(DATETIME_FORMAT);
    this->checkBox_skip_diff_dev->setChecked(
                settings.value("Database/Skip_Different_Device", True).toBool());
    this->spinBox_restor_sort_interval->setValue(
                settings.value("Restor_Sort_after_New_Row_Inserted", 100).toInt()
                );
    QString unit = settings.value("Size_Unit", "KB").toString();
    QStringList unit_list = {"Auto","B", "KB", "MB", "GB", "TB", "PB"};
    int idx;
    if (!unit_list.contains(unit))
        idx =0 ;
    else
        idx = unit_list.indexOf(unit);

    this->comboBox_size_unit->setCurrentIndex(idx);

    if ( settings.value("Search/Instant_Search", True).toBool())
        this->radioButton_instant_search->setChecked(true);
    else
        this->radioButton_enter_to_search->setChecked(true);

    comboBox_threads_for_querying->clear();
    comboBox_threads_for_querying->addItem(QApplication::translate("dialog","All Cores"));
    for(int i =0; i<QThread::idealThreadCount(); i++)
    {
        comboBox_threads_for_querying->addItem(QString::number(i+1));
    }
    int query_thread = settings.value("Search/Threads", 0).toInt();
    if (query_thread< comboBox_threads_for_querying->count())
        comboBox_threads_for_querying->setCurrentIndex(query_thread);

    checkBox_compress_db_file->setChecked(COMPRESS_DB_FILE);

    lineEdit_ThemeName->setText(settings.value("General/Theme_Name", QIcon::themeName()).toString());
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
    lineEdit_Fallback_ThemeName->setText(settings.value("General/Fallback_Theme_Name", QIcon::fallbackThemeName()).toString());
#else
    // lineEdit_Fallback_ThemeName->setText(settings.value("General/Fallback_Theme_Name", QIcon::themeName()).toString());
    lineEdit_Fallback_ThemeName->setDisabled(true);
#endif

    lineEdit_excluded_mount_path_regex->setText(settings.value("Database/Excluded_Mount_Path_Regex", DEFAULT_EXCLUDED_MOUNT_PATH_RE_STRING).toString());
}



void Dialog_Advanced_Setting::_on_lineEdit_Database_File_Name_edited(QString filename)
{
    QFileInfo path(filename);
    if (QFileInfo::exists(path.path()) && QFileInfo(path.path()).isDir())
        this->lineEdit_Database_File_Name->setStyleSheet("");
    else
        this->lineEdit_Database_File_Name->setStyleSheet("QLineEdit { color: red;  }");
}

void Dialog_Advanced_Setting::_on_Temp_lineEdit_Database_File_Name_edited(QString filename)
{
    QFileInfo path(filename);
    if (QFileInfo::exists(path.path()) && QFileInfo(path.path()).isDir())
        this->lineEdit_Temp_Database_File_Name->setStyleSheet("");
    else
        this->lineEdit_Temp_Database_File_Name->setStyleSheet("QLineEdit { color: red;  }");
}

void Dialog_Advanced_Setting::_on_change_Database_File()
{
   QString filename = QFileDialog::getSaveFileName(this,
                                                      QCoreApplication::translate("dialog","Select Directory of Database File"),
                            this->lineEdit_Database_File_Name->text()
        );
   if (filename!="")
       this->lineEdit_Database_File_Name->setText(filename);

}

void Dialog_Advanced_Setting::_on_change_Temp_Database_File()
{
    QString filename = QFileDialog::getSaveFileName(this,
                                                       QCoreApplication::translate("dialog","Select Directory of Database File"),
                             this->lineEdit_Temp_Database_File_Name->text()
         );
    if (filename!="")
        this->lineEdit_Temp_Database_File_Name->setText(filename);
}
bool Dialog_Advanced_Setting::getSettings(QWidget * parent)
{
    Dialog_Advanced_Setting dialog(parent);
    int result = dialog.exec();

    if (result == QDialog::Accepted)
    {
        QSettings settings(QSettings::IniFormat,QSettings::UserScope,
                           ORGANIZATION_NAME,ALLICATION_NAME);

        QUERY_CHUNK_SIZE = dialog.spinBox_label_query_chunk_size->value();
        settings.setValue("Query_Chunk_Size", dialog.spinBox_label_query_chunk_size->value());

        MODEL_MAX_ITEMS = dialog.spinBox_model_max_items->value();
        settings.setValue("Max_Items_in_List", dialog.spinBox_model_max_items->value());

        QUERY_LIMIT = dialog.spinBox_query_limit->value();
        settings.setValue("Query_limit", dialog.spinBox_query_limit->value());


        settings.setValue("Database_File_Name", dialog.lineEdit_Database_File_Name->text());
        settings.setValue("Temp_Database_File_Name", dialog.lineEdit_Temp_Database_File_Name->text());

        MOUNT_STATE_UPDATE_INTERVAL = dialog.spinBox_mount_state_update_interval->value();
        settings.setValue("Mount_State_Update_Interval", dialog.spinBox_mount_state_update_interval->value());
        ROWID_UPDATE_INTERVAL = dialog.spinBox_rowid_update_interval->value();
        settings.setValue("Rowid_Update_Interval", dialog.spinBox_rowid_update_interval->value());
        DB_UPDATE_INTERVAL = dialog.spinBox_db_update_interval->value();
        settings.setValue("Database_Update_Interval", dialog.spinBox_db_update_interval->value());


        DATETIME_FORMAT = dialog.lineEdit_datetime_format->text();
        settings.setValue("Search/Date_Format",
                          dialog.lineEdit_datetime_format->text());

        SKIP_DIFF_DEV = dialog.checkBox_skip_diff_dev->isChecked();
        settings.setValue("Database/Skip_Different_Device",
                          dialog.checkBox_skip_diff_dev->isChecked());


        QStringList unit_list = {"Auto","B", "KB", "MB", "GB", "TB", "PB"};
        QString unit =  unit_list[dialog.comboBox_size_unit->currentIndex()];
        settings.setValue("Size_Unit",unit);
        SIZE_UNIT = unit;

        QUERY_THREAD_NUMBER = dialog.comboBox_threads_for_querying->currentIndex();
        settings.setValue("Search/Threads", QUERY_THREAD_NUMBER);

        INSTANT_SEARCH = dialog.radioButton_instant_search->isChecked();
        settings.setValue("Search/Instant_Search", dialog.radioButton_instant_search->isChecked());

        settings.setValue("Start_Querying_after_Typing_Finished",dialog.spinBox_lazy_query_interval->value());
        settings.setValue("Restor_Sort_after_New_Row_Inserted", dialog.spinBox_restor_sort_interval->value());

        COMPRESS_DB_FILE = dialog.checkBox_compress_db_file->isChecked();
        settings.setValue("Compress_DB_File", COMPRESS_DB_FILE);

        QString themename = dialog.lineEdit_ThemeName->text();
        QString fallback_themename = dialog.lineEdit_Fallback_ThemeName->text();

        settings.setValue("General/Theme_Name", themename);
        settings.setValue("General/Fallback_Theme_Name", fallback_themename);

        QIcon::setThemeName(themename);
    #if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        QIcon::setFallbackThemeName(fallback_themename);
    #endif

        settings.setValue("Database/Excluded_Mount_Path_Regex", dialog.lineEdit_excluded_mount_path_regex->text());
        EXCLUDED_MOUNT_PATH_RE.setPattern(dialog.lineEdit_excluded_mount_path_regex->text());

        settings.sync();
        return true;
    }
    return false;
}
