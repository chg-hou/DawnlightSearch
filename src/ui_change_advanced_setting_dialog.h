#ifndef UI_CHANGE_ADVANCED_SETTING_DIALOG_H
#define UI_CHANGE_ADVANCED_SETTING_DIALOG_H

#include "ui_Ui_advanced_setting_dialog.h"

#include <QSettings>
#include <QFileDialog>

#include "globals.h"

namespace Ui {
class Dialog_Advanced_Setting;
}
class Dialog_Advanced_Setting: public QDialog, public Ui_Dialog_Advanced_Setting
    {
    Q_OBJECT

public:
    Dialog_Advanced_Setting(QWidget *parent = 0);

    static bool getSettings(QWidget * parent = 0);

public slots:
    void _on_lineEdit_Database_File_Name_edited(QString);
    void _on_Temp_lineEdit_Database_File_Name_edited(QString);
    void _on_change_Database_File();
    void _on_change_Temp_Database_File();


};


#endif // UI_CHANGE_ADVANCED_SETTING_DIALOG_H
