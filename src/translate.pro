# https://plashless.wordpress.com/2014/02/01/internationalizing-python-pyqt-apps/
SOURCES += DawnlightSearch/DawnlightSearch_main.py \
		DawnlightSearch/_Global_DawnlightSearch.py \
		DawnlightSearch/_Global_logger.py \
		DawnlightSearch/Ui_change_advanced_setting_dialog.py \
		DawnlightSearch/Ui_change_excluded_folder_dialog.py \
		DawnlightSearch/Ui_advanced_setting_dialog.ui \
		DawnlightSearch/Ui_edit_exclued_folder.ui \
		DawnlightSearch/Ui_mainwindow.ui \
		DawnlightSearch/DB_Builder/sys_blk_devices.py \
		DawnlightSearch/DB_Builder/update_db_module.py 

FORMS       += DawnlightSearch/Ui_mainwindow.ui \
                DawnlightSearch/Ui_edit_exclued_folder.ui \
                DawnlightSearch/Ui_advanced_setting_dialog.ui
		
TRANSLATIONS += translate_zh_CN.ts
