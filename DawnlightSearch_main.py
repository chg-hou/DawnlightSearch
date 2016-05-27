#!/usr/bin/env python
# -*- coding: utf-8 -*-


from __future__ import absolute_import

import os
import sqlite3
import sys
import time

if __name__ == "__main__" and __package__ is None:
    # https://github.com/arruda/relative_import_example

    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.sys.path.insert(1, parent_dir)

    mod = __import__('DawnlightSearch')
    sys.modules["DawnlightSearch"] = mod
    __package__ = 'DawnlightSearch'

    print "done"

from ._Global_logger import *
from .UI_delegate.listview_delegate import *
from .update_db_module import Update_DB_Thread

from DawnlightSearch.Ui_change_advanced_setting_dialog import EditSettingDialog
from DawnlightSearch.Ui_change_excluded_folder_dialog import EditFolderDialog

def md5sum(t):
    return t

# db = QtSql.QSqlDatabase.addDatabase('QSQLITE')

con = sqlite3.connect(DATABASE_FILE_NAME, check_same_thread=False)
# https://docs.python.org/2/library/sqlite3.html
con.create_function("md5", 1, md5sum)
cur = con.cursor()



# def createDBConnection():
    # db.setDatabaseName(DATABASE_FILE_NAME)
    # if db.open():
    #     return True
    # else:
    #     print db.lastError().text()
    #     return False



def size_to_str(value, unit='KB'):
    if not value:
        return ''
    suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    if not unit in suffixes:
        unit = None
    try:
        value = int(value)
    except:
        print 'aaa'

    if unit is 'B': return '%d B' % value
    if value == 0 and not (unit is None):
        return '0 B'
    try:
        i = 0
        while (value >= 1024 and i < len(suffixes) - 1) or not (unit is None):
            value /= 1024.
            i += 1
            if unit is suffixes[i]:    break
        f = ('%.2f' % value).rstrip('0').rstrip('.')
        return '%s %s' % (f, suffixes[i])
    except:
        print "***************************** Error in format size: ", value

        return value


class QueryThread(QtCore.QThread):
    add_row_to_model_SIGNAL = QtCore.pyqtSignal(int, list)
    update_progress_SIGNAL = QtCore.pyqtSignal(int, int)

    def __init__(self, mutex, queue_condition, qqueue, Query_Text_ID_list, parent=None):
        super(self.__class__, self).__init__()
        self.mutex = mutex
        self.queue_condition = queue_condition
        self.qqueue = qqueue
        self.Query_Text_ID_list = Query_Text_ID_list
        self.quit_flag = False
        # self.add_row_to_model_SIGNAL = QtCore.pyqtSignal(list)

        # con = QtSql.QSqlDatabase.addDatabase("QSQLITE")
        # con.setDatabaseName(DATABASE_FILE_NAME)
        # if not con.open():
        #     print con.lastError().text()
        con = sqlite3.connect(DATABASE_FILE_NAME, check_same_thread=False)
        cur = con.cursor()

        self.cur = cur
        self.con = con

    def quit_previous_query(self):
        pass
        # TODO: cancel query

    def run(self):
        cur = self.cur
        while (1):
            if self.quit_flag:
                break
            self.mutex.lock()
            self.queue_condition.wait(self.mutex, 1000 * 50)
            # print 'Condition wait:' ,QtCore.QThread.currentThreadId()
            # logger.debug('Condition wait')
            self.mutex.unlock()

            while not self.qqueue.empty():
                # print "Queue not empty: ", QtCore.QThread.currentThreadId()
                # logger.debug('Queue not empty')
                if self.quit_flag:
                    break

                self.mutex.lock()
                if self.qqueue.empty():
                    self.mutex.unlock()
                    continue  # break
                q = self.qqueue.get()
                self.mutex.unlock()

                msg = "Queue get: " + str(q) + '\n\t\t' + "self.Query_Text_ID_list: " + str(self.Query_Text_ID_list)
                logger.debug(msg)
                # print "Queue get: ", QtCore.QThread.currentThreadId()
                # print q
                # print "self.Query_Text_ID_list: ", self.Query_Text_ID_list
                query_id = q['query_id']
                sql_comm = q['sql_comm']
                if (query_id < self.Query_Text_ID_list[0]):
                    continue

                cur.execute(sql_comm)
                for query_row in cur:
                    if self.quit_flag:
                        break
                    if (query_id < self.Query_Text_ID_list[0]):
                        break
                    row = []
                    for idx, col in enumerate(query_row):
                        newitem = QtGui.QStandardItem(str(col))
                        newitem.setData(str(col), HACKED_QT_EDITROLE)
                        if idx in [0]:
                            newitem.setData(str(col), HACKED_QT_EDITROLE)
                        if idx in [2]:
                            newitem.setData(QtCore.QVariant(col), HACKED_QT_EDITROLE)
                        if idx in [4, 5, 6]:
                            newitem.setData(QtCore.QVariant(col), HACKED_QT_EDITROLE)
                        row.append(newitem)
                    self.add_row_to_model_SIGNAL.emit(query_id, row)
                    # self.model.appendRow(row)
                if (not self.quit_flag) and (query_id == self.Query_Text_ID_list[0]):
                    self.update_progress_SIGNAL.emit(self.qqueue.qsize(), q['LEN'])


class DistributeQueryWorker(QtCore.QObject):
    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args)  # , **kwargs
        self.mutex = QtCore.QMutex()
        self.queue_condition = QtCore.QWaitCondition()
        import Queue
        self.qqueue = Queue.Queue()
        # In python, we don't need mutex. Queue is thread-safe.
        self.target_slot = kwargs['target_slot']
        self.update_progress_slot = kwargs['progress_slot']
        self.Query_Text_ID_list = kwargs['Query_Text_ID_list']
        self.thread_no = max(1, QtCore.QThread.idealThreadCount())
        self.thread_pool = [QueryThread(self.mutex, self.queue_condition, self.qqueue, self.Query_Text_ID_list,
                                        parent=self) \
                            for _ in range(self.thread_no)]
        # Single thread
        # self.thread_pool = [QueryThread(self.mutex, self.queue_condition, self.qqueue, self.Query_Text_ID_list) ]
        for thread in self.thread_pool:
            thread.add_row_to_model_SIGNAL.connect(self.target_slot)
            thread.update_progress_SIGNAL.connect(self.update_progress_slot)
            thread.start()

    @pyqtSlot(int, list, str, list, QMainWindow)
    def distribute_new_query(self, query_id, uuid_path_list, sql_mask, cur_query_id_list, ui_thread):
        # print 'distribute_new_query slot received: ', query_id, uuid_path_list, sql_mask, cur_query_id_list, ui_thread
        logger.warning(
            'distribute_new_query slot received: ' + str([query_id, uuid_path_list, sql_mask, cur_query_id_list,
                                                          ui_thread]))
        for thread in self.thread_pool:
            thread.quit_previous_query()

        tmp_mutexlocker =  QtCore.QMutexLocker(self.mutex)
        while not self.qqueue.empty():
            self.qqueue.get()

        tmp_q = []
        for table in uuid_path_list:  # {'uuid':uuid,'path':path,'rows':rows}
            table['path'] = "" if table['path'] == "/" else table['path']  #  avoid "//dir/file"
            sql_comm = sql_mask % (table['path'], table['uuid'])  # path, uuid
            rowid_low = 0
            while rowid_low <= table['rows']:
                rowid_high = rowid_low + QUERY_CHUNK_SIZE
                if "WHERE" in sql_comm.upper():
                    sql_comm_2 = sql_comm + '  AND  (ROWID BETWEEN %s AND %s) ' % (rowid_low, rowid_high)
                else:
                    sql_comm_2 = sql_comm + ' WHERE (ROWID BETWEEN %s AND %s) ' % (rowid_low, rowid_high)
                sql_comm_2 += " LIMIT 100"
                tmp_q.append({'query_id': query_id, 'sql_comm': sql_comm_2})
                rowid_low = rowid_high + 1
        for idx, item in enumerate(tmp_q):
            item['SN'] = idx
            item['LEN'] = len(tmp_q)
            self.qqueue.put(item)
        # ======================
        self.queue_condition.wakeAll()

    def __del__(self):
        for thread in self.thread_pool:
            thread.quit_flag = True
            thread.quit_previous_query()
            thread.quit()
        self.mutex.lock()
        self.queue_condition.wakeAll()
        self.mutex.unlock()
        for thread in self.thread_pool:
            thread.wait()
        s = super(self.__class__, self)
        try:
            s.__del__
        except AttributeError:
            pass
        else:
            s.__del__(self)


# MainWindow_base_class, _ = uic.loadUiType(
#     os.path.join(os.path.dirname(os.path.abspath(__file__)), "./ui/Ui_mainwindow.ui"))
MainWindow_base_class, _ = uic.loadUiType("Ui_mainwindow.ui")
# from .ui.mainwindows_base import MainWindow_base_class
class MyApp(QMainWindow, MainWindow_base_class):
    send_query_to_worker_SIGNAL = QtCore.pyqtSignal(int, list, str, list, QMainWindow)
    update_db_SIGNAL = QtCore.pyqtSignal(list)

    def __init__(self, parent_application):
        # super(MyApp, self).__init__()
        super(self.__class__, self).__init__()
        self.setupUi(self)
        self.parent_application = parent_application
        # self.ui = Ui_MainWindow()
        # self.ui.setupUi(self)
        self.ui = self
        # self.ui.calc_tax_button.clicked.connect(self.CalculateTax)
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

        # Calling heavy-work function through fun() and signal-slot, will block gui event loop.
        # Only thread.run solve.
        update_db_Thread = Update_DB_Thread(mainwindows=self, parent=self)
        self.update_db_SIGNAL.connect(update_db_Thread.update_db_slot, QtCore.Qt.QueuedConnection)
        update_db_Thread.start()
        # TODO:DDDDDDDDD
        self.update_db_Thread = update_db_Thread


        self.build_table_model()
        # self.build_table_model_uuid()
        self.build_table_widget_uuid()
        # self.ui.tableView.setModel(self.model)

        # a = QtWidgets.QTableView()
        # a.horizontalHeader()
        # a.setItemDelegateForColumn(0, HTMLDelegate())
        # self.ui.tableView.setItemDelegateForColumn(0, HTMLDelegate())
        # self.ui.tableView.setItemDelegateForColumn(2, FileSizeDelegate())
        # b=a.horizontalHeader()

        HTMLDelegate = HTMLDelegate_VC_HL
        # HTMLDelegate = HTMLDelegate_VU_HL
        self.ui.tableView.setItemDelegateForColumn(0, HTMLDelegate())

        self.ui.tableView.setModel(self.proxy)
        self.ui.tableView.horizontalHeader().setSectionsMovable(True)
        self.ui.tableView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.ui.tableView.customContextMenuRequested.connect(self.on_tableview_context_menu_requested)
        self.ui.tableView.doubleClicked.connect(self.on_tableview_double_clicked)
        self.ui.tableView.verticalHeader().hide()

        self.tableview_menu = QtWidgets.QMenu(self)
        # self.ui.tableView.horizontalHeader().restoreGeometry()

        # self.ui.tableView_uuid.setModel(self.model_uuid)
        # self.ui.tableView_uuid.horizontalHeader().setSectionsMovable(True)
        # self.ui.tableView_uuid.resizeColumnsToContents()
        self.ui.tableWidget_uuid.horizontalHeader().setSectionsMovable(True)
        # self.ui.tableWidget_uuid.resizeColumnsToContents()

        settings = QSettings(QSettings.IniFormat, QSettings.UserScope, ORGANIZATION_NAME, ALLICATION_NAME)
        width_list_result = settings.value("Column_width_of_reslut_list",type=int, defaultValue = [])
        width_list_uuid = settings.value("Column_width_of_uuid_list", type=int, defaultValue=[])

        for i,width in enumerate(width_list_result):
            self.ui.tableView.setColumnWidth(i, width)
        for i,width in enumerate(width_list_uuid):
            self.ui.tableWidget_uuid.setColumnWidth(i, width)

        # self.model_uuid.itemChanged.connect(self.on_table_uuid_itemChanged)

        # query = QtSql.QSqlQuery()
        # query.exec_("select * from table2")
        # while (query.next()):
        #     id = query.value(0)
        #     name = query.value(1)
        #     country = query.value(2)
        #     #print  (name, country)

        # v = db.driver().handle()

        self.table_v_scrollbar = self.ui.tableView.verticalScrollBar()
        self.table_v_scrollbar.valueChanged.connect(self.on_tableview_vscroll_changed)
        self.table_v_scrollbar.rangeChanged.connect(self.on_tableview_vscroll_rangechanged)
        self.table_v_scrollbar.actionTriggered.connect(self.on_tableview_vscroll_actionTriggered)

        self.table_header = self.ui.tableView.horizontalHeader()
        self.table_header.sectionClicked.connect(self.on_table_header_clicked)
        self.table_header.setSortIndicatorShown(True)

        self.ui.pushButton.clicked.connect(self.on_push_button_clicked)
        self.ui.pushButton_2.clicked.connect(self.refresh_table_model)
        self.ui.pushButton_updatedb.clicked.connect(self.on_push_button_updatedb_clicked)
        self.ui.pushButton_stopupdatedb.clicked.connect(self.on_push_button_stopupdatedb_clicked)

        self._Former_search_text = ""
        self.ui.lineEdit_search.textChanged.connect(self.on_lineedit_text_changed)
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


        self.Query_Text_ID_list = [1]  # hack: make the ID accessible from other threads
        self.Query_Model_ID = 0

        workerThread = QtCore.QThread()
        worker = DistributeQueryWorker(None,
                                       target_slot=self.on_model_receive_new_row,
                                       progress_slot=self.on_update_progress_bar,
                                       Query_Text_ID_list=self.Query_Text_ID_list)
        worker.moveToThread(workerThread)       # TODO: No help. Heavy work will also block gui event loop. Only thread.run solve.
        self.send_query_to_worker_SIGNAL.connect(worker.distribute_new_query)
        workerThread.start()

        self.distribute_query_thread = workerThread
        self.distribute_query_worker = worker

        self.elapsedtimer = QtCore.QElapsedTimer()

        desktop = QtWidgets.QDesktopWidget()
        screen_size = QtCore.QRectF(desktop.screenGeometry(desktop.primaryScreen()))
        screen_w = screen_size.x() + screen_size.width()
        screen_h = screen_size.y() + screen_size.height()

        settings = QSettings(QSettings.IniFormat, QSettings.UserScope, ORGANIZATION_NAME, ALLICATION_NAME)
        x = settings.value("Main_Window/x", type=int, defaultValue= screen_w/4)
        y = settings.value("Main_Window/y", type=int, defaultValue=screen_h/ 4)
        w = settings.value("Main_Window/width", type=int, defaultValue=-1)
        h = settings.value("Main_Window/height", type=int, defaultValue=-1)
        if w > 0:
            self.resize(w, h)
        self.move(x,y)

        self.__init_connect_menu_action()
        # cur.execute("select (?),(?),md5(?), md5(?) ", ("Filename","Path","Filename","Path"))
        # print cur.fetchone()

        # self.ui.Submit.clicked.connect(self.dbinput)
        # treeview style:  https://joekuan.wordpress.com/2015/10/02/styling-qt-qtreeview-with-css/

    def __init_connect_menu_action(self):
        # a= QtWidgets.QAction()
        # a.triggered()
        # a.setToolTip()
        self.ui.actionExit.setStatusTip("Exit application.")
        self.ui.actionExit.triggered.connect(self.close)

        self.ui.actionChange_excluded_folders.setStatusTip('Exclude folders from indexing.')
        self.ui.actionChange_excluded_folders.setToolTip("folder1")
        self.ui.actionChange_excluded_folders.triggered.connect(self._show_dialog_change_excluded_folders)
        self.ui.actionChange_excluded_folders.hovered.connect(self._show_tooltips_change_excluded_folders)

        self.ui.actionEnable_C_MFT_parser.toggled.connect(self._toggle_C_MFT_parser)
        settings = QSettings(QSettings.IniFormat, QSettings.UserScope, ORGANIZATION_NAME, ALLICATION_NAME)
        enable_C_MFT_parser = settings.value('Use_CPP_MFT_parser', type=bool, defaultValue = True)
        self.ui.actionEnable_C_MFT_parser.setChecked(enable_C_MFT_parser)

        self.ui.actionUse_MFT_parser.triggered.connect(self._toggle_use_MFT_parser)
        enable_MFT_parser = settings.value('Use_MFT_parser', type=bool, defaultValue = True)
        self.ui.actionUse_MFT_parser.setChecked(enable_MFT_parser)
        self.ui.actionEnable_C_MFT_parser.setEnabled(enable_MFT_parser)

        self.ui.actionAbout.setStatusTip('About...')
        self.ui.actionAbout.triggered.connect(self._show_dialog_about)

        self.ui.actionAbout_Qt.setStatusTip('About Qt...')
        self.ui.actionAbout_Qt.triggered.connect(self._show_dialog_about_qt)

        self.ui.actionAdvanced_settings.triggered.connect(self._show_dialog_advanced_setting)

        self.ui.actionOpen_setting_db_path.triggered.connect(self._open_setting_db_path)

    def _show_dialog_about(self):
        print "About dialog..."
        msg = QtWidgets.QMessageBox()
        # msg.setIcon()
        msg.about(self,"aaa",'bbb')

    def _open_setting_db_path(self):
        db_path = os.path.dirname(
            QSettings(QSettings.IniFormat, QSettings.UserScope, ORGANIZATION_NAME, ALLICATION_NAME).fileName()
        )
        self._open_file_or_folder(db_path)

    def _show_dialog_about_qt(self):
        msgBox = QtWidgets.QMessageBox()
        msgBox.aboutQt(self,'cccc')

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
        #print avg

    def _show_dialog_change_excluded_folders(self):

        settings = QSettings(QSettings.IniFormat, QSettings.UserScope, ORGANIZATION_NAME, ALLICATION_NAME)
        excluded_folders = settings.value('Excluded_folders', type = str)


        folder_list,  ok = EditFolderDialog.getFolders(excluded_folders, parent=self)

        logger.info("Excluded folders updated.")
        logger.info("{}  {}".format(folder_list,  ok))
        if ok:
            folder_list = list(set(folder_list))
            folder_list.sort()
            logger.info("Setting file path:" + settings.fileName())
            settings.setValue('Excluded_folders', folder_list)
            settings.sync()

    def _show_dialog_advanced_setting(self):

        new_settings, ok = EditSettingDialog.getSetting(ORGANIZATION_NAME, ALLICATION_NAME, parent=self)
        if ok:
            settings = QSettings(QSettings.IniFormat, QSettings.UserScope, ORGANIZATION_NAME, ALLICATION_NAME)
            QUERY_CHUNK_SIZE = settings.value('Query_Chunk_Size', type=int, defaultValue=10000)
            MODEL_MAX_ITEMS = settings.value('Max_Items_in_List', type=int, defaultValue=3000)

            logger.info("Advanced Setting updated. " +str(QUERY_CHUNK_SIZE) +" "+ str(MODEL_MAX_ITEMS) )
            logger.info("{}  {}".format(new_settings, ok))


    def _toggle_use_MFT_parser(self, enable_MFT_parser ):
        logger.info("toggle_use_MFT_parser: " + str(enable_MFT_parser))
        settings = QSettings(QSettings.IniFormat, QSettings.UserScope, ORGANIZATION_NAME, ALLICATION_NAME)
        settings.setValue('Use_MFT_parser', enable_MFT_parser)
        self.ui.actionEnable_C_MFT_parser.setEnabled(enable_MFT_parser)
        settings.sync()

    def _toggle_C_MFT_parser(self, enable_C_MFT_parser):
        logger.info("toggle_C_MFT_parser: "+ str( enable_C_MFT_parser))
        settings = QSettings(QSettings.IniFormat, QSettings.UserScope, ORGANIZATION_NAME, ALLICATION_NAME)
        settings.setValue('Use_CPP_MFT_parser', enable_C_MFT_parser)
        settings.sync()


    def update_item_icon(self):
        # done by HTMLDelegate_VC_HL.update_item_icon

        start_ = self.table_v_scrollbar.value()
        end_ = min(start_ + self.table_v_scrollbar.pageStep(), self.proxy.rowCount() - 1)

        new_highlight_words = self.ui.lineEdit_search.text().strip()

        m = self.ui.tableView.model()
        for row in range(start_, end_ + 1):
            itemdata = m.itemData(m.index(row, 0))  # TODO: check proxy, hidden row
            filename = m.data(m.index(row, 0), HACKED_QT_EDITROLE)

            old_highlight_words = m.data(m.index(row, 0), QtCore.Qt.AccessibleDescriptionRole)
            # print old_highlight_words, type(old_highlight_words)

            if (new_highlight_words != old_highlight_words):
                m.setData(m.index(row, 0), new_highlight_words, QtCore.Qt.AccessibleDescriptionRole)
                new_display_role = filename.replace("<", "&lt;").replace(">", "&gt;").replace("&", "&amp;")
                # TODO: verify html escape
                for new_word in new_highlight_words.split():
                    if not new_word:
                        continue
                    new_display_role = new_display_role.replace(new_word, "<b>" + new_word + "</b>")
                m.setData(m.index(row, 0), new_display_role, QtCore.Qt.DisplayRole)
                # m.setData(m.index(row, 0), QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter, QtCore.Qt.TextAlignmentRole)

            # http://doc.qt.io/qt-5/qt.html#ItemDataRole-enum
            # data(const QModelIndex &index, int role = Qt::DisplayRole) const = 0
            # itemData(const QModelIndex &index) const
            if (QtCore.Qt.DecorationRole in itemdata or not (filename)):
                continue
            else:
                m.setData(m.index(row, 0), filename, QtCore.Qt.ToolTipRole)
                m.setData(m.index(row, 0), filename, QtCore.Qt.AccessibleDescriptionRole)

                path = m.data(m.index(row, 1), HACKED_QT_EDITROLE)
                m.setData(m.index(row, 1), path, QtCore.Qt.ToolTipRole)

                isPath = m.data(m.index(row, 3)) == '1'
                print 'Item filename:', filename
                newicon = build_qicon(filename, isPath, size=32)
                itemdata[QtCore.Qt.DecorationRole] = newicon
                import random
                order = random.randint(0, 100)
                print order
                itemdata[QtCore.Qt.InitialSortOrderRole] = order
                # itemdata[QtCore.Qt.TextAlignmentRole] = QtCore.Qt.AlignRight
                m.setItemData(m.index(row, 0), itemdata)
                print 'Updated icon row:', row

                size_data = m.data(m.index(row, 2), HACKED_QT_EDITROLE)
                size_data = size_to_str(size_data)
                print 'size_data: ', size_data
                m.setData(m.index(row, 2), size_data, QtCore.Qt.DisplayRole)
                m.setData(m.index(row, 2), QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter, QtCore.Qt.TextAlignmentRole)

                for col in [4, 5, 6]:
                    date = QtCore.QDateTime()
                    date.setTime_t(int(m.data(m.index(row, col), HACKED_QT_EDITROLE)))
                    m.setData(m.index(row, col), date.toString(), QtCore.Qt.DisplayRole)

    @pyqtSlot(int)
    def on_tableview_vscroll_changed(self, x):
        # a = self.table_v_scrollbar
        # print  a.minimum(), a.value(), a.maximum(), a.pageStep()
        # value : minimum <= value <= maximum.
        # pageStep
        # print('Scroll changed to (%s).' % (x))
        self.update_item_icon()

    @pyqtSlot(int, int)
    def on_tableview_vscroll_rangechanged(self, min_, max_):
        # a = self.table_v_scrollbar
        # print  a.minimum, a.value, a.maximum, a.pageStep
        # print('Scroll range changed to (%s, %s).' % (min_,max_))
        self.update_item_icon()

    @pyqtSlot(int)
    def on_tableview_vscroll_actionTriggered(self, action):
        # http://doc.qt.io/qt-4.8/qabstractslider.html#actionTriggered
        # QAbstractSlider::SliderNoAction
        # print('Scroll action (%s).' % (action))
        pass

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


        self.statusBar().setStyleSheet(
            "QStatusBar{color:red;font-weight:bold;}")

        self.statusBar().showMessage("fgsfdgaf", 3000)
        self.restore_statusbar_timer.setInterval(4000)
        self.restore_statusbar_timer.start()
        for row in range(self.ui.tableWidget_uuid.rowCount()):
            progressbar = self.ui.tableWidget_uuid.cellWidget(row, 10)
            if not progressbar:
                print "empty progress bar"
            else:
                progressbar.hide()
        str1 = str(time.time())
        QtGui.QCursor.pos()

        QtWidgets.QToolTip.showText(QtCore.QPoint(100, 200), str1)

    @pyqtSlot()
    def on_push_button_clicked_old(self):
        # header_list = ['included', 'path', 'label', 'uuid', 'fstype', 'name',
        #                'major_dnum', 'minor_dnum', 'indexed', 'updatable']
        # h_header = ['', 'Path', 'Label', 'UUID', 'FS type', 'Dev name',
        #          '', '', 'indexed', 'updatable', 'progress']
        self.aa = QtWidgets.QProgressBar()
        # self.itemc = QtGui.QStandardItem(self.aa)
        self.model_uuid.setItem(0, 9, QtWidgets.QProgressBar())

        pass
        return
        row = []
        for idx, col in enumerate(['NAME', 2, 3, 4, 5, 6, 7]):
            newitem = QtGui.QStandardItem()
            if idx in [0]:
                newitem.setData(QtCore.QVariant("aaaa"), QtCore.Qt.DisplayRole)
                newitem.setData(QtCore.QVariant("dddd"), HACKED_QT_EDITROLE)

            if idx in [2]:
                newitem.setData(QtCore.QVariant(col), HACKED_QT_EDITROLE)
            if idx in [4, 5, 6]:
                newitem.setData(QtCore.QVariant(col), HACKED_QT_EDITROLE)
            row.append(newitem)
        self.model.appendRow(row)

        # self.update_item_icon()
        return
        self.print_clipboard()

        cb = QtWidgets.QApplication.clipboard()

        qurl = QtCore.QUrl().fromLocalFile("/home/cc/Desktop/TeamViewer.desktop")

        md = QtCore.QMimeData()
        md.setUrls([qurl])
        md.setText("/home/cc/Desktop/TeamViewer.desktop")
        cb.setMimeData(md, mode=cb.Clipboard)

        self.print_clipboard()
        # print self.get_search_included_uuid()


        # self.qsql_model = QtSql.QSqlQueryModel()
        # header_list = self.header_list
        # self.qsql_model.setQuery(
        #     "select  " + ",".join(header_list) + ' from `c08e276b-45d6-4669-bef3-77260a891c31` WHERE Filename LIKE "%zip"  ')
        # self.ui.tableView.setModel(self.qsql_model)
        # self.proxy.setSourceModel(self.qsql_model)

        # self.model_uuid.clear()
        # print self.table_header.sortIndicatorSection()
        # print self.table_header.sortIndicatorOrder()
        # self.ui.tableView.setSortingEnabled(1)

    @pyqtSlot()
    def on_push_button_updatedb_clicked(self):
        update_path_list = []
        for row in range(self.ui.tableWidget_uuid.rowCount()):
            uuid = self.ui.tableWidget_uuid.item(row, 3).data(QtCore.Qt.DisplayRole)
            path = self.ui.tableWidget_uuid.item(row, 1).data(QtCore.Qt.DisplayRole)
            included = self.ui.tableWidget_uuid.item(row, 0).data(QtCore.Qt.CheckStateRole) \
                       == QtCore.Qt.Checked
            updatable = self.ui.tableWidget_uuid.item(row, 9).data(QtCore.Qt.CheckStateRole) \
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

        print self.table_header.sortIndicatorSection()
        print self.table_header.sortIndicatorOrder()

    @pyqtSlot(QtGui.QStandardItem)
    def on_table_uuid_itemChanged(self, item):
        pass
        # idx = self.model_uuid.indexFromItem(item)
        # if idx.column() == 0:
        #     row = idx.row()
        #     uuid = self.model_uuid.index(row, 3).data()
        #     print "UUID item changed: ", idx.column(), idx.row(), item.checkState(), uuid
        #     cur.execute(''' UPDATE  UUID SET included=?
        #             WHERE uuid=? ''',
        #                 (item.checkState()==QtCore.Qt.Checked,uuid))
        #     con.commit()

    @pyqtSlot(str)
    def on_lineedit_text_changed(self, text):
        print 'Text changerd.'
        text = self.ui.lineEdit_search.text().strip()
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


    def test_action_slot(self,x):
        print x

    @pyqtSlot(QtCore.QPoint)
    def on_tableview_context_menu_requested(self, point):
        point = QtGui.QCursor.pos()
        menu = QtWidgets.QMenu(self)
        file_type = self._get_filetype_of_selected()
        filename_list = [x[2] for x in self.get_tableview_selected()]
        icon_filename, app_name, app_tooltip, app_launch_fun, app_launcher = get_default_app(file_type)
        if (not file_type) or (file_type =="folder") or (not app_name):
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
                tmp = open_with_menu.addAction('''Open with "%s"''' % app_name, partial(app_launch_fun, app_launcher, filename_list))
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
        move_to_menu.addSeparator()
        copy_to_menu = menu.addMenu("Copy to ...")
        copy_to_menu.addAction("Browser ...", self.on_tableview_context_menu_copy_to)
        copy_to_menu.addSeparator()
        menu.addAction("test", self.on_tableview_context_menu_test)

        # Need GTk3 to use Gtk.AppChooserDialog.new_for_content_type
        # menu.addAction("Open with Other Application...",lambda  *args: pop_select_app_dialog())
        print point
        menu.exec_(point)

    @pyqtSlot(QtCore.QModelIndex)
    #a = QtCore.QModelIndex()
    def on_tableview_double_clicked(self, index):
        logger.info("Item double clicked: " + str(index))
        row = index.row()
        if index.column() == 0:
            Filename = self.model.data(self.model.index(row, 0), HACKED_QT_EDITROLE)
            Path = self.model.data(self.model.index(row, 1), HACKED_QT_EDITROLE)
            import  os
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
        print self.ui.tableView.SelectRows
        row_set = set()
        for i in self.ui.tableView.selectedIndexes():
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
            self.statusBar().setStyleSheet(
                "QStatusBar{color:red;font-weight:bold;}")

            self.statusBar().showMessage(msg, 3000)
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
        self.statusBar().setStyleSheet("QStatusBar{}")

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
        import os, shutil
        des_path = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory (move to)"))
        print "move to", des_path
        if not os.path.exists(des_path):    return
        for Filename, Path, fullpath, IsFolder in self.get_tableview_selected():
            # if not os.path.exists(Path):    continue
            try:
                shutil.move(fullpath, des_path)
            except:
                print("Fail to move file: %s" % fullpath)

    @pyqtSlot()
    def on_tableview_context_menu_copy_to(self):
        import os, shutil
        des_path = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory (copy to)"))
        print "copy to", des_path
        if not os.path.exists(des_path):    return
        for Filename, Path, fullpath, IsFolder in self.get_tableview_selected():
            # if not os.path.exists(Path):    continue
            try:
                if False and IsFolder:
                    pass
                    # shutil.copytree(fullpath, des_path) # TODO: test this
                else:
                    shutil.copy2(fullpath, des_path)
            except:
                print("Fail to copy file: %s" % fullpath)

    @pyqtSlot()
    def on_tableview_context_menu_test(self):
        print "test."
        cb = QtWidgets.QApplication.clipboard()
        print cb.text(mode=cb.Clipboard)
        print cb.mimeData(mode=cb.Clipboard)
        # cb.clear(mode=cb.Clipboard)
        # cb.setText("Clipboard Text", mode=cb.Clipboard)
        # print cb.text(mode=cb.Clipboard)

    @pyqtSlot(int, list)
    def on_model_receive_new_row(self, query_id, row):
        if query_id < self.Query_Text_ID_list[0]:
            # old query, ignore
            return
        # if self.Query_Model_ID < query_id:
        #     self.Query_Model_ID = query_id
        #     self.model.clear()
        #     # TODO: highlight former selected rows
        if self.model.rowCount() < MODEL_MAX_ITEMS:
            self.model.appendRow(row)

    @pyqtSlot(int, int, str)
    def on_db_progress_update(self, num_records, mftsize, uuid_updating):
        # self.update_progress_SIGNAL.emit

        # header_list = ['included', 'path', 'label', 'uuid', 'fstype', 'name',
        #                'major_dnum', 'minor_dnum', 'indexed', 'updatable']
        # h_header = ['', 'Path', 'Label', 'UUID', 'FS type', 'Dev name',
        #             '', '', 'indexed', 'updatable', 'progress']
        # self.ui.tableWidget_uuid = QtWidgets.QTableWidget()

        logger.debug("DB progress update: " + str([num_records, mftsize, uuid_updating]))
        # self.parent_application.processEvents()

        for row in range(self.ui.tableWidget_uuid.rowCount()):
            uuid = self.ui.tableWidget_uuid.item(row, 3).data(QtCore.Qt.DisplayRole)
            if uuid == uuid_updating:
                progressbar = self.ui.tableWidget_uuid.cellWidget(row, 10)
                if not progressbar:
                    progressbar = QtWidgets.QProgressBar()
                    progressbar.setMaximum(100)
                    self.ui.tableWidget_uuid.setCellWidget(row, 10, progressbar)
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
                    progressbar.setFormat("Done")
                    self.ui.tableWidget_uuid.item(row, 8).setData(1, HACKED_QT_EDITROLE)
                    self.ui.tableWidget_uuid.item(row, 8).setData(1, QtCore.Qt.DisplayRole)
                    self.ui.tableWidget_uuid.item(row, 8).setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
                else:
                    if mftsize < 0:
                        progressbar.setMinimum(0)
                        progressbar.setMaximum(0)
                        progressbar.setFormat(str(num_records))
                    else:
                        progressbar.setFormat("%d/%d  " %(num_records, mftsize) + "%p%")
                        progressbar.setValue(num_records * 100 / mftsize)
                break

        if num_records == -2:
            logger.debug("DB progress update: " + "merge temp db.")
            cur.execute('''ATTACH "%s" AS SecondaryDB''' % TEMP_DB_NAME)
            cur.execute('''SELECT name FROM SecondaryDB.sqlite_master WHERE type='table' ''')
            table_names = cur.fetchall()
            for table in table_names:
                cur.execute('''DELETE FROM `%s`'''
                            % (table[0])
                            )
                cur.execute('''INSERT OR REPLACE INTO "%s" SELECT * FROM %s  ''' % (table[0], ''' SecondaryDB."%s" ''' % table[0]))
                # '''CREATE TABLE "%s" AS SELECT * FROM %s"    '''
                # '''INSERT OR IGNORE INTO "%s" SELECT * FROM %s"    '''
                # '''INSERT OR REPLACE INTO "%s" SELECT * FROM %s"   '''
            cur.execute('''DETACH DATABASE SecondaryDB''')
            con.commit()
            try:
                os.remove(TEMP_DB_NAME)
            except Exception as e:
                logger.warning("Fail to delete temp db file: "+TEMP_DB_NAME +"\N"+e.message)

    @pyqtSlot()
    def update_query_result_old(self):

        pass
        print 'New query.'
        text = self.ui.lineEdit_search.text()
        # self.proxy.setFilterKeyColumn(            0)  # The default value is 0. If the value is -1, the keys will be read from all columns.
        # self.proxy.setFilterWildcard(text)
        # (?=.*?aa)(?=.*?bb)
        query_str = ''
        for i in text.strip().split():
            # NOT    =.*?
            query_str += "(?=.*%s)" % QtCore.QRegularExpression.escape(i)
        re = QtCore.QRegExp(query_str)
        # re = QtCore.QRegExp(text)

        # re.setPatternSyntax(QtCore.QRegExp.RegExp) # http://doc.qt.io/qt-5/qregexp.html
        # re.setPatternSyntax(QtCore.QRegExp.Wildcard)
        # re.setCaseSensitivity(QtCore.Qt.CaseSensitive)
        re.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        re.setMinimal(True)
        print "========== Search text ===== :", text, query_str, re
        self.proxy.setFilterRegExp(re)

        # self.proxy.setFilterKeyColumn(
        #     0)  # The default value is 0. If the value is -1, the keys will be read from all columns.
        # self.proxy.setFilterWildcard("*.zip*")

        # header_list = self.header_list
        # cur.execute("select  " + ",".join(header_list) + ' from `0FC20A580FC20A58`' )
        # self.model.cl
        # for query_row in cur:
        #     print query_row
        #     row = []
        #     for idx,col in enumerate(query_row):
        #         # print col
        #         newitem = QtGui.QStandardItem(str(col))
        #         if idx in [2]:
        #             newitem.setData(QtCore.QVariant(col), QtCore.Qt.EditRole)
        #
        #         if idx in [4, 5, 6]:
        #             newitem.setData(QtCore.QVariant(col), QtCore.Qt.EditRole)
        #         row.append(newitem)
        #
        #     self.model.appendRow(row)

    @pyqtSlot()
    def update_query_result(self):
        text = self.ui.lineEdit_search.text().strip()

        cur_query_id_list = self.Query_Text_ID_list
        cur_query_id_list[0] += 1  # TODO: handle overflow
        query_id = cur_query_id_list[0]
        uuid_path_list = self.get_search_included_uuid()

        header_list = self.header_list
        sql_mask = " SELECT " + ",".join(header_list) + ' FROM `%s` '
        sql_mask = sql_mask.replace("Path", '''"%s"||Path''')

        if not text:
            self.progressBar.setVisible(False)
            self.model.setRowCount(0)
            # sql_mask += "LIMIT 200"
            self.send_query_to_worker_SIGNAL.emit(query_id, uuid_path_list, sql_mask, cur_query_id_list,
                                                  self)  # (query_id, uuid_path_list, sql_mask, cur_query_id_list)

            return

        sql_where = []
        for i in text.split(' '):
            if i:
                sql_where.append(''' (`Filename` LIKE "%%%%%s%%%%") ''' % i)
        sql_where = " WHERE " + " AND ".join(sql_where)
        sql_mask = sql_mask + sql_where
        # # sql_mask % (path, uuid)
        logger.debug("SQL mask: " + sql_mask)
        # print "SQL mask: " + sql_mask
        self.model.setRowCount(0)
        self.progressBar.setVisible(True)
        self.progressBar.setValue(0)
        self.send_query_to_worker_SIGNAL.emit(query_id, uuid_path_list, sql_mask, cur_query_id_list,
                                              self)  # (query_id, uuid_path_list, sql_mask, cur_query_id_list)
        # self.distribute_query_worker.distribute_new_query(query_id, uuid_path_list, sql_mask, cur_query_id_list,
        #                                                   self)  # (query_id, uuid_path_list, sql_mask, cur_query_id_list)

    def build_table_model(self):
        self.model = QtGui.QStandardItemModel(self.ui.tableView)
        self.model.setSortRole(HACKED_QT_EDITROLE)
        header_list = ['Filename', 'Path', 'Size', 'IsFolder',
                       'atime', 'mtime', 'ctime']
        self.header_list = header_list
        # self.model.setRowCount(17)
        print len(header_list)
        self.model.setColumnCount(len(header_list))
        self.model.setHorizontalHeaderLabels(header_list)

        # cur.execute("select  " + ",".join(header_list) + ' from `c08e276b-45d6-4669-bef3-77260a891c31` limit 100' )
        #
        # for query_row in cur:
        #     row = []
        #     for idx,col in enumerate(query_row):
        #         newitem = QtGui.QStandardItem(str(col))
        #         if idx in [2]:
        #             newitem.setData(QtCore.QVariant(col), QtCore.Qt.EditRole)
        #         if idx in [4, 5, 6]:
        #             newitem.setData(QtCore.QVariant(col), QtCore.Qt.EditRole)
        #         row.append(newitem)
        #     self.model.appendRow(row)

        self.proxy = QtCore.QSortFilterProxyModel(self)
        self.proxy.setSourceModel(self.model)
        self.proxy.setFilterKeyColumn(
            0)  # The default value is 0. If the value is -1, the keys will be read from all columns.
        # self.proxy.setFilterWildcard("*.zip*")
        # https://deptinfo-ensip.univ-poitiers.fr/ENS/pyside-docs/PySide/QtGui/QSortFilterProxyModel.html
        self.proxy.setDynamicSortFilter(
            True)  # This property holds whether the proxy model is dynamically sorted and filtered whenever the contents of the source model change.
        self.proxy.setFilterRole(HACKED_QT_EDITROLE)

    @pyqtSlot()
    def refresh_table_model(self):
        ElapsedTimer = QtCore.QElapsedTimer()
        ElapsedTimer.start()

        print "Refresh table"
        # header_list = ['Filename', 'Path', 'Size', 'IsFolder',
        #                'atime', 'mtime', 'ctime']
        header_list = self.header_list
        self.model.setRowCount(0)

        included_uuid_path = self.get_search_included_uuid()

        sql_comm = []
        sql_mask = " SELECT " + ",".join(header_list) + ' FROM `%s` '
        sql_mask = sql_mask.replace("Path", '''"%s"||Path''')
        for i in included_uuid_path:
            sql_comm.append(sql_mask % (i[1], i[0]))

        sql_comm = " UNION ALL ".join(sql_comm) + "LIMIT 100"
        cur.execute(sql_comm)

        print ElapsedTimer.elapsed()

        for query_row in cur:
            row = []
            for idx, col in enumerate(query_row):
                newitem = QtGui.QStandardItem(str(col))
                if idx in [2]:
                    newitem.setData(QtCore.QVariant(col), HACKED_QT_EDITROLE)
                if idx in [4, 5, 6]:
                    newitem.setData(QtCore.QVariant(col), HACKED_QT_EDITROLE)
                row.append(newitem)

            self.model.appendRow(row)

        print ElapsedTimer.elapsed()

    def build_table_widget_uuid(self):
        header_list = ['included', 'path', 'label', 'uuid', 'fstype', 'name',
                       'major_dnum', 'minor_dnum', 'indexed', 'updatable']
        h_header = ['', 'Path', 'Label', 'UUID', 'FS type', 'Dev name',
                    '', '', 'indexed', 'updatable', 'progress']
        self.header_list_uuid = header_list
        self.ui.tableWidget_uuid.setColumnCount(len(h_header))
        self.ui.tableWidget_uuid.setHorizontalHeaderLabels(h_header)

        # self.ui.tableWidget_uuid = QtWidgets.QTableWidget()

        cur.execute("select  " + ",".join(header_list) + ' from `UUID`')

        for query_row in cur:
            self.ui.tableWidget_uuid.insertRow(self.ui.tableWidget_uuid.rowCount())
            row = self.ui.tableWidget_uuid.rowCount() - 1
            print query_row
            for idx, col in enumerate(query_row):
                # print col
                if col is None:
                    col = ''
                newitem = QtWidgets.QTableWidgetItem(str(col))
                if idx in [6, 7]:
                    newitem.setData(HACKED_QT_EDITROLE, QtCore.QVariant(col))
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
                self.ui.tableWidget_uuid.setItem(row, idx, newitem)

                # newitem = QtWidgets.QProgressBar()
                # newitem.setMaximum(100)
                # newitem.setValue(40)
                # self.ui.tableWidget_uuid.setCellWidget(row, 10, newitem)
                # progressbar = self.ui.tableWidget_uuid.cellWidget(row, 10)
                # progressbar.hide()

                # set_qicon(row[0], query_row[0], query_row[3])

                # self.model_uuid.appendRow(row)

    def build_table_model_uuid(self):
        self.model_uuid = QtGui.QStandardItemModel(self.ui.tableView_uuid)
        self.model_uuid.itemChanged.connect(self.on_table_uuid_itemChanged)

        header_list = ['included', 'path', 'label', 'uuid', 'fstype', 'name',
                       'major_dnum', 'minor_dnum', 'indexed', 'updatable']
        h_header = ['', 'Path', 'Label', 'UUID', 'FS type', 'Dev name',
                    '', '', 'indexed', 'updatable', 'progress']
        self.header_list_uuid = header_list

        self.model_uuid.setColumnCount(len(h_header))
        self.model_uuid.setHorizontalHeaderLabels(h_header)
        self.model_uuid.setSortRole(HACKED_QT_EDITROLE)
        # for i,header in enumerate(header_list):
        #     self.model.setHeaderData(i, QtCore.Qt.Horizontal, header)
        # self.model.setRowCount(0)

        cur.execute("select  " + ",".join(header_list) + ' from `UUID`')

        for query_row in cur:
            print query_row
            row = []
            for idx, col in enumerate(query_row):
                # print col
                if col is None:
                    col = ''
                newitem = QtGui.QStandardItem(str(col))
                if idx in [6, 7]:
                    newitem.setData(QtCore.QVariant(col), HACKED_QT_EDITROLE)
                elif idx in [0]:
                    newitem.setData('', HACKED_QT_EDITROLE)
                    newitem.setData('', QtCore.Qt.DisplayRole)
                    newitem.setCheckable(True)
                    if int(col) > 0:
                        newitem.setCheckState(QtCore.Qt.Checked)
                    else:
                        newitem.setCheckState(QtCore.Qt.Unchecked)
                    # icon = QtGui.QIcon('dev-harddisk.png')
                    # newitem.setEnabled(False)
                    newitem.setIcon(QtGui.QIcon('dev-harddisk.png'))
                elif idx in [9]:
                    newitem.setData('', HACKED_QT_EDITROLE)
                    newitem.setData('', QtCore.Qt.DisplayRole)
                    newitem.setCheckable(True)
                    if int(col) > 0:
                        newitem.setCheckState(QtCore.Qt.Checked)
                    else:
                        newitem.setCheckState(QtCore.Qt.Unchecked)

                if idx > 3:
                    newitem.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)

                row.append(newitem)
            # set_qicon(row[0], query_row[0], query_row[3])

            self.model_uuid.appendRow(row)

    def get_search_included_uuid_old(self):
        cur.execute('''SELECT `uuid`,`path` FROM UUID WHERE (included=1) ''')

        return cur.fetchall()

    def get_search_included_uuid_old_2(self):
        r = []
        for row in range(self.model_uuid.rowCount()):
            included = self.model_uuid.index(row, 0).data(QtCore.Qt.CheckStateRole) \
                       == QtCore.Qt.Checked
            if not included:
                continue
            uuid = self.model_uuid.index(row, 3).data()
            path = self.model_uuid.index(row, 1).data()
            cur.execute('''SELECT COALESCE(MAX(rowid),0) FROM `%s` ''' % (uuid))
            rows = cur.fetchall()[0][0]  # max(rowid)
            r.append({'uuid': uuid, 'path': path, 'rows': rows})
        return r

    def get_search_included_uuid(self):
        r = []
        for row in range(self.ui.tableWidget_uuid.rowCount()):
            included = self.ui.tableWidget_uuid.item(row, 0).data(QtCore.Qt.CheckStateRole) \
                       == QtCore.Qt.Checked
            if not included:
                continue
            uuid = self.ui.tableWidget_uuid.item(row, 3).data(QtCore.Qt.DisplayRole)
            path = self.ui.tableWidget_uuid.item(row, 1).data(QtCore.Qt.DisplayRole)
            cur.execute('''SELECT COALESCE(MAX(rowid),0) FROM `%s` ''' % (uuid))
            rows = cur.fetchall()[0][0]  # max(rowid)
            r.append({'uuid': uuid, 'path': path, 'rows': rows})
        return r

        # cur.execute('''SELECT `uuid`,`path` FROM UUID WHERE (included=1) ''')
        # r = []
        # for c in cur.fetchall():
        #     uuid = c[0]
        #     path = c[1]
        #     cur.execute('''SELECT COALESCE(MAX(rowid),0) FROM `%s` ''' % (uuid) )
        #     rows = cur.fetchall()[0][0]     # max(rowid)
        #     r.append({'uuid':uuid,
        #               'path':path,
        #               'rows':rows})
        # return r

    def closeEvent(self, event):
        print('close')
        self.distribute_query_thread.quit()
        self.update_db_Thread.quit()
        # for row in range(self.model_uuid.rowCount()):
        #     uuid        = self.model_uuid.index(row, 3).data()
        #     included    = self.model_uuid.index(row, 0).data(QtCore.Qt.CheckStateRole) \
        #                   == QtCore.Qt.Checked
        #     updatable   = self.model_uuid.index(row, 9).data(QtCore.Qt.CheckStateRole) \
        #                 == QtCore.Qt.Checked
        #     print uuid, included
        #     cur.execute(''' UPDATE  UUID SET included=?, updatable=?
        #                 WHERE uuid=? ''',
        #                 (included, updatable, uuid))
        for row in range(self.ui.tableWidget_uuid.rowCount()):
            uuid = self.ui.tableWidget_uuid.item(row, 3).data(QtCore.Qt.DisplayRole)
            included = self.ui.tableWidget_uuid.item(row, 0).data(QtCore.Qt.CheckStateRole) \
                       == QtCore.Qt.Checked
            updatable = self.ui.tableWidget_uuid.item(row, 9).data(QtCore.Qt.CheckStateRole) \
                        == QtCore.Qt.Checked
            print uuid, included
            cur.execute(''' UPDATE  UUID SET included=?, updatable=?
                        WHERE uuid=? ''',
                        (included, updatable, uuid))
        con.commit()
        # con.close()
        self.distribute_query_thread.wait()


        # save column width
        width_list_result = []
        width_list_uuid = []
        for i in  range(self.model.columnCount()):
            width_list_result.append(self.ui.tableView.columnWidth(i))
        for i in  range(self.ui.tableWidget_uuid.columnCount()):
            width_list_uuid.append(self.ui.tableWidget_uuid.columnWidth(i))

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



if __name__ == '__main__':
    app = QApplication(sys.argv)
    # if not createDBConnection():
    #     sys.exit(1)
    window = MyApp(app)
    window.show()
    exit_code = app.exec_()
    logger.info("Close db.")
    con.close()
    sys.exit(exit_code)

