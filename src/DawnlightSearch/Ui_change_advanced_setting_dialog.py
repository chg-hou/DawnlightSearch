from __future__ import absolute_import

from DawnlightSearch._Global_Qt_import import *

# import app_recource_rc

# from Ui_Ui_advanced_setting_dialog import Ui_Dialog as EditSettingDialog_base_class
import os
EditSettingDialog_base_class, _ = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "Ui_advanced_setting_dialog.ui"))
# EditSettingDialog_base_class, _ = uic.loadUiType("Ui_advanced_setting_dialog.ui")
class EditSettingDialog(QDialog, EditSettingDialog_base_class):

    def __init__(self, ORGANIZATION_NAME, ALLICATION_NAME, DATABASE_FILE_NAME, TEMP_DB_NAME, parent=None):
        self.ORGANIZATION_NAME = ORGANIZATION_NAME
        self.ALLICATION_NAME = ALLICATION_NAME

        super(self.__class__, self).__init__(parent)
        self.setupUi(self)

        settings = QSettings(QSettings.IniFormat, QSettings.UserScope, self.ORGANIZATION_NAME, self.ALLICATION_NAME)
        print settings.fileName()
        # print settings.value('Query_Chunk_Size', type=int, defaultValue=10000)

        self.spinBox_label_query_chunk_size.setValue(
            settings.value('Query_Chunk_Size', type=int, defaultValue=10000)
        )
        self.spinBox_model_max_items.setValue(
            settings.value('Max_Items_in_List', type=int, defaultValue=3000)
        )
        self.spinBox_query_limit.setValue(
            settings.value('Query_limit', type=int, defaultValue=100)
        )
        self.lineEdit_Database_File_Name.setText(DATABASE_FILE_NAME)
        self.lineEdit_Temp_Database_File_Name.setText(TEMP_DB_NAME)
        self.lineEdit_Database_File_Name.textEdited.connect(self.on_lineEdit_Database_File_Name_edited)
        self.lineEdit_Temp_Database_File_Name.textEdited.connect(self.on_Temp_lineEdit_Database_File_Name_edited)

        self.toolButton_Database_File_Name.released.connect(self.on_change_Database_File)
        self.toolButton_Temp_Database_File_Name.released.connect(self.on_change_Temp_Database_File)

    @pyqtSlot(str)
    def on_lineEdit_Database_File_Name_edited(self,path):
        if os.path.exists(os.path.dirname(path)):
            self.lineEdit_Database_File_Name.setStyleSheet(
                "");
        else:
            self.lineEdit_Database_File_Name.setStyleSheet(
                "QLineEdit { color: red;  }")

    @pyqtSlot(str)
    def on_Temp_lineEdit_Database_File_Name_edited(self, path):
        if os.path.exists(os.path.dirname(path)):
            self.lineEdit_Temp_Database_File_Name.setStyleSheet(
                "");
        else:
            self.lineEdit_Temp_Database_File_Name.setStyleSheet(
                "QLineEdit { color: red;  }");
    @pyqtSlot()
    def on_change_Database_File(self):
        folder = str(QFileDialog.getExistingDirectory(self, "Select Directory of Database File",
                                                      os.path.dirname(self.lineEdit_Database_File_Name.text())))
        if folder:
            filename = os.path.basename(self.lineEdit_Database_File_Name.text())
            self.lineEdit_Database_File_Name.setText(os.path.join(folder, filename))

    @pyqtSlot()
    def on_change_Temp_Database_File(self):
        folder = str(QFileDialog.getExistingDirectory(self, "Select Directory of Temp Database File",
                                                      os.path.dirname(self.lineEdit_Temp_Database_File_Name.text())))
        if folder:
            filename = os.path.basename(self.lineEdit_Temp_Database_File_Name.text())
            self.lineEdit_Temp_Database_File_Name.setText(os.path.join(folder, filename))

    def _getSettings(self):
        pass
        self.spinBox_label_query_chunk_size.value()
        return self.spinBox_label_query_chunk_size.value()

    # static method to create the dialog and return (date, time, accepted)
    @staticmethod
    def getSetting(ORGANIZATION_NAME, ALLICATION_NAME, DATABASE_FILE_NAME, TEMP_DB_NAME, parent=None):
        dialog = EditSettingDialog(ORGANIZATION_NAME, ALLICATION_NAME, DATABASE_FILE_NAME, TEMP_DB_NAME, parent=parent)
        result = dialog.exec_()
        new_settings = dialog._getSettings()
        # print dialog.spinBox_label_query_chunk_size.value(), dialog.spinBox_model_max_items.value(), result
        if result == QDialog.Accepted:
            settings = QSettings(QSettings.IniFormat, QSettings.UserScope,
                                 dialog.ORGANIZATION_NAME, dialog.ALLICATION_NAME)
            settings.setValue('Query_Chunk_Size', dialog.spinBox_label_query_chunk_size.value())
            settings.setValue('Max_Items_in_List', dialog.spinBox_model_max_items.value())
            settings.setValue('Query_limit', dialog.spinBox_query_limit.value())

            settings.setValue('Database_File_Name',         dialog.lineEdit_Database_File_Name.text())
            settings.setValue('Temp_Database_File_Name',    dialog.lineEdit_Temp_Database_File_Name.text())
            settings.sync()
        return (new_settings, result == QDialog.Accepted)

if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    ui = EditSettingDialog()
    ui.setupUi(Dialog)
    Dialog.show()
    sys.exit(app.exec_())

