# -*- coding: utf-8 -*-
# multi thread MFT
# Insert_db_thread insert into tmp db

from __future__ import absolute_import

from ._Global_Qt_import import *
from ._Global_DawnlightSearch import *
from ._Global_logger import *

from .MFT_parser.mftsession_thread import *
from .MFT_parser.mft_cpp_parser_wrapper import mft_parser_cpp

from sys_blk_devices import SystemDevices

import sqlite3
import os
import collections
import stat
import time

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

    def __init__(self, uuid,  db_path=TEMP_DB_NAME,
                 parent=None, sql_insert_queue=None, sql_insert_mutex=None,
                 sql_insert_condition=None ):
        super(self.__class__, self).__init__(parent)

        self.uuid = uuid
        self.db_path = db_path
        self.tmp_db_path = db_path +".tmp"

        con = sqlite3.connect(self.tmp_db_path, check_same_thread=False)
        cur = con.cursor()

        table_name = uuid
        cur.execute('''
            SELECT count(*) FROM sqlite_master WHERE type='table' AND name='%s';
            ''' % (table_name))
        if cur.fetchall()[0][0] == 0:
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

        self.cur = cur
        self.con = con
        self.quit_flag = False
        self.quit_already_flag = False

        self.commit_flag = False
        self.running_flag = False

        self.sql_insert_queue       = sql_insert_queue
        self.sql_insert_mutex       = sql_insert_mutex
        self.sql_insert_condition   = sql_insert_condition

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

            if (num_records % (max(mftsize / 100, 1)) == 0 and num_records > 0 )or \
                (num_records == mftsize-1):
                print 'Building Filepaths: {0:.0f}'.format(100.0 * num_records / mftsize) + '%'
                self.update_progress_SIGNAL.emit(num_records, mftsize, uuid)
            # print "--table_name: ", table_name
            # print "--data_list: ", data_list
            if self.quit_flag:
                return
            self.cur.execute('''insert into `%s` (`Filename`,`Path`,`Size`,`IsFolder`,
                                   `atime`,`mtime`,`ctime`)
                                values (?,  ?,  ?, ?, ?, ?, ?)''' % (table_name),
                             (unicode(data_list[0]), unicode(data_list[1]), data_list[2], data_list[3],
                              data_list[4], data_list[5], data_list[6]))#tuple(data_list)
            if self.quit_flag:
                return
            # self.cur.execute('''insert into `%s` (`entry_id`,`name`)
            #                         values (?,  ?)''' % (table_name + '_fts'),
            #                  (self.cur.lastrowid, data_list[0]))
            if self.quit_flag:
                return
            if self.commit_flag:
                self.commit_flag = False
                self.con.commit()

    @pyqtSlot()
    def commit_slot(self):
        return
        tmp_mutexlocker = QtCore.QMutexLocker(self.sql_insert_mutex)
        if not self.sql_insert_queue.empty() or self.running_flag:
            self.commit_flag = True
            return
        else:
            self.con.commit()

    def pre_quit(self, commit_progress_flag = True):
        if not self.quit_already_flag:
            self.quit_flag = True

            self.sql_insert_mutex.lock()
            self.sql_insert_condition.wakeOne()
            self.sql_insert_mutex.unlock()

            self.wait()
            self.con.commit()
            self.con.close()

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

    def __init__(self, parent= None, mainwindows=None):  # , *args, **kwargs
        super(self.__class__, self).__init__(parent)  # *args, **kwargs
        # import collections
        # def default_factory_1():
        #     return []
        # self.device_id_path = collections.defaultdict(default_factory_1)

        print "update db init: "
        print "\tThread:", int(QtCore.QThread.currentThreadId())
        self.mainwindows = mainwindows
        self.UUID_class = SystemDevices()
        from PyQt5.QtCore import QSettings
        settings = QSettings(QSettings.IniFormat, QSettings.UserScope, ORGANIZATION_NAME, ALLICATION_NAME)
        excluded_folders = settings.value('Excluded_folders', type=str)
        self.skip_dir = excluded_folders
        # self.skip_dir = set(['/proc', '/run', '/tmp', '/var', '/dev', '/sys', '/boot'])
        self._open_db()
        self._init_db()
        self.update_uuid()

        self.flag = FLAG_class()

        self.mutex = QtCore.QMutex()
        self.queue_condition = QtCore.QWaitCondition()
        import Queue
        self.qqueue = Queue.Queue()
        self.sql_insert_queue = Queue.Queue()
        self.sql_insert_mutex = QtCore.QMutex()
        self.sql_insert_condition = QtCore.QWaitCondition()

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

    def run(self):
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

                self.con.commit()

                root_path = _item['path']
                uuid      = _item['uuid']

                if self.flag.quit_flag:
                    break
                root_path = unicode(root_path)
                root_path_len = len(root_path) if len(root_path) > 1 else 0
                print ('Enter root_path: %s' % root_path)
                if root_path in self.skip_dir:
                    print ('Dir %s skipped.' % root_path)
                    continue
                if (not os.path.exists(root_path)):
                    print ("Dir %s does not exists." % root_path)
                    continue
                try:
                    if os.lstat(root_path).st_dev != 0:
                        device_maj_num = os.major(os.lstat(root_path).st_dev)
                        device_min_num = os.minor(os.lstat(root_path).st_dev)
                    else:
                        device_maj_num = device_min_num = 0

                    # uuid = self.UUID_class.deviceID_to_UUID((device_maj_num, device_min_num))
                    fstype = self.UUID_class.blockdevices_id[(device_maj_num, device_min_num)]['fstype']
                    table_name = uuid
                    self.init_table(table_name, clear_table=True)

                    self.UUID_class.device_id_path[(device_maj_num, device_min_num)].add(root_path)

                    insert_db_thread = Insert_db_thread(uuid, parent=self, sql_insert_queue=self.sql_insert_queue,
                                                             sql_insert_mutex=self.sql_insert_mutex,
                                                             sql_insert_condition=self.sql_insert_condition)
                    insert_db_thread.update_progress_SIGNAL.connect(self.mainwindows.on_db_progress_update,
                                                                         QtCore.Qt.QueuedConnection)
                    insert_db_thread.start()
                    from PyQt5.QtCore import QSettings
                    settings = QSettings(QSettings.IniFormat, QSettings.UserScope, ORGANIZATION_NAME, ALLICATION_NAME)
                    enable_MFT_parser = settings.value('Use_MFT_parser', type=bool, defaultValue = True)

                    # self.update_progress_SIGNAL.emit(-1, -1, uuid)  # start
                    if fstype == "ntfs" and root_path in self.UUID_class.mountNTFSpath and enable_MFT_parser:
                        print("Enter NTFS folder:", root_path)
                        assert os.path.exists(os.path.join(root_path, "$MFT"))
                        print " "
                        # TODO: In linux, cannot get the latest MFT. "sync" does not work. Linux cache?

                        # settings = QSettings(QSettings.IniFormat, QSettings.UserScope, ORGANIZATION_NAME, ALLICATION_NAME)
                        enable_C_MFT_parser = settings.value('Use_CPP_MFT_parser', type=bool, defaultValue=True)

                        if enable_C_MFT_parser:
                            insert_db_thread.pre_quit(commit_progress_flag=False)
                            pass
                            insert_db_thread.update_progress_SIGNAL.emit(1, -3, uuid)
                            mft_parser_cpp(os.path.join(root_path, "$MFT"), TEMP_DB_NAME, table_name)
                            insert_db_thread.update_progress_SIGNAL.emit(-2, -2, uuid)

                        else:
                            session = MftSession(os.path.join(root_path, "$MFT"))
                            session.start(table_name, self.sql_insert_queue, self.sql_insert_mutex, self.sql_insert_condition)
                            while session.isRunning():
                                session.wait(timeout_ms=1000)
                                print "Waiting... Running..."

                                if self.flag.quit_flag or self.flag.restart_flag:
                                    break
                            session.quit()
                            del session


                    else:
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
                                    self.UUID_class.device_id_path[(major_dnum, minor_dnum)].add(full_file_or_dir)
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
                                    print('Found socket: %s' % full_file_or_dir)
                                    continue
                                elif stat.S_ISFIFO(mode):
                                    print('Found FIFO (named pipe): %s' % full_file_or_dir)
                                    continue
                                else:
                                    # raise Exception("Unkown file type: " + full_file_or_dir)
                                    print ("Unkown file type: " + full_file_or_dir)
                                    continue
                                    # write back to 'shared_dir_content' in os_listdir_walk(root_path, BFS = True)
                            subfiles[:] = subdirs
                        self.db_commit_SIGNAL.emit()
                    # self.update_progress_SIGNAL.emit(-2, -2, uuid)  # end
                    print "ALl sql_insert queued."
                    while not self.sql_insert_queue.empty():
                        if self.flag.quit_flag or self.flag.restart_flag:
                            break
                        time.sleep(0.1)
                    print " sql_insert queue empty.. or quit/restart"
                    insert_db_thread.quit()
                except Exception as e:
                    print "Error when updating db: ", e

            if self.flag.quit_flag:
                return

            self.mutex.lock()
            if not self.flag.restart_flag:
                self.queue_condition.wait(self.mutex)   # timeout
            self.flag.restart_flag = False
            self.mutex.unlock()

            if self.flag.quit_flag:
                return
            # self.db_commit_SIGNAL.emit()


    def _open_db(self):
        db_path = DATABASE_FILE_NAME

        con = sqlite3.connect(db_path, check_same_thread=False)
        cur = con.cursor()
        self.cur = cur
        self.con = con

    def _init_tmp_db(self, tmp_db_path, uuid):
        table_name = uuid

        con = sqlite3.connect(tmp_db_path, check_same_thread=False)
        cur = con.cursor()
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
        con.commit()
        con.close()

    def _init_db(self):
        cur = self.cur

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
                            `indexed` BLOB DEFAULT 1,
                            `updatable` BLOB DEFAULT 1
                        )''')

    def update_uuid(self):
        cur = self.cur
        cur.execute('''
            SELECT uuid FROM `UUID` ;
            ''')
        uuid_in_db = cur.fetchall()
        uuids = [x[0] for x in uuid_in_db]
        devices = self.UUID_class
        for dev_name in devices.mountPath_dev:
            dev = devices.blockdevices_name[dev_name]
            (device_maj_num, device_min_num) = map(int, dev['maj:min'].split(':'))
            # uuid = dev['uuid']
            uuid = self.UUID_class.deviceID_to_UUID((device_maj_num, device_min_num))
            fstype = dev['fstype']
            label = dev['label']
            major_dnum, minor_dnum = map(int, dev['maj:min'].split(':'))

            if not uuid in uuids:
                cur.execute('''INSERT INTO UUID (included, uuid,fstype,name,label,major_dnum,minor_dnum)
                             VALUES (?, ?,   ?,     ?,    ?,    ?,   ?)''',
                            (True, dev['uuid'], dev['fstype'], dev['name'], dev['label'],
                             int(dev['maj:min'].split(':')[0]), int(dev['maj:min'].split(':')[1])))
            else:
                cur.execute('''UPDATE  UUID SET fstype=?,name=?,label=?,major_dnum=?,minor_dnum=?
                    WHERE uuid=?''',
                            (dev['fstype'], dev['name'], dev['label'],
                             int(dev['maj:min'].split(':')[0]), int(dev['maj:min'].split(':')[1]),
                             dev['uuid'])
                            )
            self.init_table(uuid, clear_table=False)
            if dev_name in devices.mountPath_dev:
                path = devices.mountPath_dev[dev_name]
                cur.execute('''UPDATE  UUID SET path=?
                    WHERE uuid=?''',
                            (path,
                             dev['uuid'])
                            )

        self.con.commit()  # commit

    def init_table(self, table_name, clear_table=True):
        cur = self.cur
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

            cur.execute('''CREATE VIRTUAL TABLE "%s" USING fts4(
                            `entry_id` INTEGER,
                            `name`	TEXT,
                        )'''
                        % (table_name + '_fts')
                        )

        elif clear_table:
            cur.execute('''DELETE FROM `%s`'''
                        % (table_name)
                        )
        cur.execute('''select Count(*) from `%s` limit 1;'''
                    % (table_name)
                    )
        table_item_count = int(cur.fetchall()[0][0])
        cur.execute('''UPDATE  UUID SET indexed=?
            WHERE uuid=?''',
                    (table_item_count > 0, table_name)
                    )
        self.con.commit()
        #  `UUID_ID`	INTEGER,
        #  FOREIGN KEY(`UUID_ID`) REFERENCES UUID(ID)

    @pyqtSlot(list)  # {'path': path, 'uuid': uuid}
    def update_db_slot(self, path_lists):
        pass
        self.con.commit()
        self.db_commit_SIGNAL.emit()
        # self.con.close()
        print "update db slot: ", path_lists
        print "\tThread:", int(QtCore.QThread.currentThreadId())

        tmp_mutexlocker  = QtCore.QMutexLocker(self.mutex)
        tmp_mutexlocker2 = QtCore.QMutexLocker(self.sql_insert_mutex)
        while not  self.qqueue.empty():
            self.qqueue.get()
        while not self.sql_insert_queue.empty():
            self.sql_insert_queue.get()

        for _item in path_lists:
            self.qqueue.put(_item)
        if (not self.isRunning()):
            self.start()        # just test
        else:
            self.flag.restart_flag = True
            self.queue_condition.wakeOne()

    def quit(self):
        self.mutex.lock()
        self.flag.quit_flag = True
        self.queue_condition.wakeOne()
        self.mutex.unlock()

        self.con.commit()
        self.wait()
        self.con.close()  # TODO: find a better place to close con
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