from __future__ import absolute_import

from DawnlightSearch._Global_Qt_import import *
# from Ui_edit_exclued_folder import Ui_Dialog
import os

# EditFolderDialog_base_class, _ = uic.loadUiType(
#     os.path.join(os.path.dirname(os.path.abspath(__file__)), "Ui_edit_exclued_folder.ui"))
EditFolderDialog_base_class, _ = uic.loadUiType("Ui_edit_exclued_folder.ui")


class EditFolderDialog(QDialog, EditFolderDialog_base_class):
    def __init__(self, folder_list, parent=None):
        super(self.__class__, self).__init__(parent)
        self.setupUi(self)
        self.folder_list = folder_list
        for folder in folder_list:
            a = QListWidgetItem()
            a.setText(folder)
            a.setFlags(a.flags() | QtCore.Qt.ItemIsEditable)
            self.folder_listWidget.addItem(a)

        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        self.add_one_folder.released.connect(self.action_add_one_folder)
        self.add_open_folder.released.connect(self.action_add_open_folder)
        self.remove_folders.released.connect(self.action_remove_folders)

    def _getFolders(self):
        folder_list = []
        for row in range(self.folder_listWidget.count()):
            item = self.folder_listWidget.item(row)
            folder_list.append(item.text())
        return folder_list

    def action_add_one_folder(self):
        a = QListWidgetItem()
        a.setFlags(a.flags() | QtCore.Qt.ItemIsEditable)
        self.folder_listWidget.addItem(a)
        index = self.folder_listWidget.indexFromItem(a)
        self.folder_listWidget.clearSelection()
        a.setSelected(True)
        self.folder_listWidget.edit(index)

    def action_add_open_folder(self):
        folder = str(QFileDialog.getExistingDirectory(self, QCoreApplication.translate('dialog',"Select Directory to Add")))
        if folder:
            a = QListWidgetItem()
            a.setText(folder)
            a.setFlags(a.flags() | QtCore.Qt.ItemIsEditable)
            self.folder_listWidget.addItem(a)

    def action_remove_folders(self):
        for SelectedItem in self.folder_listWidget.selectedItems():
            self.folder_listWidget.takeItem(self.folder_listWidget.row(SelectedItem))

    # static method to create the dialog and return (date, time, accepted)
    @staticmethod
    def getFolders(folder_list, parent=None):
        dialog = EditFolderDialog(folder_list, parent=parent)
        result = dialog.exec_()
        folders = dialog._getFolders()
        return (folders, result == QDialog.Accepted)


if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    ui = DateDialog_test()
    ui.setupUi(Dialog)
    Dialog.show()
    sys.exit(app.exec_())
