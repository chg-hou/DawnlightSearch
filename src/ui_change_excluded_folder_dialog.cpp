#include "ui_change_excluded_folder_dialog.h"

#include <QListWidgetItem>

Dialog_Exclued_Folder::Dialog_Exclued_Folder(QStringList folder_list_in, QWidget *parent ):QDialog(parent)
{
        setupUi(this);
//        folder_list = folder_list_in;
    for(QString folder : folder_list_in)
    {
        QListWidgetItem* a = new QListWidgetItem(folder);
        a->setFlags(a->flags() | Qt::ItemIsEditable);
        folder_listWidget->addItem(a);
    }
    connect(buttons, SIGNAL(accepted()),
            this, SLOT(accept()));
    connect(buttons, SIGNAL(rejected()),
            this, SLOT(reject()));

    connect(this->add_one_folder, SIGNAL(released()),
            this, SLOT(action_add_one_folder()));
    connect(this->add_open_folder, SIGNAL(released()),
            this, SLOT(action_add_open_folder()));
    connect(this->remove_folders, SIGNAL(released()),
            this, SLOT(action_remove_folders()));

}

QStringList Dialog_Exclued_Folder::__getFolders()
{
      QStringList folders;
       for(int row =0; row< folder_listWidget->count(); row++)
       {
           folders<< folder_listWidget->item(row)->text();
       }
       return folders;

}


void Dialog_Exclued_Folder::action_add_one_folder()
{
    QListWidgetItem* a = new QListWidgetItem();
    a->setFlags(a->flags() | Qt::ItemIsEditable);
    folder_listWidget->addItem(a);

    folder_listWidget->clearSelection();
    a->setSelected(true);
    folder_listWidget->editItem(a);

}

void Dialog_Exclued_Folder::action_add_open_folder()
{
    QString folder = QFileDialog::getExistingDirectory(this,
                            QCoreApplication::translate("dialog","Select Directory to Add"));
    if (folder != "")
    {
        QListWidgetItem* a = new QListWidgetItem(folder);
        a->setFlags(a->flags() | Qt::ItemIsEditable);
        folder_listWidget->addItem(a);
    }
}

void Dialog_Exclued_Folder::action_remove_folders()
{
    for(auto SelectedItem: folder_listWidget->selectedItems())
    {
        folder_listWidget->takeItem(folder_listWidget->row(SelectedItem));
    }
}
QPair<bool, QStringList> Dialog_Exclued_Folder::getFolders(QStringList folder_list_in, QWidget *parent)
{
    Dialog_Exclued_Folder dialog(folder_list_in,parent);
    int result = dialog.exec();
    QStringList folders = dialog.__getFolders();
    return QPair<bool, QStringList>({ result == QDialog::Accepted, folders });
}


