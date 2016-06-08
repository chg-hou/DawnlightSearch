#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import print_function
import os
import struct
from PyQt5 import QtCore

try:
    import mft
except:
    from ..MFT_parser import mft

class MftWorkerThread(QtCore.QThread):
    def __init__(self, mft_var, mft_seqs_flag_list, mftsize, filename, rw_lock,
                 sql_insert_queue, sql_insert_mutex, sql_insert_condition,
                 table_name, options, parent=None, ):

        super(self.__class__, self).__init__(parent)
        self.mft = mft_var
        self.mft_seqs_flag_list = mft_seqs_flag_list
        self.mftsize = mftsize
        self.filename = filename
        self.rw_lock = rw_lock
        self.sql_insert_queue = sql_insert_queue
        self.sql_insert_mutex = sql_insert_mutex
        self.sql_insert_condition = sql_insert_condition
        self.table_name = table_name
        self.options = options
        self.debug = options.debug

        self.file_mft = open(filename, 'rb')
        self.record_seq = 0

        self.quit_flag = False
        # ===================FOR CLEAN
        # self.rw_lock = QtCore.QReadWriteLock()
        # self.mft_seqs_flag_list = []

    def build_seq(self, record_seq):
        file_handle = self.file_mft
        # file_handle = open(self.options.filename, 'rb')

        file_handle.seek(record_seq * 1024, 0)
        raw_record = file_handle.read(1024)

        record = {}
        minirec = {}

        # file deleted
        if not (struct.unpack("<H", raw_record[22:24])[0] & 0x0001):
            minirec['name'] = "FILE_DELETED"
            minirec['path'] = "/"
            minirec['par_ref'] = 5
            # locked in function run already.
            self.mft[record_seq] = minirec
            self.mft_seqs_flag_list[record_seq] = 2
            return

        record = mft.parse_record(record, raw_record, self.options)
        record_num = record['recordnum']
        assert record_num == 0 or record_seq == record_num

        if record['fncnt'] == 1:
            minirec['par_ref'] = record['fn', 0]['par_ref']
            minirec['name'] = record['fn', 0]['name']
        elif record['fncnt'] > 1:
            minirec['par_ref'] = record['fn', 0]['par_ref']  # TODO: check hard link files
            for i in (0, record['fncnt'] - 1):
                if (record['fn', i]['nspace'] == 0x1 or record['fn', i]['nspace'] == 0x3):
                    minirec['name'] = record['fn', i]['name']
            if minirec.get('name') is None:
                minirec['name'] = record['fn', record['fncnt'] - 1]['name']

        if record['fncnt'] > 0:
            self.mft[record_seq] = minirec
            # self.get_folder_path(record_seq, record_seq)  # skip from loop
            # self.mft_seqs_flag_list[record_seq] = 2       # path is unknow, cannot submit
        else:
            minirec['name'] = "BAD_NAME"
            minirec['path'] = "/"
            minirec['par_ref'] = 5
            self.mft[record_seq] = minirec
            self.mft_seqs_flag_list[record_seq] = 2

    def get_folder_path(self, seqnum, seqnum2):
        if seqnum not in self.mft:
            self.build_seq(seqnum)
            if seqnum not in self.mft:
                print("Bad sernum: ", seqnum)
                self.mft[seqnum] = {'name': "BAD_NAME",
                                    'path': "/",
                                    'par_ref': 5}
                self.mft_seqs_flag_list[seqnum] = 2

        # If we've already figured out the path name, just return it
        if ('path' in self.mft[seqnum]) and ((self.mft[seqnum]['path']) != ''):
            # if self.debug: print "Building Folder For Record Number (%d) FOUND" % seqnum
            if self.mft[seqnum]['path'] is "/":
                return self.mft[seqnum]['path'] + self.mft[seqnum]['name']
            else:
                return self.mft[seqnum]['path'] + '/' + self.mft[seqnum]['name']

        try:
            if self.mft[seqnum]['par_ref'] == 5:  # Seq number 5 is "/", root of the directory
                self.mft[seqnum]['path'] = '/'
                return '/' + self.mft[seqnum]['name']
        except:  # If there was an error getting the parent's sequence number, then there is no FN record
            self.mft[seqnum]['name'] = ''  # 'NoFNRecord'
            return self.mft[seqnum]['path'] + '/' + self.mft[seqnum]['name']

        # Self referential parent sequence number. The filename becomes a NoFNRecord note
        if (self.mft[seqnum]['par_ref']) == seqnum:
            # if self.debug: print "Error, self-referential, while trying to determine path for seqnum %s" % seqnum
            self.mft[seqnum]['filename'] = 'ORPHAN/' + self.mft[seqnum]['name']
            return self.mft[seqnum]['path'] + '/' + self.mft[seqnum]['name']

        # We're not at the top of the tree and we've not hit an error
        parentpath = self.get_folder_path((self.mft[seqnum]['par_ref']), seqnum2)
        self.mft[seqnum]['path'] = parentpath
        if parentpath is "/":
            return self.mft[seqnum]['path'] + self.mft[seqnum]['name']
        else:
            return self.mft[seqnum]['path'] + '/' + self.mft[seqnum]['name']

    def run(self):
        record_seq = self.record_seq

        while record_seq < self.mftsize:
            self.rw_lock.lockForWrite()
            if self.quit_flag:
                self.rw_lock.unlock()
                return
            while self.mft_seqs_flag_list[record_seq] > 0:
                record_seq += 1
                if record_seq >= self.mftsize:
                    self.rw_lock.unlock()
                    return
            self.mft_seqs_flag_list[record_seq] = 1
            self.rw_lock.unlock()

            self.file_mft.seek(record_seq * 1024, 0)
            raw_record = self.file_mft.read(1024)

            record = {}
            minirec = {}

            # file deleted
            if not (struct.unpack("<H", raw_record[22:24])[0] & 0x0001):
                minirec['name'] = "FILE_DELETED"
                minirec['path'] = "/"
                minirec['par_ref'] = 5
                # http://effbot.org/pyfaq/what-kinds-of-global-value-mutation-are-thread-safe.htm
                # thread-safe, no lock needed.
                self.rw_lock.lockForWrite()
                self.mft[record_seq] = minirec
                self.mft_seqs_flag_list[record_seq] = 2
                self.rw_lock.unlock()
                continue

            record = mft.parse_record(record, raw_record, self.options)
            record_num = record['recordnum']
            assert record_num == 0 or record_seq == record_num

            if record['fncnt'] == 1:
                minirec['par_ref'] = record['fn', 0]['par_ref']
                minirec['name'] = record['fn', 0]['name']
            elif record['fncnt'] > 1:
                minirec['par_ref'] = record['fn', 0]['par_ref']  # TODO: check hard link files
                for i in (0, record['fncnt'] - 1):
                    if record['fn', i]['nspace'] == 0x1 or record['fn', i]['nspace'] == 0x3:
                        minirec['name'] = record['fn', i]['name']
                if minirec.get('name') is None:
                    minirec['name'] = record['fn', record['fncnt'] - 1]['name']

            if record['fncnt'] > 0:
                self.rw_lock.lockForWrite()
                if self.quit_flag:
                    self.rw_lock.unlock()
                    return
                self.mft[record_seq] = minirec
                self.get_folder_path(record_seq, record_seq)
                self.mft_seqs_flag_list[record_seq] = 2
                self.rw_lock.unlock()

                filename = self.mft[record_seq]['name']
                filepath = self.mft[record_seq]['path']
                filesize = record['fn', 0]['alloc_fsize']
                atime = record['fn', 0]['atime']  # .unixtime
                mtime = record['fn', 0]['mtime']  # .unixtime
                ctime = record['fn', 0]['ctime']  # .unixtime
                isFolder = bool(int(record['flags']) & 0x0002)  # decodeMFTrecordtype(record):

                self.sql_insert_mutex.lock()
                if isFolder:
                    # self.insert_db_SIGNAL.emit
                    self.sql_insert_queue.put([self.table_name,
                                               [filename, filepath,
                                                None, True,
                                                int(atime), int(mtime), int(ctime)],
                                               record_seq, self.mftsize, self.table_name]
                                              )
                else:
                    self.sql_insert_queue.put([self.table_name,
                                               [filename, filepath,
                                                filesize, False,
                                                int(atime), int(mtime), int(ctime)],
                                               record_seq, self.mftsize, self.table_name]
                                              )
                self.sql_insert_condition.wakeOne()
                self.sql_insert_mutex.unlock()

            else:
                minirec['name'] = "BAD_NAME"
                minirec['path'] = "/"
                minirec['par_ref'] = 5
                self.rw_lock.lockForWrite()
                self.mft[record_seq] = minirec
                self.mft_seqs_flag_list[record_seq] = 2
                self.rw_lock.unlock()

        try:
            self.file_mft.close()
        except:
            pass

    def quit(self):
        self.quit_flag = True
        self.wait(5000)
        try:
            self.file_mft.close()
        except:
            pass
        super(self.__class__, self).quit()


class MftSession(object):
    def __init__(self, filename, parent=None):
        super(self.__class__, self).__init__()

        # session.mft_options()
        class _seesion_option_:
            pass

        self.parent = parent
        self.options = _seesion_option_()
        self.options.filename = filename
        self.options.debug = False
        self.options.progress = False
        self.options.localtz = False  # report times using local timezone
        self.options.inmemory = False
        self.options.anomaly = False  # Check for STD create times that are before the FN create times

    def start(self, table_name, sql_insert_queue, sql_insert_mutex, sql_insert_condition):

        # table_name = "dfdfd"
        #
        # sql_insert_queue = Queue.Queue()
        # sql_insert_mutex = QtCore.QMutex()
        # sql_insert_condition = QtCore.QWaitCondition()

        self.rw_lock = QtCore.QReadWriteLock()

        mftsize = (os.path.getsize(self.options.filename)) / 1024
        self.mftsize = mftsize
        filename = self.options.filename

        self.mft_seqs_flag_list = [0] * self.mftsize  # 0 empty, 1 parsering, 2 done.
        self.mft = {}

        self.thread_no = max(1, QtCore.QThread.idealThreadCount())
        self.thread_no = 10  # 1'26''
        self.thread_no = 1  # 1'12''
        printself.thread_no
        self.thread_pool = [MftWorkerThread(self.mft, self.mft_seqs_flag_list, mftsize, filename, self.rw_lock,
                                            sql_insert_queue, sql_insert_mutex, sql_insert_condition,
                                            table_name, self.options,
                                            parent=self.parent) for _ in range(self.thread_no)]

        for thread in self.thread_pool:
            # thread.add_row_to_model_SIGNAL.connect(self.target_slot)
            # thread.update_progress_SIGNAL.connect(self.update_progress_slot)
            thread.start()

    def quit(self):
        for thread in self.thread_pool:
            thread.quit()

        if self.rw_lock.tryLockForWrite(10000):
            self.mft = {}
            self.rw_lock.unlock()
        else:
            print ("Fail to obtain write lock, timeout.")

    def wait(self, timeout_ms=1000):
        for thread in self.thread_pool:
            thread.wait(timeout_ms / self.thread_no)

    def isRunning(self):
        _tmp_running = False
        for thread in self.thread_pool:
            if thread.isRunning():
                _tmp_running = True
        print("_tmp_running: ", _tmp_running)
        return _tmp_running

    def __del__(self):
        self.quit()
        s = super(self.__class__, self)
        try:
            s.__del__
        except AttributeError:
            pass
        else:
            s.__del__(self)

# class MftSession_test(object):
#     def __init__(self, filename, parent=None):
#         super(self.__class__, self).__init__()
#
#         # session.mft_options()
#         class _seesion_option_():
#             pass
#
#         self.parent = parent
#         self.options = _seesion_option_()
#         self.options.filename = filename
#         self.options.debug = False
#         self.options.progress = False
#         self.options.localtz = False  # report times using local timezone
#         self.options.inmemory = False
#         self.options.anomaly = False  # Check for STD create times that are before the FN create times
#
#     def start(self, table_name, sql_insert_queue, sql_insert_mutex, sql_insert_condition):
#         # table_name = "dfdfd"
#         #
#         # sql_insert_queue = Queue.Queue()
#         # sql_insert_mutex = QtCore.QMutex()
#         # sql_insert_condition = QtCore.QWaitCondition()
#
#
#         self.rw_lock = QtCore.QReadWriteLock()
#
#         mftsize = long(os.path.getsize(self.options.filename)) / 1024
#         self.mftsize = mftsize
#         filename = self.options.filename
#
#         self.mft_seqs_flag_list = [0] * self.mftsize  # 0 empty, 1 parsering, 2 done.
#         self.mft = {}
#
#         self.thread_no = max(1, QtCore.QThread.idealThreadCount())
#         self.thread_no = 1
#
#         self.thread_pool = [MftWorkerThread(self.mft, self.mft_seqs_flag_list, mftsize, filename, self.rw_lock,
#                                             sql_insert_queue, sql_insert_mutex, sql_insert_condition,
#                                             table_name, self.options,
#                                             parent=self.parent) for _ in range(self.thread_no)]
#
#         for thread in self.thread_pool:
#             # thread.add_row_to_model_SIGNAL.connect(self.target_slot)
#             # thread.update_progress_SIGNAL.connect(self.update_progress_slot)
#             thread.run()
#
#
# if __name__ == "__main__":
#     # import cProfile
#     # cProfile.run("run_test()")
#     root_path = "/media/cc2/D_disk"
#     table_name = "aaaa"
#     import Queue
#
#     sql_insert_queue = Queue.Queue()
#     sql_insert_mutex = QtCore.QMutex()
#     sql_insert_condition = QtCore.QWaitCondition()
#
#     session = MftSession_test(os.path.join(root_path, "$MFT"))
#     session.start(table_name, sql_insert_queue, sql_insert_mutex, sql_insert_condition)
#
#
#     # session = MftSession(os.path.join(root_path, "$MFT"))
#     # session.start(table_name,  sql_insert_queue,  sql_insert_mutex,  sql_insert_condition)
#     # while session.isRunning():
#     #     session.wait(timeout_ms=1000)
#     #     print "Waiting... Running..."
#     #
#     #
#     # session.quit()
#     # del session
