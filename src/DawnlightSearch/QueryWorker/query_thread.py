from __future__ import absolute_import

from .._Global_Qt_import import *
from .._Global_DawnlightSearch import *
from .._Global_logger import *
from .sql_formatter import format_sql_cmd

try:
    import Queue
except:
    import queue as Queue

class QueryThread(QtCore.QThread):
    add_row_to_model_SIGNAL = QtCore.pyqtSignal(int, list)
    update_progress_SIGNAL = QtCore.pyqtSignal(int, int)

    def __init__(self, mutex, queue_condition, qqueue, parent=None,thread_id=0):
        super(self.__class__, self).__init__()
        self.mutex = mutex
        self.queue_condition = queue_condition
        self.qqueue = qqueue
        self.quit_flag = False
        self.thread_id = thread_id
        # self.add_row_to_model_SIGNAL = QtCore.pyqtSignal(list)

        # con = QtSql.QSqlDatabase.addDatabase("QSQLITE")
        # con.setDatabaseName(DATABASE_FILE_NAME)
        # if not con.open():
        #     print con.lastError().text()
        con = sqlite3.connect(DATABASE_FILE_NAME, check_same_thread=False)
        
        # note:  "COLLATE nocase" has no effect here. Use "(?i)" in the reg expr.
        import re
        def sqlite_regexp(expr, text):
            reg = re.compile(expr)
            return reg.search(text) is not None
        con.create_function("regexp", 2, sqlite_regexp)
        
        cur = con.cursor()

        self.cur = cur
        self.con = con

    def quit_previous_query(self):
        pass
        # TODO: cancel query

    def run(self):
        cur = self.cur
        cur.execute("PRAGMA case_sensitive_like=ON;")

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


                query_id = q['query_id']
                sql_comm = q['sql_comm']
                # msg = "Queue get: " + str(q) + '\n\t\t' + "Query_Text_ID: " + str(GlobalVar.Query_Text_ID) + " ID: " + str(query_id)
                # logger.debug(msg)
                case_sensitive_like_flag_ON = q['case_sensitive_like_flag']
                if (query_id < GlobalVar.Query_Text_ID or GlobalVar.CURRENT_MODEL_ITEMS>=GlobalVar.MODEL_MAX_ITEMS):
                    continue
                try:
                    if case_sensitive_like_flag_ON:
                        cur.execute('PRAGMA case_sensitive_like=ON;')
                    else:
                        cur.execute('PRAGMA case_sensitive_like=OFF;')
                    cur.execute(sql_comm)
                    for query_row in cur:
                        if self.quit_flag:
                            break
                        row = [None] * len(DB_HEADER_LIST)
                        for idx, col in enumerate(query_row):
                            newitem = QtGui.QStandardItem(str(col))
                            newitem.setData(str(col), HACKED_QT_EDITROLE)
                            if idx in [QUERY_HEADER.Filename, QUERY_HEADER.Path]:
                                newitem.setData(str(col), HACKED_QT_EDITROLE)
                            if idx in [QUERY_HEADER.Size]:
                                newitem.setData(QtCore.QVariant(col), HACKED_QT_EDITROLE)
                            if idx in [QUERY_HEADER.atime, QUERY_HEADER.ctime, QUERY_HEADER.mtime]:
                                newitem.setData(QtCore.QVariant(col), HACKED_QT_EDITROLE)
                            if idx in [QUERY_HEADER.IsFolder]:
                                newitem.setTextAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)
                                if str(col) == '1':
                                    row[DB_HEADER.Extension] = QtGui.QStandardItem('')

                            row[QUERY_TO_DSP_MAP[idx]] = newitem

                            if idx == QUERY_HEADER.Filename and (row[DB_HEADER.IsFolder] is None):
                                extension = os.path.splitext(col)[1].replace('.','')
                                newitem = QtGui.QStandardItem(extension)
                                newitem.setData(extension, HACKED_QT_EDITROLE)
                                newitem.setTextAlignment(QtCore.Qt.AlignVCenter)
                                row[DB_HEADER.Extension] = newitem
                        if (query_id < GlobalVar.Query_Text_ID or GlobalVar.CURRENT_MODEL_ITEMS >= GlobalVar.MODEL_MAX_ITEMS):
                            break

                        self.add_row_to_model_SIGNAL.emit(query_id, row)
                        # self.model.appendRow(row)
                except Exception as e:
                    logger.error(str(e))
                if (not self.quit_flag) and (query_id == GlobalVar.Query_Text_ID):
                    self.update_progress_SIGNAL.emit(self.qqueue.qsize(), q['LEN'])

                    if self.qqueue.qsize() == 0:
                        GlobalVar.QUERY_READY_FLAG[self.thread_id] = True
                        # self.mutex.lock()
                        if   all(flag for flag in GlobalVar.QUERY_READY_FLAG):
                            # print(GlobalVar.QUERY_READY_FLAG)
                            logger.info('Query END')
                            self.update_progress_SIGNAL.emit(0, q['LEN'])
                        # self.mutex.unlock()

    def quit(self):
        self.quit_flag = True
        super(self.__class__, self).quit()

class DistributeQueryWorker(QtCore.QThread):
    def __init__(self, parent, **kwargs):  # *args, **kwargs
        super(self.__class__, self).__init__(parent)  # , **kwargs
        self.mutex = QtCore.QMutex()
        self.condition = QtCore.QWaitCondition()

        self.queue_mutex = QtCore.QMutex()
        self.queue_condition = QtCore.QWaitCondition()
        self.quit_flag = False

        self.qqueue = Queue.Queue()
        # In python, we don't need mutex. Queue is thread-safe.
        self.target_slot = kwargs['target_slot']
        self.update_progress_slot = kwargs['progress_slot']
        self.thread_no = max(1, QtCore.QThread.idealThreadCount())
        self.thread_pool = [QueryThread(self.queue_mutex, self.queue_condition, self.qqueue, parent=self, thread_id = i ) \
                            for i in range(self.thread_no)]
        GlobalVar.QUERY_READY_FLAG = [False] * self.thread_no
        for thread in self.thread_pool:
            thread.add_row_to_model_SIGNAL.connect(self.target_slot)
            thread.update_progress_SIGNAL.connect(self.update_progress_slot)
            thread.start()

    def run(self):
        while 1:
            if self.quit_flag:
                break
            self.mutex.lock()
            self.condition.wait(self.mutex)
            self.mutex.unlock()
            if self.quit_flag:
                break

            self.mutex.lock()
            [query_id, uuid_path_list, sql_text] = self.new_query_list
            self.mutex.unlock()

            # # ======================================
            # header_list = DB_HEADER_LIST
            # sql_mask = " SELECT " + ",".join(header_list) + ' FROM `%s` '
            # sql_mask = sql_mask.replace("Path", '''"%s"||Path''')
            # sql_where = []
            # for i in sql_text.split(' '):
            #     if i:
            #         sql_where.append(''' (`Filename` LIKE "%%%%%s%%%%") ''' % i)  # FIXME: ugly sql cmd
            # sql_where = " WHERE " + " AND ".join(sql_where)
            # sql_mask = sql_mask + sql_where
            # logger.debug("SQL mask: " + sql_mask)
            # # ======================================
            # logger.info(
            #     'distribute_new_query slot received: ' + str([query_id, uuid_path_list, sql_mask, cur_query_id_list
            #                                                   ]))
            # for thread in self.thread_pool:
            #     thread.quit_previous_query()
            #
            # self.queue_mutex.lock()
            # while not self.qqueue.empty():
            #     self.qqueue.get()
            # tmp_q = []
            # for table in uuid_path_list:  # {'uuid':uuid,'path':path,'rows':rows}
            #     table['path'] = "" if table['path'] == "/" else table['path']  # avoid "//dir/file"
            #     sql_comm = sql_mask % (table['path'], table['uuid'])  # path, uuid
            #     rowid_low = 0
            #     while rowid_low <= table['rows']:
            #         rowid_high = rowid_low + GlobalVar.QUERY_CHUNK_SIZE
            #         if "WHERE" in sql_comm.upper():
            #             sql_comm_2 = sql_comm + '  AND  (ROWID BETWEEN %s AND %s) ' % (rowid_low, rowid_high)
            #         else:
            #             sql_comm_2 = sql_comm + ' WHERE (ROWID BETWEEN %s AND %s) ' % (rowid_low, rowid_high)
            #         sql_comm_2 += " LIMIT %d" % GlobalVar.QUERY_LIMIT
            #         tmp_q.append({'query_id': query_id, 'sql_comm': sql_comm_2})
            #         rowid_low = rowid_high + 1
            # for idx, item in enumerate(tmp_q):
            #     item['SN'] = idx
            #     item['LEN'] = len(tmp_q)
            #     self.qqueue.put(item)
            # # ======================



            logger.info(
                'distribute_new_query slot received: ' + str([query_id, uuid_path_list, sql_text  ]))
            for thread in self.thread_pool:
                thread.quit_previous_query()

            self.queue_mutex.lock()
            while not self.qqueue.empty():
                self.qqueue.get()
            tmp_q = []
            for table in uuid_path_list:  # {'uuid':uuid,'path':path,'rows':rows}
                if not table['path']:       # table['path'] == None
                    # table['path'] = table['uuid']+'::'
                    table['path'] = table['alias'] + '::'
                table['path'] = "" if table['path'] == "/" else table['path']  # avoid "//dir/file"

                (table['path'], table['uuid'])  # path, uuid

                rowid_low = 0
                while rowid_low <= table['rows']:
                    rowid_high = rowid_low + GlobalVar.QUERY_CHUNK_SIZE
                    OK_flag, _ ,_ , sql_cmd, case_sensitive_like_flag_ON,_ = format_sql_cmd(
                        {
                            'path': table['path'],
                            'uuid': table['uuid'],
                            'sql_text': sql_text,
                            'rowid_low': rowid_low,
                            'rowid_high': rowid_high,
                        }
                    )
                    if OK_flag:
                        tmp_q.append({'query_id': query_id, 'sql_comm': sql_cmd, 'case_sensitive_like_flag': case_sensitive_like_flag_ON})
                    rowid_low = rowid_high + 1
            for idx, item in enumerate(tmp_q):
                item['SN'] = idx
                item['LEN'] = len(tmp_q)
                self.qqueue.put(item)

            GlobalVar.QUERY_READY_FLAG = [False] * self.thread_no

            self.queue_condition.wakeAll()

            self.queue_mutex.unlock()

    @pyqtSlot(list)
    def distribute_new_query(self, new_query_list):

        tmp_mutexlocker = QtCore.QMutexLocker(self.mutex)
        self.new_query_list = new_query_list
        self.condition.wakeOne()

    def quit(self):
        self.quit_flag = True
        for thread in self.thread_pool:
            thread.quit_flag = True
            thread.quit_previous_query()
            thread.quit()

        self.queue_mutex.lock()
        self.queue_condition.wakeAll()
        self.queue_mutex.unlock()

        self.mutex.lock()
        self.condition.wakeOne()
        self.mutex.unlock()

        for thread in self.thread_pool:
            thread.wait(5000)

        super(self.__class__, self).quit()
