#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import os
import sys
import time

if __name__ == "__main__" and __package__ is None:
    # https://github.com/arruda/relative_import_example

    # print os.path.dirname(sys.argv[0])
    # print os.path.dirname(os.path.abspath(__file__))
    # os.chdir(os.path.dirname(os.path.abspath(__file__)))

    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.sys.path.insert(1, parent_dir)

    mod = __import__('DawnlightSearch')
    sys.modules["DawnlightSearch"] = mod
    __package__ = 'DawnlightSearch'

from ._Global_logger import *

from .UI_delegate.listview_delegate import *
from .DB_Builder.update_db_module import Update_DB_Thread
from .QueryWorker.query_thread import DistributeQueryWorker

from .Ui_change_advanced_setting_dialog import EditSettingDialog
from .Ui_change_excluded_folder_dialog import EditFolderDialog
from .DB_Builder.sys_blk_devices import SystemDevices

# ini db path
try:
    _tmp_settings = QSettings(QSettings.IniFormat, QSettings.UserScope, ORGANIZATION_NAME, ALLICATION_NAME)
    _tmp_settings.setValue("History/last_run", time.time())
    del _tmp_settings
except:
    pass

MainWindow_base_class, _ = uic.loadUiType("Ui_mainwindow.ui")


# from .ui.mainwindows_base import MainWindow_base_class

class AppDawnlightSearch(QMainWindow, MainWindow_base_class):
    send_query_to_worker_SIGNAL = QtCore.pyqtSignal(int, list, str, list, QMainWindow)
    update_db_SIGNAL = QtCore.pyqtSignal(list)
    update_uuid_SIGNAL = QtCore.pyqtSignal(list)
    get_uuid_SIGNAL = QtCore.pyqtSignal(list)
    merge_db_SIGNAL = QtCore.pyqtSignal()

    def __init__(self):
        # super(MyApp, self).__init__()
        super(self.__class__, self).__init__()
        self.setupUi(self)

        # http://stackoverflow.com/questions/8923562/getting-data-from-selected-item-in-qlistview
        # self.model = QtSql.QSqlTableModel(self)
        # self.model.setTable("tableView")
        # self.model.setEditStrategy(2)
        # self.model.select()

        self.progressBar = QtWidgets.QProgressBar()
        self.progressBar.setRange(0, 10000)
        self.progressBar.setValue(400)

        self.statusBar.addPermanentWidget(self.progressBar)
        self.progressBar.show()
        self.progressBar.setVisible(False)

        self.pushButton.clicked.connect(self.on_push_button_clicked)
        self.pushButton_2.clicked.connect(self.refresh_table_uuid_mount_state_slot)

        # self.pushButton_updatedb.clicked.connect(self.on_push_button_updatedb_clicked)
        # self.pushButton_stopupdatedb.clicked.connect(self.on_push_button_stopupdatedb_clicked)
        self.actionUpdatedb.triggered.connect(self.on_push_button_updatedb_clicked)
        self.actionStop_Updating.triggered.connect(self.on_push_button_stopupdatedb_clicked)

        self._Former_search_text = ""

        self.lazy_query_timer = QtCore.QTimer(self)
        self.lazy_query_timer.setSingleShot(True)
        self.lazy_query_timer.timeout.connect(self.update_query_result)
        self.lazy_query_timer.setInterval(2000 * 0)

        self.hide_tooltip_timer = QtCore.QTimer(self)
        self.hide_tooltip_timer.setSingleShot(True)
        self.hide_tooltip_timer.timeout.connect(self._hide_tooltip_slot)
        self.hide_tooltip_timer.setInterval(2000)

        self.restore_statusbar_timer = QtCore.QTimer(self)
        self.restore_statusbar_timer.setSingleShot(True)
        self.restore_statusbar_timer.timeout.connect(self._restore_statusbar_style)
        self.restore_statusbar_timer.setInterval(2000)

        self.refresh_mount_state_timer = QtCore.QTimer(self)
        self.refresh_mount_state_timer.setSingleShot(False)
        self.refresh_mount_state_timer.timeout.connect(self.refresh_table_uuid_mount_state_slot)
        self.mount_state_timestamp = 0

        self.Query_Text_ID_list = [1]  # hack: make the ID accessible from other threads
        self.Query_Model_ID = 0

        self.elapsedtimer = QtCore.QElapsedTimer()

        desktop = QtWidgets.QDesktopWidget()
        screen_size = QtCore.QRectF(desktop.screenGeometry(desktop.primaryScreen()))
        screen_w = screen_size.x() + screen_size.width()
        screen_h = screen_size.y() + screen_size.height()

        settings = QSettings(QSettings.IniFormat, QSettings.UserScope, ORGANIZATION_NAME, ALLICATION_NAME)
        x = settings.value("Main_Window/x", type=int, defaultValue=screen_w / 4)
        y = settings.value("Main_Window/y", type=int, defaultValue=screen_h / 4)
        w = settings.value("Main_Window/width", type=int, defaultValue=-1)
        h = settings.value("Main_Window/height", type=int, defaultValue=-1)

        self.refresh_mount_state_timer.setInterval(
            settings.value('Mount_State_Update_Interval', type=int, defaultValue=3000))

        if w > 0:
            self.resize(w, h)
        self.move(x, y)

        self.__init_connect_menu_action()
        # MainCon.cur.execute("select (?),(?),md5(?), md5(?) ", ("Filename","Path","Filename","Path"))
        # print MainCon.cur.fetchone()

        # self.Submit.clicked.connect(self.dbinput)
        # treeview style:  https://joekuan.wordpress.com/2015/10/02/styling-qt-qtreeview-with-css/

        self.lineEdit_search = self.comboBox_search.lineEdit()
        self.comboBox_search.lineEdit().textChanged.connect(self.on_lineedit_text_changed)
        # self.comboBox_search.lineEdit().installEventFilter(self)
        self.comboBox_search.installEventFilter(self)

    def eventFilter(self, source, event):
        if source is self.comboBox_search.lineEdit() or \
                        source is self.comboBox_search:
            # http://doc.qt.io/qt-5/qevent.html
            if (event.type() == QtCore.QEvent.FocusOut):
                print "focus"
                self.comboBox_search.lineEdit().returnPressed.emit()
        return QtWidgets.QWidget.eventFilter(self, source, event)

    def __init_connect_menu_action(self):

        self.actionChange_excluded_folders.setStatusTip('Exclude folders from indexing.')
        self.actionChange_excluded_folders.setToolTip("folder1")
        self.actionChange_excluded_folders.triggered.connect(self._show_dialog_change_excluded_folders)
        self.actionChange_excluded_folders.hovered.connect(self._show_tooltips_change_excluded_folders)

        self.actionEnable_C_MFT_parser.toggled.connect(self._toggle_C_MFT_parser)
        settings = QSettings(QSettings.IniFormat, QSettings.UserScope, ORGANIZATION_NAME, ALLICATION_NAME)
        GlobalVar.USE_MFT_PARSER_CPP = settings.value('Use_CPP_MFT_parser', type=bool, defaultValue=True)
        self.actionEnable_C_MFT_parser.setChecked(GlobalVar.USE_MFT_PARSER_CPP)

        self.actionUse_MFT_parser.triggered.connect(self._toggle_use_MFT_parser)
        GlobalVar.USE_MFT_PARSER = settings.value('Use_MFT_parser', type=bool, defaultValue=True)
        self.actionUse_MFT_parser.setChecked(GlobalVar.USE_MFT_PARSER)
        self.actionEnable_C_MFT_parser.setEnabled(GlobalVar.USE_MFT_PARSER)

        self.actionAbout.setStatusTip('About...')
        self.actionAbout.triggered.connect(self._show_dialog_about)

        self.actionAbout_Qt.setStatusTip('About Qt...')
        self.actionAbout_Qt.triggered.connect(self._show_dialog_about_qt)

        self.actionAdvanced_settings.triggered.connect(self._show_dialog_advanced_setting)

        self.actionOpen_setting_path.triggered.connect(self._open_setting_path)
        self.actionOpen_db_path.triggered.connect(self._open_db_path)
        self.actionOpen_temp_db_path.triggered.connect(self._open_temp_db_path)

    def ini_after_show(self):
        logger.info('ini subthread.')
        self.ini_subthread()
        logger.info('ini table.')
        self.ini_table()
        logger.info('ini done.')

        settings = QSettings(QSettings.IniFormat, QSettings.UserScope, ORGANIZATION_NAME, ALLICATION_NAME)
        if (settings.value("DOCK_LOCATIONS")):
            try:
                self.restoreState(settings.value("DOCK_LOCATIONS"))
            except Exception as e:
                logger.error('Failt to restore dock states.')

    def ini_subthread(self):
        # Calling heavy-work function through fun() and signal-slot, will block gui event loop.
        # Only thread.run solve.
        logger.info('ini_subthread 1')
        update_db_Thread = Update_DB_Thread(mainwindows=self, parent=self)
        logger.info('ini_subthread 2')
        self.update_db_SIGNAL.connect(update_db_Thread.update_db_slot, QtCore.Qt.QueuedConnection)
        self.update_uuid_SIGNAL.connect(update_db_Thread.update_uuid_slot, QtCore.Qt.QueuedConnection)
        self.get_uuid_SIGNAL.connect(update_db_Thread.get_table_uuid_slot, QtCore.Qt.QueuedConnection)
        self.merge_db_SIGNAL.connect(update_db_Thread.merge_db_slot, QtCore.Qt.QueuedConnection)

        update_db_Thread.start()
        self.update_db_Thread = update_db_Thread

        workerThread = QtCore.QThread()
        worker = DistributeQueryWorker(None,
                                       target_slot=self.on_model_receive_new_row,
                                       progress_slot=self.on_update_progress_bar,
                                       Query_Text_ID_list=self.Query_Text_ID_list)
        worker.moveToThread(
            workerThread)  # TODO: No help. Heavy work will also block gui event loop. Only thread.run solve.
        self.send_query_to_worker_SIGNAL.connect(worker.distribute_new_query)

        workerThread.start()
        self.distribute_query_thread = workerThread
        self.distribute_query_worker = worker

    def ini_table(self):
        self.build_table_model()
        # self.build_table_model_uuid()
        self.build_table_widget_uuid()
        # self.tableView.setModel(self.model)

        HTMLDelegate = HTMLDelegate_VC_HL
        # HTMLDelegate = HTMLDelegate_VU_HL
        self.tableView.setItemDelegateForColumn(0, HTMLDelegate())
        # self.tableView.setItemDelegateForColumn(2, FileSizeDelegate())

        # self.tableView.setModel(self.proxy)
        self.tableView.setModel(self.model)
        self.tableView.horizontalHeader().setSectionsMovable(True)
        self.tableView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tableView.customContextMenuRequested.connect(self.on_tableview_context_menu_requested)
        self.tableView.doubleClicked.connect(self.on_tableview_double_clicked)
        self.tableView.verticalHeader().hide()

        self.tableview_menu = QtWidgets.QMenu(self)
        # self.tableView.horizontalHeader().restoreGeometry()
        self.tableView.setSortingEnabled(1)

        # self.tableView_uuid.setModel(self.model_uuid)
        # self.tableView_uuid.horizontalHeader().setSectionsMovable(True)
        # self.tableView_uuid.resizeColumnsToContents()
        self.tableWidget_uuid.horizontalHeader().setSectionsMovable(True)
        # self.tableWidget_uuid.resizeColumnsToContents()

        settings = QSettings(QSettings.IniFormat, QSettings.UserScope, ORGANIZATION_NAME, ALLICATION_NAME)
        width_list_result = settings.value("Column_width_of_reslut_list", type=int, defaultValue=[])
        width_list_uuid = settings.value("Column_width_of_uuid_list", type=int, defaultValue=[])
        try:
            for i, width in enumerate(width_list_result):
                self.tableView.setColumnWidth(i, width)
            for i, width in enumerate(width_list_uuid):
                self.tableWidget_uuid.setColumnWidth(i, width)
        except Exception as e:
            logger.error(e.message)

    def _show_dialog_about(self):
        print "About dialog..."
        msg = QtWidgets.QMessageBox()
        # msg.setIcon()
        msg.about(self, "aaa", 'bbb')

    def _open_setting_path(self):
        self._open_file_or_folder(os.path.dirname(
            QSettings(QSettings.IniFormat, QSettings.UserScope, ORGANIZATION_NAME, ALLICATION_NAME).fileName()
        ))

    def _open_db_path(self):
        self._open_file_or_folder(os.path.dirname(DATABASE_FILE_NAME))

    def _open_temp_db_path(self):
        self._open_file_or_folder(os.path.dirname(TEMP_DB_NAME))

    def _show_dialog_about_qt(self):
        msgBox = QtWidgets.QMessageBox()
        msgBox.aboutQt(self, 'cccc')

    @pyqtSlot()
    def _hide_tooltip_slot(self):
        QtWidgets.QToolTip.hideText()

    def _show_tooltips_change_excluded_folders(self, *avg):
        settings = QSettings(QSettings.IniFormat, QSettings.UserScope, ORGANIZATION_NAME, ALLICATION_NAME)
        excluded_folders = settings.value('Excluded_folders', type=str)

        # str1 = str(time.time())
        QtWidgets.QToolTip.showText(QtGui.QCursor.pos(), "\n".join(excluded_folders))
        # self.hide_tooltip_timer.setInterval(2000)
        self.hide_tooltip_timer.start()
        # print avg

    def _show_dialog_change_excluded_folders(self):

        settings = QSettings(QSettings.IniFormat, QSettings.UserScope, ORGANIZATION_NAME, ALLICATION_NAME)
        excluded_folders = settings.value('Excluded_folders', type=str)

        folder_list, ok = EditFolderDialog.getFolders(excluded_folders, parent=self)

        logger.info("Excluded folders updated.")
        logger.info("{}  {}".format(folder_list, ok))
        if ok:
            folder_list = list(set(folder_list))
            folder_list.sort()
            logger.info("Setting file path:" + settings.fileName())
            settings.setValue('Excluded_folders', folder_list)
            settings.sync()

    def _show_dialog_advanced_setting(self):

        new_settings, ok = EditSettingDialog.getSetting(ORGANIZATION_NAME, ALLICATION_NAME,
                                                        DATABASE_FILE_NAME, TEMP_DB_NAME,
                                                        parent=self)
        if ok:
            settings = QSettings(QSettings.IniFormat, QSettings.UserScope, ORGANIZATION_NAME, ALLICATION_NAME)
            GlobalVar.QUERY_CHUNK_SIZE = settings.value('Query_Chunk_Size', type=int, defaultValue=10000)
            GlobalVar.MODEL_MAX_ITEMS = settings.value('Max_Items_in_List', type=int, defaultValue=3000)
            GlobalVar.QUERY_LIMIT = settings.value('Query_limit', type=int, defaultValue=100)
            self.refresh_mount_state_timer.setInterval(
                settings.value('Mount_State_Update_Interval', type=int, defaultValue=3000))

            logger.info(
                "Advanced Setting updated. " + str(GlobalVar.QUERY_CHUNK_SIZE) + " " + str(GlobalVar.MODEL_MAX_ITEMS))
            logger.info("{}  {}".format(new_settings, ok))

    def _toggle_use_MFT_parser(self, enable_MFT_parser):
        logger.info("toggle_use_MFT_parser: " + str(enable_MFT_parser))
        GlobalVar.USE_MFT_PARSER = enable_MFT_parser
        settings = QSettings(QSettings.IniFormat, QSettings.UserScope, ORGANIZATION_NAME, ALLICATION_NAME)
        settings.setValue('Use_MFT_parser', enable_MFT_parser)
        self.actionEnable_C_MFT_parser.setEnabled(enable_MFT_parser)
        settings.sync()

    def _toggle_C_MFT_parser(self, enable_C_MFT_parser):
        logger.info("toggle_C_MFT_parser: " + str(enable_C_MFT_parser))
        GlobalVar.USE_MFT_PARSER_CPP = enable_C_MFT_parser
        settings = QSettings(QSettings.IniFormat, QSettings.UserScope, ORGANIZATION_NAME, ALLICATION_NAME)
        settings.setValue('Use_CPP_MFT_parser', enable_C_MFT_parser)
        settings.sync()

    def print_clipboard(self):
        print '\n\nclipboard:\n\n'
        cb = QtWidgets.QApplication.clipboard()
        print cb.text(mode=cb.Clipboard)
        md = cb.mimeData(mode=cb.Clipboard)
        print cb.mimeData(mode=cb.Clipboard)
        print md.text()
        print md.html()
        print md.urls()
        print md.imageData()
        print md.colorData()

        if md.urls():
            a = md.urls()[0]
            fun_names = "adjusted authority errorString fileName fragment host password path query resolved scheme toDisplayString toLocalFile url 	userInfo"
            for i in fun_names.split(" "):
                try:
                    print i, ":\t\t", getattr(a, i)()
                except:
                    pass

    @pyqtSlot()
    def on_push_button_clicked(self):

        logger.info('on_push_button_clicked')
        # a = self.saveGeometry()


        self.statusBar.setStyleSheet(
            "QStatusBar{color:red;font-weight:bold;}")

        self.statusBar.showMessage("fgsfdgaf", 3000)
        self.restore_statusbar_timer.setInterval(4000)
        self.restore_statusbar_timer.start()
        for row in range(self.tableWidget_uuid.rowCount()):
            progressbar = self.tableWidget_uuid.cellWidget(row, 10)
            if not progressbar:
                print "empty progress bar"
            else:
                progressbar.hide()
        str1 = str(time.time())
        QtGui.QCursor.pos()

        QtWidgets.QToolTip.showText(QtCore.QPoint(100, 200), str1)

    # @pyqtSlot()
    # def on_push_button_clicked_old(self):
    #     # header_list = ['included', 'path', 'label', 'uuid', 'fstype', 'name',
    #     #                'major_dnum', 'minor_dnum', 'rows', 'updatable']
    #     # h_header = ['', 'Path', 'Label', 'UUID', 'FS type', 'Dev name',
    #     #          '', '', 'rows', 'updatable', 'progress']
    #     self.aa = QtWidgets.QProgressBar()
    #     # self.itemc = QtGui.QStandardItem(self.aa)
    #     self.model_uuid.setItem(0, 9, QtWidgets.QProgressBar())
    #
    #     pass
    #     return
    #     row = []
    #     for idx, col in enumerate(['NAME', 2, 3, 4, 5, 6, 7]):
    #         newitem = QtGui.QStandardItem()
    #         if idx in [0]:
    #             newitem.setData(QtCore.QVariant("aaaa"), QtCore.Qt.DisplayRole)
    #             newitem.setData(QtCore.QVariant("dddd"), HACKED_QT_EDITROLE)
    #
    #         if idx in [2]:
    #             newitem.setData(QtCore.QVariant(col), HACKED_QT_EDITROLE)
    #         if idx in [4, 5, 6]:
    #             newitem.setData(QtCore.QVariant(col), HACKED_QT_EDITROLE)
    #         row.append(newitem)
    #     self.model.appendRow(row)
    #
    #     return
    #     self.print_clipboard()
    #
    #     cb = QtWidgets.QApplication.clipboard()
    #
    #     qurl = QtCore.QUrl().fromLocalFile("/home/cc/Desktop/TeamViewer.desktop")
    #
    #     md = QtCore.QMimeData()
    #     md.setUrls([qurl])
    #     md.setText("/home/cc/Desktop/TeamViewer.desktop")
    #     cb.setMimeData(md, mode=cb.Clipboard)
    #
    #     self.print_clipboard()
    #     # print self.get_search_included_uuid()
    #
    #
    #     # self.qsql_model = QtSql.QSqlQueryModel()
    #     # header_list = self.header_list
    #     # self.qsql_model.setQuery(
    #     #     "select  " + ",".join(header_list) + ' from `c08e276b-45d6-4669-bef3-77260a891c31` WHERE Filename LIKE "%zip"  ')
    #     # self.tableView.setModel(self.qsql_model)
    #     # self.proxy.setSourceModel(self.qsql_model)
    #
    #     # self.model_uuid.clear()
    #     # print self.table_header.sortIndicatorSection()
    #     # print self.table_header.sortIndicatorOrder()
    #     # self.tableView.setSortingEnabled(1)

    @pyqtSlot()
    def on_push_button_updatedb_clicked(self):
        update_path_list = []
        for row in range(self.tableWidget_uuid.rowCount()):
            uuid = self.tableWidget_uuid.item(row, 3).data(QtCore.Qt.DisplayRole)
            path = self.tableWidget_uuid.item(row, 1).data(QtCore.Qt.DisplayRole)
            included = self.tableWidget_uuid.item(row, 0).data(QtCore.Qt.CheckStateRole) \
                       == QtCore.Qt.Checked
            updatable = self.tableWidget_uuid.item(row, 9).data(QtCore.Qt.CheckStateRole) \
                        == QtCore.Qt.Checked
            if not updatable:
                continue
            update_path_list.append({'path': path, 'uuid': uuid})

        # for row in range(self.model_uuid.rowCount()):
        #     uuid = self.model_uuid.index(row, 3).data()
        #     path = self.model_uuid.index(row, 1).data()
        #     included = self.model_uuid.index(row, 0).data(QtCore.Qt.CheckStateRole) \
        #                == QtCore.Qt.Checked
        #     updatable = self.model_uuid.index(row, 9).data(QtCore.Qt.CheckStateRole) \
        #                 == QtCore.Qt.Checked
        #     if not updatable:
        #         continue
        #     update_path_list.append({'path': path, 'uuid': uuid})
        print "Updatedb clicked.", update_path_list
        print "main Thread:", int(QtCore.QThread.currentThreadId())
        self.update_db_SIGNAL.emit(update_path_list)

    @pyqtSlot()
    def on_push_button_stopupdatedb_clicked(self):
        update_path_list = []
        print "Stop Updatedb clicked.", update_path_list
        print "main Thread:", int(QtCore.QThread.currentThreadId())
        self.update_db_SIGNAL.emit(update_path_list)

    @pyqtSlot(int)
    def on_table_header_clicked(self, logicalIndex):
        print 'Header clicked: ', logicalIndex

        # sortIndicatorOrder()
        # sortIndicatorSection()   logical index of the section that has a sort indicator

        # setSortIndicator(int  logicalIndex, Qt::SortOrder order)
        # isSortIndicatorShown(),  setSortIndicatorShown(bool  show)
        # showSection(int logicalIndex)
        # hideSection(int logicalIndex)

        # print self.table_header.sortIndicatorSection()
        # print self.table_header.sortIndicatorOrder()

    @pyqtSlot(QtGui.QStandardItem)
    def on_table_uuid_itemChanged(self, item):
        pass
        # idx = self.model_uuid.indexFromItem(item)
        # if idx.column() == 0:
        #     row = idx.row()
        #     uuid = self.model_uuid.index(row, 3).data()
        #     print "UUID item changed: ", idx.column(), idx.row(), item.checkState(), uuid
        #     MainCon.cur.execute(''' UPDATE  UUID SET included=?
        #             WHERE uuid=? ''',
        #                 (item.checkState()==QtCore.Qt.Checked,uuid))
        #     MainCon.con.commit()

    @pyqtSlot(str)
    def on_lineedit_text_changed(self, text):
        print 'Text changerd.'
        text = self.lineEdit_search.text().strip()
        if self._Former_search_text == text:  # or (not text)
            return
        self._Former_search_text = text
        self.lazy_query_timer.start()

    @pyqtSlot(int, int)
    def on_update_progress_bar(self, remained, total):
        self.progressBar.setRange(0, total)
        self.progressBar.setValue(total - remained)
        if remained == 0:
            self.progressBar.setVisible(False)

    def test_action_slot(self, x):
        print x

    @pyqtSlot(QtCore.QPoint)
    def on_tableview_context_menu_requested(self, point):
        menu = QtWidgets.QMenu(self)
        file_type = self._get_filetype_of_selected()
        filename_list = [x[2] for x in self.get_tableview_selected()]
        icon_filename, app_name, app_tooltip, app_launch_fun, app_launcher = get_default_app(file_type)
        if (not file_type) or (file_type == "folder") or (not app_name):
            menu.addAction("Open", self.on_tableview_context_menu_open)
        else:
            tmp = menu.addAction('''Open with "%s"''' % app_name, partial(app_launch_fun, app_launcher, filename_list))
            tmp.setIcon(get_QIcon_object(icon_filename))
            tmp.setToolTip(app_tooltip)

            open_with_menu_flag = False
            for icon_filename, app_name, app_tooltip, app_launch_fun, app_launcher in get_open_with_app(file_type):
                if not open_with_menu_flag:
                    open_with_menu = menu.addMenu("Open with")
                    open_with_menu_flag = True
                tmp = open_with_menu.addAction('''Open with "%s"''' % app_name,
                                               partial(app_launch_fun, app_launcher, filename_list))
                tmp.setIcon(get_QIcon_object(icon_filename))
                tmp.setToolTip(app_tooltip)

        menu.addAction("Open path", self.on_tableview_context_menu_open_path)
        copy_menu = menu.addMenu("Copy ...")
        copy_menu.addAction("Copy fullpath", self.on_tableview_context_menu_copy_fullpath)
        copy_menu.addAction("Copy filename", self.on_tableview_context_menu_copy_filename)
        copy_menu.addAction("Copy path", self.on_tableview_context_menu_copy_path)
        menu.addSeparator()
        move_to_menu = menu.addMenu("Move to ...")
        move_to_menu.addAction("Browser ...", self.on_tableview_context_menu_move_to)
        # TODO: history
        move_to_menu.addSeparator()
        copy_to_menu = menu.addMenu("Copy to ...")
        copy_to_menu.addAction("Browser ...", self.on_tableview_context_menu_copy_to)
        copy_to_menu.addSeparator()
        menu.addAction("test", self.on_tableview_context_menu_test)
        # https://github.com/hsoft/send2trash
        # tmp = menu.addAction("Move to trash", self.on_tableview_context_menu_move_to_trash)
        # tmp.setIcon(get_QIcon_object('./ui/icon/user-trash.png'))
        tmp = menu.addAction("Delete", self.on_tableview_context_menu_delete)
        tmp.setIcon(get_QIcon_object('./ui/icon/trash-empty.png'))

        # Need GTk3 to use Gtk.AppChooserDialog.new_for_content_type
        # menu.addAction("Open with Other Application...",lambda  *args: pop_select_app_dialog())
        point = QtGui.QCursor.pos()
        menu.exec_(point)

    @pyqtSlot(QtCore.QModelIndex)
    # a = QtCore.QModelIndex()
    def on_tableview_double_clicked(self, index):
        logger.info("Item double clicked: " + str(index))
        row = index.row()
        if index.column() == 0:
            Filename = self.model.data(self.model.index(row, 0), HACKED_QT_EDITROLE)
            Path = self.model.data(self.model.index(row, 1), HACKED_QT_EDITROLE)
            import os
            fullpath = os.path.join(Path, Filename)  # TODO: convert in Windows
        elif index.column() == 1:
            fullpath = self.model.data(self.model.index(row, 1), HACKED_QT_EDITROLE)
        self._open_file_or_folder(fullpath)

    def _get_filetype_of_selected(self):
        file_type_set = set()
        for Filename, Path, fullpath, IsFolder in self.get_tableview_selected():
            if IsFolder:
                return "folder"
            file_type_set.add(get_file_type(Filename, IsFolder))
        if len(file_type_set) != 1:
            return "folder"
        else:
            return file_type_set.pop()

    def get_tableview_selected(self):
        import os
        print self.tableView.SelectRows
        row_set = set()
        for i in self.tableView.selectedIndexes():
            row_set.add(i.row())
        for row in row_set:
            IsFolder = self.model.data(self.model.index(row, 3), HACKED_QT_EDITROLE)
            Filename = self.model.data(self.model.index(row, 0), HACKED_QT_EDITROLE)
            Path = self.model.data(self.model.index(row, 1), HACKED_QT_EDITROLE)

            fullpath = os.path.join(Path, Filename)  # TODO: convert in Windows
            logger.debug('==== Selected : ' + str([Filename, Path, fullpath, int(IsFolder) > 0]))
            yield Filename, Path, fullpath, int(IsFolder) > 0

    @pyqtSlot()
    def on_tableview_context_menu_open(self):
        # print "Open."

        for Filename, Path, fullpath, IsFolder in self.get_tableview_selected():
            logger.debug('Open: ' + fullpath)
            self._open_file_or_folder(fullpath)

    def _open_file_or_folder(self, path):
        import os, subprocess
        if not os.path.exists(path):
            logger.warning("File/path does not exist: " + path)
            msg = "File/path does not exist: " + path
            QtWidgets.QToolTip.showText(QtGui.QCursor.pos(), msg)
            self.statusBar.setStyleSheet(
                "QStatusBar{color:red;font-weight:bold;}")

            self.statusBar.showMessage(msg, 3000)
            self.restore_statusbar_timer.setInterval(3000)
            self.restore_statusbar_timer.start()
            return
        try:
            if sys.platform.startswith('darwin'):
                subprocess.call(('open', path))
            elif os.name == 'nt':
                os.startfile(path)
            elif os.name == 'posix':
                subprocess.call(('xdg-open', path))
        except:
            logger.warning("Cannot open file: %s" % path)

    def _restore_statusbar_style(self):
        self.statusBar.setStyleSheet("QStatusBar{}")

    @pyqtSlot()
    def on_tableview_context_menu_open_path(self):
        print "Open path."
        import os, subprocess
        for Filename, Path, fullpath, IsFolder in self.get_tableview_selected():
            print Path
            if not os.path.exists(Path):    continue
            try:
                if sys.platform.startswith('darwin'):
                    subprocess.call(('open', Path))
                elif os.name == 'nt':
                    os.startfile(Path)
                elif os.name == 'posix':
                    subprocess.call(('xdg-open', Path))
            except:
                print("Cannot open path: %s" % Path)

    @pyqtSlot()
    def on_tableview_context_menu_copy_fullpath(self):
        print "copy fullpath"
        cb = QtWidgets.QApplication.clipboard()
        qurls = []
        paths = []
        md = QtCore.QMimeData()
        for Filename, Path, fullpath, IsFolder in self.get_tableview_selected():
            # if not os.path.exists(Path):    continue
            qurls.append(QtCore.QUrl().fromLocalFile(fullpath))
            paths.append(fullpath)
        md.setUrls(qurls)
        md.setText("\n".join(paths))
        cb.setMimeData(md, mode=cb.Clipboard)

    @pyqtSlot()
    def on_tableview_context_menu_copy_filename(self):
        print "copy filename"
        cb = QtWidgets.QApplication.clipboard()
        paths = []
        md = QtCore.QMimeData()
        for Filename, Path, fullpath, IsFolder in self.get_tableview_selected():
            # if not os.path.exists(Path):    continue
            paths.append(Filename)
        md.setText("\n".join(paths))
        cb.setMimeData(md, mode=cb.Clipboard)

    @pyqtSlot()
    def on_tableview_context_menu_copy_path(self):
        print "copy path"
        cb = QtWidgets.QApplication.clipboard()
        paths = []
        md = QtCore.QMimeData()
        for Filename, Path, fullpath, IsFolder in self.get_tableview_selected():
            # if not os.path.exists(Path):    continue
            paths.append(Path)
        md.setText("\n".join(paths))
        cb.setMimeData(md, mode=cb.Clipboard)

    @pyqtSlot()
    def on_tableview_context_menu_move_to(self):
        # TODO: show process?
        import os, shutil
        des_path = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory (move to)"))
        print "move to", des_path
        if not os.path.exists(des_path):    return
        self.statusBar.showMessage("Moving...")
        for Filename, Path, fullpath, IsFolder in self.get_tableview_selected():
            # if not os.path.exists(Path):    continue
            try:
                shutil.move(fullpath, des_path)
            except:
                print("Fail to move file: %s" % fullpath)
        self.statusBar.showMessage("Done.", 3000)

    @pyqtSlot()
    def on_tableview_context_menu_copy_to(self):
        import os, shutil
        des_path = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory (copy to)"))
        # print "copy to", des_path
        if not os.path.exists(des_path):    return
        self.statusBar.showMessage("Coping...")
        for Filename, Path, fullpath, IsFolder in self.get_tableview_selected():
            # if not os.path.exists(Path):    continue
            try:
                if False and IsFolder:
                    shutil.copy2(fullpath, des_path)
                    # shutil.copytree(fullpath, des_path) # TODO: test this
                else:
                    shutil.copy2(fullpath, des_path)
            except:
                logger.error("Fail to copy file: %s" % fullpath)
        self.statusBar.showMessage("Done.", 3000)

    @pyqtSlot()
    def on_tableview_context_menu_test(self):
        print "test."
        cb = QtWidgets.QApplication.clipboard()
        print cb.text(mode=cb.Clipboard)
        print cb.mimeData(mode=cb.Clipboard)
        # cb.clear(mode=cb.Clipboard)
        # cb.setText("Clipboard Text", mode=cb.Clipboard)
        # print cb.text(mode=cb.Clipboard)

    @pyqtSlot()
    def on_tableview_context_menu_move_to_trash(self):
        reply = QtGui.QMessageBox.question(self, 'Message',
                                           "Are you sure to quit?", QtGui.QMessageBox.Yes |
                                           QtGui.QMessageBox.No, QtGui.QMessageBox.No)

    @pyqtSlot()
    def on_tableview_context_menu_delete(self):
        reply = QMessageBox.question(self, 'Message',
                                     "Are you sure to DELETE?", QMessageBox.Yes |
                                     QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.statusBar.showMessage("Deleting...")

            import shutil
            for Filename, Path, fullpath, IsFolder in self.get_tableview_selected():
                logger.info("Delete: " + fullpath)
                # if not os.path.exists(Path):    continue
                try:
                    if IsFolder:
                        os.removedirs(fullpath)
                    else:
                        os.remove(fullpath)
                except:
                    logger.error("Fail to delete file: %s" % fullpath)
            self.statusBar.showMessage("Done.", 3000)

    @pyqtSlot(int, list)
    def on_model_receive_new_row(self, query_id, insert_row):
        # QApplication.processEvents()
        # self.parent_application.processEvents()
        if query_id < self.Query_Text_ID_list[0]:
            # old query, ignore
            return

        # self.parent_application.processEvents()
        # if self.Query_Model_ID < query_id:
        #     self.Query_Model_ID = query_id
        #     self._clear_model()
        #     # TODO: highlight former selected rows
        row = self.model.rowCount()
        if row < GlobalVar.MODEL_MAX_ITEMS:
            #  method 2
            for col, item in enumerate(insert_row):
                if col > 0:
                    row = insert_row[0].row()
                self.model.setItem(row, col, item)
                #  method 1, XXX, memory leak!
                # self.model.appendRow(insert_row)

    @pyqtSlot(int, int, str)
    def on_db_progress_update(self, num_records, mftsize, uuid_updating):
        # self.update_progress_SIGNAL.emit

        # header_list = ['included', 'path', 'label', 'uuid', 'fstype', 'name',
        #                'major_dnum', 'minor_dnum', 'rows', 'updatable']
        # h_header = ['', 'Path', 'Label', 'UUID', 'FS type', 'Dev name',
        #             '', '', 'rows', 'updatable', 'progress']
        # self.tableWidget_uuid = QtWidgets.QTableWidget()

        logger.debug("DB progress update: " + str([num_records, mftsize, uuid_updating]))
        # self.parent_application.processEvents()

        for row in range(self.tableWidget_uuid.rowCount()):
            uuid = self.tableWidget_uuid.item(row, 3).data(QtCore.Qt.DisplayRole)
            if uuid == uuid_updating:
                progressbar = self.tableWidget_uuid.cellWidget(row, 10)
                if not progressbar:
                    progressbar = QtWidgets.QProgressBar()
                    progressbar.setMaximum(100)
                    self.tableWidget_uuid.setCellWidget(row, 10, progressbar)
                    progressbar.hide()
                # progressbar = QtWidgets.QProgressBar()
                if num_records == -1:
                    progressbar.show()
                    progressbar.setVisible(True)
                    progressbar.setTextVisible(True)
                    progressbar.setMaximum(100)
                    progressbar.setMinimum(0)
                    progressbar.setValue(0)
                    progressbar.setFormat("%p%")
                elif num_records == -2:
                    # Qt bug? even show when resized.
                    # progressbar.setHidden(True)
                    # progressbar.hide()
                    # progressbar.setVisible(False)
                    progressbar.setMaximum(100)
                    progressbar.setMinimum(0)
                    progressbar.setValue(100)
                    # progressbar.setFormat("Done")
                    progressbar.setFormat("Merging...")
                    self.tableWidget_uuid.item(row, 8).setData(1, HACKED_QT_EDITROLE)
                    self.tableWidget_uuid.item(row, 8).setData(1, QtCore.Qt.DisplayRole)
                    self.tableWidget_uuid.item(row, 8).setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
                else:
                    if mftsize < 0:
                        progressbar.setMinimum(0)
                        progressbar.setMaximum(0)
                        progressbar.setFormat(str(num_records))
                    else:
                        progressbar.setFormat("%d/%d  " % (num_records, mftsize) + "%p%")
                        progressbar.setValue(num_records * 100 / mftsize)
                break

        if num_records == -2:
            logger.debug("DB progress update: " + "merge temp db.")
            self.merge_db_SIGNAL.emit()
            progressbar.setFormat("Done")

    def _clear_model(self):
        self.model.setRowCount(0)
        # self.model.clear()    # will clear header too.

    @pyqtSlot()
    def update_query_result(self):
        text = self.lineEdit_search.text().strip()

        cur_query_id_list = self.Query_Text_ID_list
        cur_query_id_list[0] += 1  # TODO: handle overflow
        query_id = cur_query_id_list[0]
        uuid_path_list = self.get_search_included_uuid()

        header_list = self.header_list
        sql_mask = " SELECT " + ",".join(header_list) + ' FROM `%s` '
        sql_mask = sql_mask.replace("Path", '''"%s"||Path''')

        if (len(uuid_path_list) == 0) or (not text):
            self.progressBar.setVisible(False)
            self._clear_model()
            # sql_mask += "LIMIT 200"
            # self.send_query_to_worker_SIGNAL.emit(query_id, uuid_path_list, sql_mask, cur_query_id_list,
            #                                       self)  # (query_id, uuid_path_list, sql_mask, cur_query_id_list)

            return

        sql_where = []
        for i in text.split(' '):
            if i:
                sql_where.append(''' (`Filename` LIKE "%%%%%s%%%%") ''' % i)  # FIXME: ugly sql cmd
        sql_where = " WHERE " + " AND ".join(sql_where)
        sql_mask = sql_mask + sql_where
        # # sql_mask % (path, uuid)
        logger.debug("SQL mask: " + sql_mask)
        # print "SQL mask: " + sql_mask
        self._clear_model()
        self.progressBar.setVisible(True)
        self.progressBar.setValue(0)
        self.send_query_to_worker_SIGNAL.emit(query_id, uuid_path_list, sql_mask, cur_query_id_list,
                                              self)  # (query_id, uuid_path_list, sql_mask, cur_query_id_list)
        # self.distribute_query_worker.distribute_new_query(query_id, uuid_path_list, sql_mask, cur_query_id_list,
        #                                                   self)  # (query_id, uuid_path_list, sql_mask, cur_query_id_list)

    def build_table_model(self):
        self.model = QtGui.QStandardItemModel(self.tableView)
        self.model.setSortRole(HACKED_QT_EDITROLE)
        header_list = ['Filename', 'Path', 'Size', 'IsFolder',
                       'atime', 'mtime', 'ctime']
        self.header_list = header_list
        # self.model.setRowCount(17)
        print len(header_list)
        self.model.setColumnCount(len(header_list))
        self.model.setHorizontalHeaderLabels(header_list)

        self.proxy = QtCore.QSortFilterProxyModel(self)
        self.proxy.setSourceModel(self.model)
        self.proxy.setFilterKeyColumn(
            0)  # The default value is 0. If the value is -1, the keys will be read from all columns.
        # self.proxy.setFilterWildcard("*.zip*")
        # https://deptinfo-ensip.univ-poitiers.fr/ENS/pyside-docs/PySide/QtGui/QSortFilterProxyModel.html
        self.proxy.setDynamicSortFilter(
            True)  # This property holds whether the proxy model is dynamically sorted and filtered whenever the contents of the source model change.
        self.proxy.setFilterRole(HACKED_QT_EDITROLE)

    @pyqtSlot(str)
    def show_statusbar_warning_msg_slot(self, msg):
        QtWidgets.QToolTip.showText(QtGui.QCursor.pos(), msg)
        self.statusBar.setStyleSheet(
            "QStatusBar{color:red;font-weight:bold;}")

        self.statusBar.showMessage(msg, 3000)
        self.restore_statusbar_timer.setInterval(3000)
        self.restore_statusbar_timer.start()

    def build_table_widget_uuid(self):
        header_list = ['included', 'path', 'label', 'uuid', 'fstype', 'name',
                       'major_dnum', 'minor_dnum', 'rows', 'updatable']
        h_header = ['', 'Path', 'Label', 'UUID', 'FS type', 'Dev name',
                    '', '', 'rows', 'updatable', 'progress']
        self.header_list_uuid = header_list
        self.header_name_uuid = h_header
        self.tableWidget_uuid.setColumnCount(len(h_header))
        self.tableWidget_uuid.setHorizontalHeaderLabels(h_header)

        self.get_uuid_SIGNAL.emit(header_list)
        # self.tableWidget_uuid = QtWidgets.QTableWidget()

    @pyqtSlot(list)
    def get_table_widget_uuid_back_slot(self, cur_result_list):
        for query_row in cur_result_list:
            self.tableWidget_uuid.insertRow(self.tableWidget_uuid.rowCount())
            row = self.tableWidget_uuid.rowCount() - 1
            logger.info(str(query_row))
            for idx, col in enumerate(query_row):
                # print col
                if col is None:
                    col = ''
                newitem = QtWidgets.QTableWidgetItem(str(col))  # TODO: set item directly
                if idx in [6, 7]:
                    newitem.setData(HACKED_QT_EDITROLE, QtCore.QVariant(col))  # TODO: check  QtCore.QVariant()
                elif idx in [0]:
                    newitem.setData(HACKED_QT_EDITROLE, '')
                    newitem.setData(QtCore.Qt.DisplayRole, '')
                    if int(col) > 0:
                        newitem.setCheckState(QtCore.Qt.Checked)
                    else:
                        newitem.setCheckState(QtCore.Qt.Unchecked)
                    newitem.setIcon(QtGui.QIcon('./ui/icon/dev-harddisk.png'))
                elif idx in [9]:
                    newitem.setData(HACKED_QT_EDITROLE, '')
                    newitem.setData(QtCore.Qt.DisplayRole, '')
                    if int(col) > 0:
                        newitem.setCheckState(QtCore.Qt.Checked)
                    else:
                        newitem.setCheckState(QtCore.Qt.Unchecked)

                if idx > 3:
                    newitem.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)

                # row.append(newitem)
                self.tableWidget_uuid.setItem(row, idx, newitem)

                # newitem = QtWidgets.QProgressBar()
                # newitem.setMaximum(100)
                # newitem.setValue(40)
                # self.tableWidget_uuid.setCellWidget(row, 10, newitem)
                # progressbar = self.tableWidget_uuid.cellWidget(row, 10)
                # progressbar.hide()

                # set_qicon(row[0], query_row[0], query_row[3])

                # self.model_uuid.appendRow(row)
        self.refresh_mount_state_timer.start()

    def _find_row_of_uuid(self, uuid):
        for row in range(self.tableWidget_uuid.rowCount()):
            if uuid == self.tableWidget_uuid.item(row, 3).data(QtCore.Qt.DisplayRole):
                return row
        return -1

    @pyqtSlot()
    def refresh_table_uuid_mount_state_slot(self):

        if (not SystemDevices.refresh_state()) and \
                (SystemDevices.timestamp == self.mount_state_timestamp):
            logger.debug('Same, will not refresh.')
            return
        deviceDict = SystemDevices.deviceDict
        self.mount_state_timestamp = SystemDevices.timestamp
        for id, device in deviceDict.items():
            uuid = device['uuid']
            row = self._find_row_of_uuid(uuid)
            if row < 0:  # uuid does not exist, insert now row
                self.tableWidget_uuid.insertRow(self.tableWidget_uuid.rowCount())
                row = self.tableWidget_uuid.rowCount() - 1

                newitem = QtWidgets.QTableWidgetItem('')
                newitem.setCheckState(QtCore.Qt.Unchecked)
                self.tableWidget_uuid.setItem(row, 0, newitem)

                newitem = QtWidgets.QTableWidgetItem('')
                newitem.setCheckState(QtCore.Qt.Unchecked)
                self.tableWidget_uuid.setItem(row, 9, newitem)

                newitem = QtWidgets.QTableWidgetItem(device['uuid'])
                newitem.setCheckState(QtCore.Qt.Unchecked)
                self.tableWidget_uuid.setItem(row, 3, newitem)

                for col in [1, 2, 4, 5, 6, 7, 8]:
                    newitem = QtWidgets.QTableWidgetItem(device['uuid'])
                    self.tableWidget_uuid.setItem(row, col, newitem)

            if device['mountpoint']:
                self.tableWidget_uuid.item(row, 0).setIcon(get_QIcon_object('./ui/icon/dev-harddisk.png'))
            else:
                self.tableWidget_uuid.item(row, 0).setIcon(get_QIcon_object('./ui/icon/tab-close-other.png'))
            self.tableWidget_uuid.item(row, 1).setData(QtCore.Qt.DisplayRole, device['mountpoint'])
            self.tableWidget_uuid.item(row, 2).setData(QtCore.Qt.DisplayRole, device['label'])
            self.tableWidget_uuid.item(row, 4).setData(QtCore.Qt.DisplayRole, device['fstype'])
            self.tableWidget_uuid.item(row, 5).setData(QtCore.Qt.DisplayRole, device['name'])

            self.tableWidget_uuid.item(row, 6).setData(QtCore.Qt.DisplayRole, id[0])
            self.tableWidget_uuid.item(row, 7).setData(QtCore.Qt.DisplayRole, id[1])
            self.tableWidget_uuid.item(row, 6).setData(HACKED_QT_EDITROLE, id[0])  # TODO: check  QtCore.QVariant()
            self.tableWidget_uuid.item(row, 7).setData(HACKED_QT_EDITROLE, id[1])
            # QtWidgets.QTableWidgetItem

    def get_search_included_uuid(self):
        r = []
        for row in range(self.tableWidget_uuid.rowCount()):
            included = self.tableWidget_uuid.item(row, 0).data(QtCore.Qt.CheckStateRole) \
                       == QtCore.Qt.Checked
            if not included:
                continue
            uuid = self.tableWidget_uuid.item(row, 3).data(QtCore.Qt.DisplayRole)
            path = self.tableWidget_uuid.item(row, 1).data(QtCore.Qt.DisplayRole)
            # MainCon.cur.execute('''SELECT COALESCE(MAX(rowid),0) FROM `%s` ''' % (uuid))
            # rows = MainCon.cur.fetchall()[0][0]  # max(rowid)
            rows = int(self.tableWidget_uuid.item(row, 8).data(QtCore.Qt.DisplayRole))
            # TODO: move rows into query thread
            r.append({'uuid': uuid, 'path': path, 'rows': rows})
        return r

        # MainCon.cur.execute('''SELECT `uuid`,`path` FROM UUID WHERE (included=1) ''')
        # r = []
        # for c in MainCon.cur.fetchall():
        #     uuid = c[0]
        #     path = c[1]
        #     MainCon.cur.execute('''SELECT COALESCE(MAX(rowid),0) FROM `%s` ''' % (uuid) )
        #     rows = MainCon.cur.fetchall()[0][0]     # max(rowid)
        #     r.append({'uuid':uuid,
        #               'path':path,
        #               'rows':rows})
        # return r

    def closeEvent(self, event):
        print('close')
        self.distribute_query_thread.quit()
        self.update_db_Thread.quit()

        uuid_list = []
        for row in range(self.tableWidget_uuid.rowCount()):
            uuid = self.tableWidget_uuid.item(row, 3).data(QtCore.Qt.DisplayRole)
            included = self.tableWidget_uuid.item(row, 0).data(QtCore.Qt.CheckStateRole) \
                       == QtCore.Qt.Checked
            updatable = self.tableWidget_uuid.item(row, 9).data(QtCore.Qt.CheckStateRole) \
                        == QtCore.Qt.Checked
            logger.info("uuid: %s, included: %s" % (uuid, included))
            # MainCon.cur.execute(''' UPDATE  UUID SET included=?, updatable=?
            #             WHERE uuid=? ''',
            #             (included, updatable, uuid))
            uuid_list.append([uuid, included, updatable])
        self.update_uuid_SIGNAL.emit(uuid_list)

        self.distribute_query_thread.wait()

        # save column width
        width_list_result = []
        width_list_uuid = []
        for i in range(self.model.columnCount()):
            width_list_result.append(self.tableView.columnWidth(i))
        for i in range(self.tableWidget_uuid.columnCount()):
            width_list_uuid.append(self.tableWidget_uuid.columnWidth(i))

        settings = QSettings(QSettings.IniFormat, QSettings.UserScope, ORGANIZATION_NAME, ALLICATION_NAME)
        settings.setValue("Column_width_of_reslut_list", width_list_result)
        settings.setValue("Column_width_of_uuid_list", width_list_uuid)

        # save windows position
        settings.setValue("Main_Window/x", self.x())
        settings.setValue("Main_Window/y", self.y())
        settings.setValue("Main_Window/width", self.width())
        settings.setValue("Main_Window/height", self.height())
        desktop = QtWidgets.QDesktopWidget()
        screen_size = QtCore.QRectF(desktop.screenGeometry(desktop.primaryScreen()))
        x = screen_size.x() + screen_size.width()
        y = screen_size.y() + screen_size.height()

        # event.accept()
        super(self.__class__, self).closeEvent(event)

        settings.setValue("DOCK_LOCATIONS", self.saveState())


if __name__ == '__main__':
    app = QApplication(sys.argv)

    while 1:
        # https://docs.python.org/2/library/sqlite3.html
        try:
            MainCon.con = sqlite3.connect(DATABASE_FILE_NAME, check_same_thread=False, timeout=10)
            MainCon.cur = MainCon.con.cursor()
            break
            # MainCon.con.create_function("md5", 1, md5sum)
        except Exception as e:
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Critical)
            msgBox.setText("Fail to connect to databse:\n%s\n\nError message:\n%s" % (DATABASE_FILE_NAME, e.message))
            msgBox.setInformativeText("Do you want to retry?")
            msgBox.setStandardButtons(QMessageBox.Retry | QMessageBox.Cancel)
            msgBox.setDefaultButton(QMessageBox.Retry)
            ret = msgBox.exec_()
            if (ret != msgBox.Retry):
                sys.exit(0)

    # from .DB_Builder.update_db_module import Update_DB_Thread

    # if not createDBConnection():
    #     sys.exit(1)
    window = AppDawnlightSearch()
    window.show()
    window.ini_after_show()
    exit_code = app.exec_()
    logger.info("Close db.")

    while 1:
        try:
            MainCon.con.commit()
            MainCon.con.close()
            sys.exit(exit_code)
        except Exception as e:
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Critical)
            msgBox.setText("Fail to close databse:\n%s\n\nError message:\n%s" % (DATABASE_FILE_NAME, e.message))
            msgBox.setInformativeText("Do you want to retry?")
            msgBox.setStandardButtons(QMessageBox.Retry | QMessageBox.Cancel)
            msgBox.setDefaultButton(QMessageBox.Retry)
            ret = msgBox.exec_()
            if (ret != msgBox.Retry):
                sys.exit(exit_code)
