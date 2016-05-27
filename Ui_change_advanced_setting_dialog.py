from __future__ import absolute_import

from DawnlightSearch._Global_Qt_import import *

# import app_recource_rc

# from Ui_advanced_setting_dialog import Ui_Dialog as EditSettingDialog_base_class
import os
EditSettingDialog_base_class, _ = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "Ui_advanced_setting_dialog.ui"))
# EditSettingDialog_base_class, _ = uic.loadUiType("Ui_advanced_setting_dialog.ui")
class EditSettingDialog(QDialog, EditSettingDialog_base_class):

    def __init__(self, ORGANIZATION_NAME, ALLICATION_NAME, parent=None):
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
        # self.spinBox_label_query_chunk_size.setValue(987)

        # print self.spinBox_3.value()
        # self.spinBox_3.setValue(23)
    def _getSettings(self):
        pass
        self.spinBox_label_query_chunk_size.value()
        return self.spinBox_label_query_chunk_size.value()

    # static method to create the dialog and return (date, time, accepted)
    @staticmethod
    def getSetting(ORGANIZATION_NAME, ALLICATION_NAME, parent=None):
        dialog = EditSettingDialog(ORGANIZATION_NAME, ALLICATION_NAME, parent=parent)
        result = dialog.exec_()
        new_settings = dialog._getSettings()
        # print dialog.spinBox_label_query_chunk_size.value(), dialog.spinBox_model_max_items.value(), result
        if result == QDialog.Accepted:
            settings = QSettings(QSettings.IniFormat, QSettings.UserScope,
                                 dialog.ORGANIZATION_NAME, dialog.ALLICATION_NAME)
            settings.setValue('Query_Chunk_Size', dialog.spinBox_label_query_chunk_size.value())
            settings.setValue('Max_Items_in_List', dialog.spinBox_model_max_items.value())

        return (new_settings, result == QDialog.Accepted)

if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    ui = EditSettingDialog()
    ui.setupUi(Dialog)
    Dialog.show()
    sys.exit(app.exec_())

