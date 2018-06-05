#include "MainWindow.h"
#include "ui_Ui_mainwindow.h"

#include "ui_change_advanced_setting_dialog.h"
#include "ui_change_excluded_folder_dialog.h"

void MainWindow::_on_toolbutton_casesensitive_toggled(bool checked){
    _Former_search_text = "";
    CASE_SENSTITIVE = checked;
    _on_lineedit_text_changed(lineEdit_search->text());

    QSettings settings(QSettings::IniFormat,QSettings::UserScope,
                       ORGANIZATION_NAME,ALLICATION_NAME);
    settings.setValue("Search/Case_Sensitive",CASE_SENSTITIVE);
    settings.sync();
}

void MainWindow::_on_match_option_changed(bool){
    if(ui->radioButton_1->isChecked())
        MATCH_OPTION = 1;
    else if (ui->radioButton_2->isChecked())
        MATCH_OPTION = 2;
    else if (ui->radioButton_3->isChecked())
        MATCH_OPTION = 3;
    else if (ui->radioButton_4->isChecked())
        MATCH_OPTION = 4;
    else if (ui->radioButton_5->isChecked())
        MATCH_OPTION = 5;
    QSettings settings(QSettings::IniFormat,QSettings::UserScope,
                       ORGANIZATION_NAME,ALLICATION_NAME);
    settings.setValue("Search/Match_Mode",MATCH_OPTION);
    settings.sync();
}

void  MainWindow::_open_setting_path(){
    QSettings settings(QSettings::IniFormat,QSettings::UserScope,
                       ORGANIZATION_NAME,ALLICATION_NAME);
    QDesktopServices::openUrl(QUrl::fromLocalFile(QFileInfo(settings.fileName()).path()));
}

void  MainWindow:: _open_db_path(){
    QDesktopServices::openUrl(QUrl::fromLocalFile(QFileInfo(DATABASE_FILE_NAME).path()));
}

void  MainWindow::_open_temp_db_path(){
    QDesktopServices::openUrl(QUrl::fromLocalFile(QFileInfo(TEMP_DB_NAME).path()));
}


void  MainWindow::_show_dialog_about(bool ){
    QMessageBox().about(this,"About Dawnlight Search", COPYRIGHT);
}

void  MainWindow::_show_dialog_about_qt(){
    QMessageBox().aboutQt(this,"About Qt");
}
void  MainWindow::_about_open_homepage(){
    QDesktopServices::openUrl(QUrl("https://github.com/chg-hou/DawnlightSearch"));
}
void  MainWindow::_about_open_latest_version(){

    QDesktopServices::openUrl(QUrl("https://github.com/chg-hou/DawnlightSearch/wiki/Latest-Version"));
}

void  MainWindow::_show_dialog_advanced_setting(){
    bool ok = Dialog_Advanced_Setting::getSettings();
    if (ok)
    {
        QSettings settings(QSettings::IniFormat,QSettings::UserScope,
                           ORGANIZATION_NAME,ALLICATION_NAME);
        lazy_query_timer->setInterval(settings.value("Start_Querying_after_Typing_Finished",
                                                     50).toInt()
                                      );
        lazy_sort_timer->setInterval(settings.value("Restor_Sort_after_New_Row_Inserted",
                                                    100).toInt()
                                     );
    }
}

void MainWindow::_hide_tooltip_slot(){
    QToolTip::hideText();
}
void MainWindow::_show_tooltips_change_excluded_folders(){
    QSettings settings(QSettings::IniFormat,QSettings::UserScope,
                       ORGANIZATION_NAME,ALLICATION_NAME);
    QStringList excluded_folders(settings.value("Excluded_folders",{}).toStringList());

    QToolTip::showText(QCursor::pos(),  excluded_folders.join("\n") );
    hide_tooltip_timer->start();

}

void MainWindow::_show_dialog_change_excluded_folders(){
    QSettings settings(QSettings::IniFormat,QSettings::UserScope,
                       ORGANIZATION_NAME,ALLICATION_NAME);
    QSet<QString> excluded_folders(settings.value("Excluded_folders",{}).toStringList().toSet());

    QPair<bool, QStringList> rsts = Dialog_Exclued_Folder::getFolders( excluded_folders.toList(), this);
    if (rsts.first)
    {
        settings.setValue("Excluded_folders" , rsts.second );
        settings.sync();
    }

}


void MainWindow::retranslate_whole_ui()
{
    ui->retranslateUi(this);
    {
        QStringList DB_HEADER_LABEL_tr;
        for(const QString & str: DB_HEADER_LABEL){
            std::string s2 = str.toStdString();
            const char * c3 = s2.c_str();
            DB_HEADER_LABEL_tr<<QCoreApplication::translate("ui",c3);
        }
        model->setHorizontalHeaderLabels(DB_HEADER_LABEL_tr);
    }
    {
        QStringList UUID_HEADER_LABEL_tr;
        for(const QString & str: UUID_HEADER_LABEL){
            std::string s2 = str.toStdString();
            const char * c3 = s2.c_str();
            UUID_HEADER_LABEL_tr<<QCoreApplication::translate("ui",c3);
        }
        ui->tableWidget_uuid->setHorizontalHeaderLabels(UUID_HEADER_LABEL_tr);
    }

}

// TODO: clean up
void  MainWindow::change_language_auto(){

    QTranslator translator;
    QString lang = QLocale::system().name();

    QString lang_path = ":/lang/"+ lang+ ".qm";
    if (!QFile::exists(lang_path))
    {
        qDebug()<<"lang file missing: " + lang_path;
        translator.load(lang_path);
        QCoreApplication * app = QCoreApplication::instance();
        app->installTranslator(&translator);
    }
    retranslate_whole_ui();
    QSettings settings(QSettings::IniFormat,QSettings::UserScope,
                       ORGANIZATION_NAME,ALLICATION_NAME);
    settings.setValue("Language/language", "auto");

}

void  MainWindow::_change_language(QString lang){
    QTranslator translator;
    QString lang_path = ":/lang/"+ lang+ ".qm";
    translator.load(lang_path);
    QCoreApplication * app = QCoreApplication::instance();
    app->installTranslator(&translator);
    retranslate_whole_ui();
    QSettings settings(QSettings::IniFormat,QSettings::UserScope,
                       ORGANIZATION_NAME,ALLICATION_NAME);
    settings.setValue("Language/language", lang);
}

void  MainWindow::change_language_English(){
    QTranslator translator;
    QString lang_path = "";
    translator.load(lang_path);
    QCoreApplication * app = QCoreApplication::instance();
    app->installTranslator(&translator); // ?
    app->removeTranslator(&translator);
    retranslate_whole_ui();
    QSettings settings(QSettings::IniFormat,QSettings::UserScope,
                       ORGANIZATION_NAME,ALLICATION_NAME);
    settings.setValue("Language/language", "en_US");
};
void  MainWindow::change_language_zh_CN(){
    _change_language("zh_CN");
}



void MainWindow::_toggle_use_MFT_parser(bool enable_MFT_parser){
    USE_MFT_PARSER  = enable_MFT_parser;
    QSettings settings(QSettings::IniFormat,QSettings::UserScope,
                       ORGANIZATION_NAME,ALLICATION_NAME);
    settings.setValue("Use_MFT_parser",USE_MFT_PARSER);
    ui->actionEnable_C_MFT_parser->setEnabled(USE_MFT_PARSER);
    settings.sync();
}

void MainWindow::_toggle_C_MFT_parser(bool enable_C_MFT_parser){
    USE_MFT_PARSER_CPP = enable_C_MFT_parser;
    QSettings settings(QSettings::IniFormat,QSettings::UserScope,
                       ORGANIZATION_NAME,ALLICATION_NAME);
    settings.setValue("Use_CPP_MFT_parser",USE_MFT_PARSER_CPP);
    settings.sync();
}
