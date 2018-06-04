#ifndef UI_CHANGE_EXCLUDED_FOLDER_DIALOG_H
#define UI_CHANGE_EXCLUDED_FOLDER_DIALOG_H

#include "ui_Ui_edit_exclued_folder.h"

#include <QSettings>
#include <QFileDialog>

#include "globals.h"

namespace Ui {
class Dialog_Exclued_Folder;
}
class Dialog_Exclued_Folder: public QDialog, public Ui_Dialog_Exclued_Folder
    {
    Q_OBJECT

public:
    Dialog_Exclued_Folder(QStringList folder_list,  QWidget *parent = 0);

//    QStringList folder_list;

    static QPair<bool, QStringList> getFolders(QStringList, QWidget * parent = 0);
    QStringList __getFolders();

public slots:
    void action_add_one_folder();
    void action_add_open_folder();
    void action_remove_folders();



};


#endif // UI_CHANGE_EXCLUDED_FOLDER_DIALOG_H
