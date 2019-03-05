#include "MainWindow.h"
#include "ui_Ui_mainwindow.h"



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

    _Former_search_text = "";
    _on_lineedit_text_changed(lineEdit_search->text());

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

    QStringList DB_HEADER_LABEL_tr;
    for(const QString & str: DB_HEADER_LABEL){
        std::string s2 = str.toStdString();
        const char * c3 = s2.c_str();
        DB_HEADER_LABEL_tr<<QCoreApplication::translate("ui",c3);
    }
    model->setHorizontalHeaderLabels(DB_HEADER_LABEL_tr);

    for(int i=0;i<model->columnCount();i++)
    {
        model->horizontalHeaderItem(i)->setToolTip(
                    model->horizontalHeaderItem(i)->text());
    }
//    model->horizontalHeaderItem(DB_HEADER.IsFolder)->setText("");
//    model->horizontalHeaderItem(DB_HEADER.IsFolder)->setIcon(QIcon::fromTheme("folder"));

    QStringList UUID_HEADER_LABEL_tr;
    for(const QString & str: UUID_HEADER_LABEL){
        std::string s2 = str.toStdString();
        const char * c3 = s2.c_str();
        UUID_HEADER_LABEL_tr<<QCoreApplication::translate("ui",c3);
    }
    ui->tableWidget_uuid->setHorizontalHeaderLabels(UUID_HEADER_LABEL_tr);

    QTableWidgetItem * major_dnum_header, * minor_dnum_header;
    major_dnum_header = ui->tableWidget_uuid->horizontalHeaderItem(UUID_HEADER.major_dnum);
    minor_dnum_header = ui->tableWidget_uuid->horizontalHeaderItem(UUID_HEADER.minor_dnum);

    major_dnum_header->setToolTip(major_dnum_header->text());
    minor_dnum_header->setToolTip(minor_dnum_header->text());

    // 1. copy label to tooltip firstly
    for(int i=0;i<ui->tableWidget_uuid->columnCount();i++)
    {
        ui->tableWidget_uuid->horizontalHeaderItem(i)->setToolTip(
                    ui->tableWidget_uuid->horizontalHeaderItem(i)->text());
    }
    ui->tableWidget_uuid->horizontalHeaderItem(UUID_HEADER.major_dnum)->setText("Ⓜ");
    ui->tableWidget_uuid->horizontalHeaderItem(UUID_HEADER.minor_dnum)->setText("ⓜ");

    // 2. add tr(tooltip) behind
    for(int i=0;i<ui->tableWidget_uuid->columnCount();i++)
    {
        std::string s2 = UUID_HEADER_TOOLTIP[i].toStdString();
        const char * c3 = s2.c_str();
        ui->tableWidget_uuid->horizontalHeaderItem(i)->setToolTip(
                    ui->tableWidget_uuid->horizontalHeaderItem(i)->toolTip() + '\n' +
                    QCoreApplication::translate("ui", c3 )  );
    }
}

// TODO: clean up
void  MainWindow::change_language_auto(){
    _change_language("auto");
}

void  MainWindow::_change_language(QString lang){
    QSettings settings(QSettings::IniFormat,QSettings::UserScope,
                       ORGANIZATION_NAME,ALLICATION_NAME);
    settings.setValue("Language/language", lang);

    if (lang == "auto")
        lang = QLocale::system().name();
    if(!translator.load("translate_"+ lang, ":/lang"))
        qDebug()<<"lang file missing: " + lang;

    QCoreApplication * app = QCoreApplication::instance();
    app->installTranslator(&translator);
    retranslate_whole_ui();
}

void  MainWindow::change_language_nl(){
    _change_language("nl");
}
void  MainWindow::change_language_English(){
    _change_language("en");
}
void  MainWindow::change_language_hu(){
    _change_language("hu");
}
void  MainWindow::change_language_nb_NO(){
    _change_language("nb_NO");
}
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

void MainWindow::_on_menu_view_aboutToShown(){
    ui->actionShowView_Database_Dock->setChecked(ui->dockWidget_uuid->isVisible());
    ui->actionShowView_Search_Dock->setChecked(ui->dockWidget_search->isVisible());
    ui->actionShowView_Search_Settings_Dock->setChecked(ui->dockWidget_search_settings->isVisible());
    ui->actionShowView_SQL_Command_Preview_Dock->setChecked(ui->dockWidget_sqlcmd->isVisible());

    ui->actionShowView_Toolbar->setChecked(ui->mainToolBar->isVisible());
    ui->actionShowView_Toolbar_Advanced_Setting->setChecked(ui->toolBar_2->isVisible());
    ui->actionShowView_Toolbar_Case_Snesitive->setChecked(ui->toolBar->isVisible());
}
//void  MainWindow::_on_actionShowView_Database_Dock_toggled(bool ){
//    ui->dockWidget_uuid->setVisible(!ui->dockWidget_uuid->isVisible());
//}
//void  MainWindow::_on_actionShowView_Search_Dock_toggled(bool ){
//    ui->dockWidget_search->setVisible(!ui->dockWidget_search->isVisible());
//}
//void  MainWindow::_on_actionShowView_Search_Settings_Dock_toggled(bool ){
//    ui->dockWidget_search_settings->setVisible(!ui->dockWidget_search_settings->isVisible());
//}
//void  MainWindow::_on_actionShowView_SQL_Command_Preview_Dock_toggled(bool ){
//    ui->dockWidget_sqlcmd->setVisible(!ui->dockWidget_sqlcmd->isVisible());
//}

//void  MainWindow::_on_actionShowView_Toolbar_toggled(bool ){
//    ui->mainToolBar->setVisible(!ui->mainToolBar->isVisible());
//}
//void  MainWindow::_on_actionShowView_Toolbar_Advanced_Setting_toggled(bool ){
//    ui->toolBar_2->setVisible(!ui->toolBar_2->isVisible());
//}
//void  MainWindow::_on_actionShowView_Toolbar_Case_Snesitive_toggled(bool ){
//    ui->toolBar->setVisible(!ui->toolBar->isVisible());
//}
