# -*- coding: utf-8 -*-
# multi thread MFT
# Insert_db_thread insert into tmp db

from __future__ import absolute_import

import collections
import os
import sqlite3
import stat
import time

from .._Global_DawnlightSearch import *
from .._Global_Qt_import import *
from .._Global_logger import *
from ..MFT_parser.mft_cpp_parser_wrapper import mft_parser_cpp
from ..MFT_parser.mftsession_thread import *
from .sys_blk_devices import SystemDevices


class FLAG_class:
    __slots__ = ('quit_flag', 'restart_flag')
    quit_flag = False
    restart_flag = False


def estimate_num_of_files(root_path):
    import sys
    if sys.platform.startswith('darwin'):
        return -1
        pass
    elif os.name == 'nt':
        return -1
        pass  # TODO: handle in windows
    elif os.name == 'posix':
        root_path = '"' + root_path.replace('\\', '\\\\') \
            .replace('"', '\\"') \
            .replace('$', '\\$') \
            .replace('`', '\\`') + '"'
        tmp = os.popen('df --inodes ' + root_path).read().split('\n')
        tmp = tmp[-1] if tmp[-1] else tmp[-2]
        # Filesystem      Inodes  IUsed   IFree IUse% Mounted on
        # /dev/sda10     4808704 541245 4267459   12% /
        import re
        pattern = re.compile(r"^(.*?)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+\%)\s+(.*?)$")
        match = pattern.match(tmp)
        if match:
            # print match.groups(), int(match.groups()[2])
            return int(match.groups()[2])
        else:
            return -1


def os_listdir_walk(root_path, BFS=True):
    dir_queue = collections.deque([root_path])
    while dir_queue:
        if BFS:
            next_dir = dir_queue.popleft()  # BFS
        else:
            next_dir = dir_queue.pop()  # DFS
        try:
            shared_dir_content = os.listdir(next_dir)
            yield next_dir, shared_dir_content
            #   root,      subdirs + subfiles
            #   modified dir_content  =  list(  subdirs)
            if shared_dir_content:
                dir_queue.extend(shared_dir_content)
        except OSError as e:
            print ('\tError in lisdit : ' + str(e))
        except:
            print('\t\tError in lisdit : ' + next_dir)


class Insert_db_thread(QtCore.QThread):
    update_progress_SIGNAL = QtCore.pyqtSignal(int, int, str)

    # TODO: insert into tmp db and then merge

    def __init__(self, uuid, db_path=TEMP_DB_NAME,
                 parent=None, sql_insert_queue=None, sql_insert_mutex=None,
                 sql_insert_condition=None):
        super(self.__class__, self).__init__(parent)

        self.uuid = uuid
        self.db_path = db_path
        self.tmp_db_path = db_path + ".tmp"

        self.con_tmp_db = sqlite3.connect(self.tmp_db_path, check_same_thread=False)
        self.cur_tmp_db = self.con_tmp_db.cursor()

        table_name = uuid
        self.cur_tmp_db.execute('''
            SELECT count(*) FROM sqlite_master WHERE type='table' AND name='%s';
            ''' % (table_name))
        if self.cur_tmp_db.fetchall()[0][0] == 0:
            self.cur_tmp_db.execute('''CREATE TABLE "%s" (
                            `file_id` INTEGER,
                            `Filename`	TEXT,
                            `Path`	TEXT,
                            `Size`	INTEGER,
                            `IsFolder`	BLOB,
                            `atime`	INTEGER,
                            `mtime`	INTEGER,
                            `ctime`	INTEGER,
                            PRIMARY KEY(`file_id`)
                        )'''
                                    % (table_name)
                                    )

        self.quit_flag = False
        self.quit_already_flag = False

        self.commit_flag = False
        self.running_flag = False

        self.sql_insert_queue = sql_insert_queue
        self.sql_insert_mutex = sql_insert_mutex
        self.sql_insert_condition = sql_insert_condition

    def run(self):
        self.update_progress_SIGNAL.emit(-1, -1, self.uuid)  # start
        while 1:
            # Python queue is thread-safe.
            # In c++, use mutex - condition instead.
            self.running_flag = False

            self.sql_insert_mutex.lock()
            if self.sql_insert_queue.empty():
                self.sql_insert_condition.wait(self.sql_insert_mutex)
            if self.quit_flag:
                self.sql_insert_mutex.unlock()
                return
            table_name, data_list, num_records, mftsize, uuid = self.sql_insert_queue.get()
            self.sql_insert_mutex.unlock()

            self.running_flag = True

            if (num_records % (max(mftsize / 100, 1)) == 0 and num_records > 0) or \
                    (num_records == mftsize - 1):
                logger.info('Building Filepaths: {0:.0f}'.format(100.0 * num_records / mftsize) + '%')
                self.update_progress_SIGNAL.emit(num_records, mftsize, uuid)
            # print "--table_name: ", table_name
            # print "--data_list: ", data_list
            if self.quit_flag:
                return
            self.cur_tmp_db.execute('''insert into `%s` (`Filename`,`Path`,`Size`,`IsFolder`,
                                   `atime`,`mtime`,`ctime`)
                                values (?,  ?,  ?, ?, ?, ?, ?)''' % (table_name),
                                    (unicode(data_list[0]), unicode(data_list[1]), data_list[2], data_list[3],
                                     data_list[4], data_list[5], data_list[6]))  # tuple(data_list)
            if self.quit_flag:
                return
            # self.cur.execute('''insert into `%s` (`entry_id`,`name`)
            #                         values (?,  ?)''' % (table_name + '_fts'),
            #                  (self.cur.lastrowid, data_list[0]))
            if self.quit_flag:
                return
            if self.commit_flag:
                self.commit_flag = False
                self.con_tmp_db.commit()

    @pyqtSlot()
    def commit_slot(self):
        return
        tmp_mutexlocker = QtCore.QMutexLocker(self.sql_insert_mutex)
        if not self.sql_insert_queue.empty() or self.running_flag:
            self.commit_flag = True
            return
        else:
            self.con.commit()

    def pre_quit(self, commit_progress_flag=True):
        if not self.quit_already_flag:
            self.quit_flag = True

            self.sql_insert_mutex.lock()
            self.sql_insert_condition.wakeOne()
            self.sql_insert_mutex.unlock()

            self.wait()
            self.con_tmp_db.commit()
            self.con_tmp_db.close()

            import shutil
            shutil.move(self.tmp_db_path, self.db_path)
            if commit_progress_flag:
                self.update_progress_SIGNAL.emit(-2, -2, self.uuid)

            self.quit_already_flag = True

    def quit(self):
        self.pre_quit()
        super(self.__class__, self).quit()


class Update_DB_Thread(QtCore.QThread):
    insert_db_SIGNAL = QtCore.pyqtSignal(str, list, int, int, str)
    db_commit_SIGNAL = QtCore.pyqtSignal()
    update_progress_SIGNAL = QtCore.pyqtSignal(int, int, str)
    get_table_uuid_sendback_SIGNAL = QtCore.pyqtSignal(list)
    show_statusbar_warning_msg_SIGNAL = QtCore.pyqtSignal(str)

    def __init__(self, parent=None, mainwindows=None):  # , *args, **kwargs
        super(self.__class__, self).__init__(parent)  # *args, **kwargs

        logger.info("update db init: ")
        logger.info("\tThread:" + str(QtCore.QThread.currentThreadId()))
        self.mainwindows = mainwindows

        from PyQt5.QtCore import QSettings
        settings = QSettings(QSettings.IniFormat, QSettings.UserScope, ORGANIZATION_NAME, ALLICATION_NAME)
        excluded_folders = settings.value('Excluded_folders', type=str, defaultValue='')
        self.skip_dir = excluded_folders
        self.flag = FLAG_class()

        self.mutex = QtCore.QMutex()
        self.queue_condition = QtCore.QWaitCondition()
        import Queue
        self.qqueue = Queue.Queue()
        self.sql_insert_queue = Queue.Queue()
        self.sql_insert_mutex = QtCore.QMutex()
        self.sql_insert_condition = QtCore.QWaitCondition()

        self.get_table_uuid_sendback_SIGNAL.connect(parent.get_table_widget_uuid_back_slot)
        self.show_statusbar_warning_msg_SIGNAL.connect(parent.show_statusbar_warning_msg_slot)
        # self.insert_db_thread = Insert_db_thread(parent=self, sql_insert_queue=self.sql_insert_queue,
        #                                          sql_insert_mutex=self.sql_insert_mutex,
        #                                          sql_insert_condition=self.sql_insert_condition)
        # self.db_commit_SIGNAL.connect(self.insert_db_thread.commit_slot)
        #
        # self.update_progress_SIGNAL.connect(mainwindows.on_db_progress_update, QtCore.Qt.QueuedConnection)
        # self.insert_db_thread.update_progress_SIGNAL.connect(mainwindows.on_db_progress_update,
        #                                                      QtCore.Qt.QueuedConnection)
        #
        # self.insert_db_thread.start()

        logger.info("update db init: 1")
        logger.info("update db init: 2")
        self._init_db()  # TODO: OPT
        logger.info("update db init: 3")
        self.update_uuid()  # TODO: OPT
        logger.info("update db init: 4")

    def run(self):
        # logger.info("update db init: 1")
        # logger.info("update db init: 2")
        # self._init_db()  # TODO: OPT
        # logger.info("update db init: 3")
        # self.update_uuid()  # TODO: OPT
        # logger.info("update db init: 4")

        # follow the same structure of http://doc.qt.io/qt-5/qtcore-threads-mandelbrot-example.html
        while (1):
            print "Update db run: "
            print "\tThread:", int(QtCore.QThread.currentThreadId())

            while not self.qqueue.empty():
                if self.flag.restart_flag:
                    break
                if self.flag.quit_flag:
                    return

                self.mutex.lock()
                if self.qqueue.empty():
                    self.mutex.unlock()
                    continue  # break
                _item = self.qqueue.get()
                self.mutex.unlock()

                # self.con.commit()
                # TODO: try catch
                root_path = _item['path']
                uuid = _item['uuid']

                if self.flag.quit_flag:
                    break
                root_path = unicode(root_path)
                root_path_len = len(root_path) if len(root_path) > 1 else 0
                print ('Enter root_path: %s' % root_path)
                if root_path in self.skip_dir:
                    print ('Dir %s skipped.' % root_path)
                    continue
                if (not os.path.exists(root_path)):
                    logger.warning("Dir %s does not exists." % root_path)
                    self.show_statusbar_warning_msg_SIGNAL.emit("Dir %s does not exists." % root_path)
                    continue
                # try:
                if os.lstat(root_path).st_dev != 0:
                    device_maj_num = os.major(os.lstat(root_path).st_dev)
                    device_min_num = os.minor(os.lstat(root_path).st_dev)
                else:
                    device_maj_num = device_min_num = 0

                # uuid = self.UUID_class.deviceID_to_UUID((device_maj_num, device_min_num))
                fstype = SystemDevices.deviceDict[(device_maj_num, device_min_num)]['fstype']
                table_name = uuid
                self.init_table(table_name, clear_table=False)

                insert_db_thread = Insert_db_thread(uuid, parent=self, sql_insert_queue=self.sql_insert_queue,
                                                    sql_insert_mutex=self.sql_insert_mutex,
                                                    sql_insert_condition=self.sql_insert_condition)
                insert_db_thread.update_progress_SIGNAL.connect(self.mainwindows.on_db_progress_update,
                                                                QtCore.Qt.QueuedConnection)
                insert_db_thread.start()
                from PyQt5.QtCore import QSettings

                enable_MFT_parser = GlobalVar.USE_MFT_PARSER

                # self.update_progress_SIGNAL.emit(-1, -1, uuid)  # start
                MFT_parser_successful_flag = False
                if fstype == "ntfs" and enable_MFT_parser:
                    try:
                        MFT_file_path = os.path.join(root_path, "$MFT")
                        logger.info("Enter NTFS folder: %s" % root_path)
                        if not os.path.exists(MFT_file_path):
                            logger.warning("$MFT file does not exists." % MFT_file_path)
                            raise Exception("$MFT file does not exists." % MFT_file_path)

                        # FIXME: In linux, cannot get the latest MFT; "sync" does not work. Linux cache?

                        # settings = QSettings(QSettings.IniFormat, QSettings.UserScope, ORGANIZATION_NAME, ALLICATION_NAME)
                        enable_C_MFT_parser = GlobalVar.USE_MFT_PARSER_CPP

                        logger.info("enable_C_MFT_parser: " + str(enable_C_MFT_parser))
                        if enable_C_MFT_parser:
                            insert_db_thread.pre_quit(commit_progress_flag=False)
                            pass
                            insert_db_thread.update_progress_SIGNAL.emit(1, -3, uuid)
                            mft_parser_cpp(MFT_file_path, TEMP_DB_NAME, table_name)
                            insert_db_thread.update_progress_SIGNAL.emit(-2, -2, uuid)

                        else:
                            session = MftSession(MFT_file_path)
                            session.start(table_name, self.sql_insert_queue, self.sql_insert_mutex,
                                          self.sql_insert_condition)
                            while session.isRunning():
                                session.wait(timeout_ms=1000)
                                logger.info("Waiting... Running...")

                                if self.flag.quit_flag or self.flag.restart_flag:
                                    break
                            session.quit()
                            del session
                        MFT_parser_successful_flag = True
                    except Exception as e:
                        logger.error(e.message)
                        self.show_statusbar_warning_msg_SIGNAL.emit(e.message)

                if not MFT_parser_successful_flag:
                    num_records = 0
                    mftsize = estimate_num_of_files(root_path)
                    for root, subfiles in os_listdir_walk(root_path):
                        if self.flag.quit_flag or self.flag.restart_flag:
                            break
                        subdirs = []
                        for file_or_dir in subfiles:
                            if self.flag.quit_flag or self.flag.restart_flag:
                                break
                            num_records += 1
                            full_file_or_dir = os.path.join(root, file_or_dir)

                            # os.lstat   returns the information about a file, but do not follow symbolic links.
                            try:
                                l_stat = os.lstat(full_file_or_dir)
                            except OSError as e:
                                print e
                                continue

                            mode = l_stat.st_mode

                            if stat.S_ISLNK(mode):
                                # symbolic link
                                # TODO: handle symbolic link
                                continue

                            if l_stat.st_dev != 0:
                                major_dnum = os.major(l_stat.st_dev)
                                minor_dnum = os.minor(l_stat.st_dev)
                            else:
                                major_dnum = minor_dnum = 0

                            if (device_maj_num != major_dnum) or (device_min_num != minor_dnum):
                                print("In different device: %s vs. %s" % (full_file_or_dir, root_path))
                                # self.UUID_class.device_id_path[(major_dnum, minor_dnum)].add(full_file_or_dir)
                                # TODO: skip different device
                                # path_lists.append(full_file_or_dir)
                                continue

                            if stat.S_ISDIR(mode):
                                # https://docs.python.org/2/library/stat.html
                                # It's a directory, recurse into it
                                if full_file_or_dir in self.skip_dir:
                                    print ('Dir %s skipped.' % full_file_or_dir)
                                    continue
                                subdirs.append(full_file_or_dir)
                                #
                                self.sql_insert_mutex.lock()
                                self.sql_insert_queue.put([table_name,
                                                           [file_or_dir,
                                                            root[root_path_len:] if root[
                                                                                    root_path_len:] else '/' + root[
                                                                                                               root_path_len:],
                                                            None, True,
                                                            int(l_stat.st_atime), int(l_stat.st_mtime),
                                                            int(l_stat.st_ctime)],
                                                           num_records, mftsize, uuid]
                                                          )
                                self.sql_insert_condition.wakeOne()
                                self.sql_insert_mutex.unlock()

                            elif stat.S_ISREG(mode):
                                # regular file
                                self.sql_insert_mutex.lock()
                                self.sql_insert_queue.put([table_name,
                                                           [file_or_dir,
                                                            root[root_path_len:] if root[
                                                                                    root_path_len:] else '/' + root[
                                                                                                               root_path_len:],
                                                            l_stat.st_size, False,
                                                            int(l_stat.st_atime), int(l_stat.st_mtime),
                                                            int(l_stat.st_ctime)],
                                                           num_records, mftsize, uuid]
                                                          )
                                self.sql_insert_condition.wakeOne()
                                self.sql_insert_mutex.unlock()

                            elif stat.S_ISSOCK(mode):
                                # print('Found socket: %s' % full_file_or_dir)
                                continue
                            elif stat.S_ISFIFO(mode):
                                # print('Found FIFO (named pipe): %s' % full_file_or_dir)
                                continue
                            else:
                                # raise Exception("Unkown file type: " + full_file_or_dir)
                                # print ("Unkown file type: " + full_file_or_dir)
                                continue
                                # write back to 'shared_dir_content' in os_listdir_walk(root_path, BFS = True)
                        subfiles[:] = subdirs
                    self.db_commit_SIGNAL.emit()
                # self.update_progress_SIGNAL.emit(-2, -2, uuid)  # end
                logger.info("ALl sql_insert queued.")
                while not self.sql_insert_queue.empty():
                    if self.flag.quit_flag or self.flag.restart_flag:
                        break
                    time.sleep(0.1)
                logger.info(" sql_insert queue empty.. or quit/restart" + str(self.flag.quit_flag) + str(
                    self.flag.restart_flag))
                insert_db_thread.quit()
                # except Exception as e:
                #     print "Error when updating db: ", e

            if self.flag.quit_flag:
                return

            self.mutex.lock()
            if not self.flag.restart_flag:
                self.queue_condition.wait(self.mutex)  # timeout
            self.flag.restart_flag = False
            self.mutex.unlock()

            if self.flag.quit_flag:
                return
                # self.db_commit_SIGNAL.emit()

    def _open_db(self):
        # db_path = DATABASE_FILE_NAME

        # con has been declared in _Global_DawnlightSearch and initialized in DawnlightSearch_main

        # con = sqlite3.connect(db_path, check_same_thread=False)
        # cur = con.cursor()
        # self.cur = MainCon.cur
        # self.con = MainCon.con
        pass

    def _init_db(self):

        cur = MainCon.cur

        cur.execute('''
        SELECT count(*) FROM sqlite_master WHERE type='table' AND name='UUID';
        ''')
        if cur.fetchall()[0][0] == 0:
            cur.execute(''' CREATE TABLE "UUID" (
                            `included`  BLOB,
                            `id`	INTEGER NOT NULL PRIMARY KEY  ,
                            `uuid`	TEXT NOT NULL UNIQUE,
                            `fstype`	TEXT,
                            `name`	TEXT,
                            `label`	TEXT,
                            `major_dnum`	INTEGER,
                            `minor_dnum`	INTEGER,
                            `path`      TEXT,
                            `rows` INTEGER DEFAULT 0,
                            `updatable` BLOB DEFAULT 0
                        )''')
        self.update_uuid()

    def update_uuid(self):

        cur = MainCon.cur
        cur.execute('''
            SELECT uuid FROM `UUID` ;
            ''')
        uuid_in_db = cur.fetchall()
        uuids = [x[0] for x in uuid_in_db]
        SystemDevices.refresh_state()
        deviceDict = SystemDevices.deviceDict

        for dev_id, dev in deviceDict.items():
            uuid = dev['uuid']
            fstype = dev['fstype']
            label = dev['label']
            major_dnum, minor_dnum = dev_id

            if not uuid in uuids:
                cur.execute('''INSERT INTO UUID (included, uuid,fstype,name,label,major_dnum,minor_dnum, path)
                             VALUES (?, ?,   ?,     ?,    ?,    ?,   ?, ?)''',
                            (False, dev['uuid'], dev['fstype'], dev['name'], dev['label'],
                             major_dnum, minor_dnum, dev['mountpoint']))
            else:
                cur.execute('''UPDATE  UUID SET fstype=?,name=?,label=?,major_dnum=?,minor_dnum=?,path=?
                    WHERE uuid=?''',
                            (dev['fstype'], dev['name'], dev['label'],
                             major_dnum, minor_dnum, dev['mountpoint'],
                             dev['uuid'])
                            )
            self.init_table(uuid, clear_table=False)

            # self.con.commit()  # commit

    def init_table(self, table_name, clear_table=True):
        con = MainCon.con
        cur = MainCon.cur
        cur.execute('''
            SELECT count(*) FROM sqlite_master WHERE type='table' AND name='%s';
            ''' % (table_name))
        if cur.fetchall()[0][0] == 0:
            # unique file_id
            # http://stackoverflow.com/questions/9342249/how-to-insert-a-unique-id-into-each-sqlite-row
            cur.execute('''CREATE TABLE "%s" (
                            `file_id` INTEGER,
                            `Filename`	TEXT,
                            `Path`	TEXT,
                            `Size`	INTEGER,
                            `IsFolder`	BLOB,
                            `atime`	INTEGER,
                            `mtime`	INTEGER,
                            `ctime`	INTEGER,
                            PRIMARY KEY(`file_id`)
                        )'''
                        % (table_name)
                        )
            cur.execute('''CREATE INDEX `%s` ON `%s` (Filename, Size, atime, mtime, ctime) '''
                        % (table_name + '_idx', table_name)
                        )

            # cur.execute('''CREATE VIRTUAL TABLE "%s" USING fts4(
            #                 `entry_id` INTEGER,
            #                 `name`	TEXT,
            #             )'''
            #             % (table_name + '_fts')
            #             )

        elif clear_table:
            cur.execute('''DELETE FROM `%s`'''
                        % (table_name)
                        )
        cur.execute('''SELECT COALESCE(MAX(rowid),0) FROM `%s` ''' % (table_name))
        maxrowid = MainCon.cur.fetchall()[0][0]  # max(rowid)

        # Need Max-rowid rather than no. of rows. Rowid maybe larger than seq num.
        # cur.execute('''select Count(*) from `%s` limit 1;'''
        #             % (table_name)
        #             )
        # table_item_count = int(cur.fetchall()[0][0])
        cur.execute('''UPDATE  UUID SET rows=?
            WHERE uuid=?''',
                    (maxrowid, table_name)
                    )
        con.commit()

        # self.con.commit()
        #  `UUID_ID`	INTEGER,
        #  FOREIGN KEY(`UUID_ID`) REFERENCES UUID(ID)

    @pyqtSlot(list)  # {'path': path, 'uuid': uuid}
    def update_db_slot(self, path_lists):
        pass
        # self.con.commit()
        self.db_commit_SIGNAL.emit()
        # self.con.close()
        print "update db slot: ", path_lists
        print "\tThread:", int(QtCore.QThread.currentThreadId())

        tmp_mutexlocker = QtCore.QMutexLocker(self.mutex)
        tmp_mutexlocker2 = QtCore.QMutexLocker(self.sql_insert_mutex)
        while not self.qqueue.empty():
            self.qqueue.get()
        while not self.sql_insert_queue.empty():
            self.sql_insert_queue.get()

        for _item in path_lists:
            self.qqueue.put(_item)
        if (not self.isRunning()):
            self.start()  # just test
        else:
            self.flag.restart_flag = True
            self.queue_condition.wakeOne()

    @pyqtSlot(list)
    def update_uuid_slot(self, uuid_list):
        for row in uuid_list:
            uuid = row[0]
            included = row[1]
            updatable = row[2]
            logger.info("uuid: %s, included: %s" % (uuid, included))
            try:
                # MainCon.cur.execute(''' UPDATE  UUID SET included=?, updatable=?
                #             WHERE uuid=? ''',
                #                     (included, updatable, uuid))
                MainCon.cur.execute(''' insert or replace into  UUID ( included, updatable, uuid) VALUES (?, ?, ?) ''',
                                    (included, updatable, uuid))

            except Exception as e:
                self.show_statusbar_warning_msg_SIGNAL.emit(e.message)
                logger.error(e.message)
        self.update_uuid()

    @pyqtSlot()
    def merge_db_slot(self):
        logger.debug("Merge temp db.")
        while 1:
            try:
                MainCon.cur.execute('''ATTACH "%s" AS SecondaryDB''' % TEMP_DB_NAME)
                MainCon.cur.execute('''SELECT name FROM SecondaryDB.sqlite_master WHERE type='table' ''')
                table_names = MainCon.cur.fetchall()
                for table in table_names:
                    MainCon.cur.execute('''DELETE FROM `%s`'''
                                        % (table[0])
                                        )
                    MainCon.cur.execute('''INSERT OR REPLACE INTO "%s" SELECT * FROM %s  ''' % (
                        table[0], ''' SecondaryDB."%s" ''' % table[0]))
                    # '''CREATE TABLE "%s" AS SELECT * FROM %s"    '''
                    # '''INSERT OR IGNORE INTO "%s" SELECT * FROM %s"    '''
                    # '''INSERT OR REPLACE INTO "%s" SELECT * FROM %s"   '''
                MainCon.cur.execute('''DETACH DATABASE SecondaryDB''')
                MainCon.con.commit()
                break
            except Exception as e:
                msgBox = QMessageBox(self.parent())
                msgBox.setIcon(QMessageBox.Critical)
                msgBox.setText("Fail to merge temp databse into main database:\n%s\n\nError message:\n%s" % (
                TEMP_DB_NAME, e.message))
                msgBox.setInformativeText(
                    "Do you want to retry?\nPress \"Abort\" to quit and KEEP the temp database.\nPress \"Cancel\" or close this message to quit and DELETE the temp database.")
                msgBox.setStandardButtons(QMessageBox.Retry | QMessageBox.Abort | QMessageBox.Cancel)
                msgBox.setDefaultButton(QMessageBox.Retry)
                ret = msgBox.exec_()
                if (ret == msgBox.Retry):
                    continue
                elif (ret == msgBox.Abort):
                    return
                else:
                    break
        while 1:
            try:
                if not os.path.exists(TEMP_DB_NAME):
                    logger.warning("Temp db does not exist: " + TEMP_DB_NAME)
                    return
                os.remove(TEMP_DB_NAME)
                break
            except Exception as e:
                msgBox = QMessageBox(self.parent())
                msgBox.setIcon(QMessageBox.Critical)
                msgBox.setText("Fail to delete temp databse:\n%s\n\nError message:\n%s" % (TEMP_DB_NAME, e.message))
                msgBox.setInformativeText("Do you want to retry?")
                msgBox.setStandardButtons(QMessageBox.Retry | QMessageBox.Cancel)
                msgBox.setDefaultButton(QMessageBox.Retry)
                ret = msgBox.exec_()
                if (ret != msgBox.Retry):
                    break

    @pyqtSlot(list)
    def get_table_uuid_slot(self, header_list):
        # logger.info("update table uuid." + str(header_list))
        logger.info("get_table_uuid_slot.  gettable uuid." + str(header_list))
        MainCon.cur.execute("select  " + ",".join(header_list) + ' from `UUID`')
        self.get_table_uuid_sendback_SIGNAL.emit(MainCon.cur.fetchall())

    @pyqtSlot()
    def refresh_table_uuid_mount_state_slot_sender(self):
        pass

    def quit(self):
        self.mutex.lock()
        self.flag.quit_flag = True
        self.queue_condition.wakeOne()
        self.mutex.unlock()

        # self.con.commit()
        self.wait()
        # self.con.close()  # TODO: find a better place to close con
        super(self.__class__, self).quit()

    def __del__(self):
        s = super(self.__class__, self)
        try:
            s.__del__
        except AttributeError:
            pass
        else:
            s.__del__(self)


if __name__ == '__main__':
    # LinuxDevices()
    pass
    update_db_thread = Update_DB_Thread()
    update_db_thread.update_uuid()
    # update_db_thread.update_whole_filesdb('/')
    update_db_thread.update_whole_filesdb('/media')

    print update_db_thread.UUID_class.device_id_path
    print update_db_thread.UUID_class.device_id_path.keys()
    print update_db_thread.UUID_class.device_id_path.values()
