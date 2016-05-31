from __future__ import absolute_import

from .._Global_Qt_import import *
from .._Global_DawnlightSearch import *
from .._Global_logger import *

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
        logger.info(
            'distribute_new_query slot received: ' + str([query_id, uuid_path_list, sql_mask, cur_query_id_list,
                                                          ui_thread]))
        for thread in self.thread_pool:
            thread.quit_previous_query()

        tmp_mutexlocker = QtCore.QMutexLocker(self.mutex)
        while not self.qqueue.empty():
            self.qqueue.get()



        tmp_q = []
        for table in uuid_path_list:  # {'uuid':uuid,'path':path,'rows':rows}
            table['path'] = "" if table['path'] == "/" else table['path']  # avoid "//dir/file"
            sql_comm = sql_mask % (table['path'], table['uuid'])  # path, uuid
            rowid_low = 0
            while rowid_low <= table['rows']:
                rowid_high = rowid_low + GlobalVar.QUERY_CHUNK_SIZE
                if "WHERE" in sql_comm.upper():
                    sql_comm_2 = sql_comm + '  AND  (ROWID BETWEEN %s AND %s) ' % (rowid_low, rowid_high)
                else:
                    sql_comm_2 = sql_comm + ' WHERE (ROWID BETWEEN %s AND %s) ' % (rowid_low, rowid_high)
                sql_comm_2 += " LIMIT %d" % GlobalVar.QUERY_LIMIT
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
