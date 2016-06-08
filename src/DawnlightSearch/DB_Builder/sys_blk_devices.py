# -*- coding: utf-8 -*-
import os, json, sys

'''
blockdevices_id:


blockdevices_name:

NTFSblock:
[u'sda1', u'sda5', u'sda6', u'sda7', u'sda8', u'sda9']

NTFSid:
[(8, 1), (8, 5), (8, 6), (8, 7), (8, 8), (8, 9)]
===============
mountPath_dev:
{'sda2': '/boot/efi', 'sda10': '/', 'sda8': '/media/cc/D_disk'}

mountPath_path:
{'/media/cc/D_disk': 'sda8', '/boot/efi': 'sda2', '/': 'sda10'}

mountNTFSpath:
['/media/cc/D_disk']
'''

import collections, threading
import os, json, time

class LinuxDevices(object):
    mount_target_path = set()
    blockdevices_id = {}
    deviceDict = {}

    lsblk_history = ''
    df_history = ''
    timestamp = 0

    mutex = threading.Lock()

    def __init__(self):
        def default_factory_1():
            return set()

        self.device_id_path = collections.defaultdict(default_factory_1)
        # self.refresh()

    def refresh(self):
        self.refresh_state()

    @staticmethod
    def refresh_state():
        LinuxDevices.mutex.acquire()
        blockinfo = os.popen('lsblk -o name,MAJ:MIN,UUID,LABEL,FSTYPE,MOUNTPOINT -J').read()
        df_all = os.popen('df -a --output=source,target,fstype').read()

        if blockinfo == LinuxDevices.lsblk_history and df_all == LinuxDevices.df_history:
            LinuxDevices.mutex.release()
            return False
        else:
            LinuxDevices.lsblk_history = blockinfo
            LinuxDevices.df_history = df_all
            LinuxDevices.timestamp = time.time()

        blockinfo = json.loads(blockinfo)
        df_source = os.popen('df -a --output=source').readlines()[1:]
        df_target = os.popen('df -a --output=target').readlines()[1:]
        df_fstype = os.popen('df -a --output=fstype').readlines()[1:]

        mount_target_path = set()
        blockdevices_id = {}
        deviceDict = {}

        df_source = [x[:-1] for x in df_source]
        df_target = [x[:-1] for x in df_target]
        df_fstype = [x[:-1] for x in df_fstype]

        for row in range(len(df_target)):

            target, source, fstype = df_target[row], df_source[row], df_fstype[row]
            try:
                l_stat = os.lstat(target)
            except Exception as e:
                print("Fail to stat: " + target)
                print(str(e))
                continue
            major_dnum = os.major(l_stat.st_dev)
            minor_dnum = os.minor(l_stat.st_dev)

            deviceDict[(major_dnum, minor_dnum)] = {}
            deviceDict[(major_dnum, minor_dnum)]['name'] = source
            deviceDict[(major_dnum, minor_dnum)]['mountpoint'] = target
            deviceDict[(major_dnum, minor_dnum)]['fstype'] = fstype

            # will be overwritten by lsblk
            deviceDict[(major_dnum, minor_dnum)]['uuid'] = "%s:%s" % (major_dnum, minor_dnum)
            deviceDict[(major_dnum, minor_dnum)]['label'] = ""
            deviceDict[(major_dnum, minor_dnum)]['isblock'] = False

            mount_target_path.add(target)
            # print major_dnum, minor_dnum, target, source, fstype

        for device in blockinfo['blockdevices']:
            major, minor = map(int, device['maj:min'].split(':'))
            if device['fstype']:  # unnecessary
                blockdevices_id[major, minor] = device
                blockdevices_id[major, minor]['isblock'] = True
            if 'children' in device:
                for child in device['children']:
                    if not child['fstype']:  # filter out root/special partition
                        continue
                    major, minor = map(int, child['maj:min'].split(':'))
                    blockdevices_id[major, minor] = child
                    blockdevices_id[major, minor]['isblock'] = True

        deviceDict.update(blockdevices_id)

        LinuxDevices.mount_target_path = mount_target_path
        LinuxDevices.blockdevices_id = blockdevices_id
        LinuxDevices.deviceDict = deviceDict

        LinuxDevices.mutex.release()
        return True

    def mounted_uuid(self):
        return [self.blockdevices_name[dev]['uuid'] \
                for dev in self.mountPath_dev]

    def deviceID_to_UUID(self, device_id):
        if device_id in self.blockdevices_id:
            return self.blockdevices_id[device_id]['uuid']
        else:
            return "%s:%s" % (device_id[0], device_id[1])


if sys.platform.startswith('darwin'):
    pass
elif os.name == 'nt':
    pass  # TODO: handle in windows
elif os.name == 'posix':
    SystemDevices = LinuxDevices

if __name__ == '__main__':
    a = SystemDevices()
    a.refresh_state()
    # print(a.mounted_uuid())
