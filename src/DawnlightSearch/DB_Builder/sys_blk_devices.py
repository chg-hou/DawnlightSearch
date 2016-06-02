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


class LinuxDevices_old:
    blockdevices_id = None
    blockdevices_name = None
    NTFSblock = None
    NTFSid = None
    mountPath_dev = None
    mountPath_path = None
    device_id_path = None

    def __init__(self):
        import collections
        def default_factory_1():
            return set()

        self.device_id_path = collections.defaultdict(default_factory_1)

        self.refresh()

    def refresh(self):
        # print os.popen('lsblk -o name,MAJ:MIN,UUID,LABEL,FSTYPE ').read()
        # print os.popen('lsblk -o name,MAJ:MIN,UUID,LABEL,FSTYPE -J').read()
        # lsblk -f
        # https://wiki.archlinux.org/index.php/Fstab#UUIDs
        # https://wiki.debian.org/Part-UUID#Via_UUIDs
        BlockInfo = json.load(os.popen('lsblk -o name,MAJ:MIN,UUID,LABEL,FSTYPE,MOUNTPOINT -J'))

        blockdevices_id = {}
        blockdevices_name = {}
        NTFSblock = []
        NTFSid = []
        mountPath_dev = {}
        mountPath_path = {}
        mountNTFSpath = []
        for device in BlockInfo['blockdevices']:
            major, minor = map(int, device['maj:min'].split(':'))
            if device['fstype']:  # unnecessary
                blockdevices_id[major, minor] = device
                blockdevices_name[device['name']] = device
            if not 'children' in device:
                continue
            # blockdevices.append(device)
            for child in device['children']:
                # print device['fstype']
                if not child['fstype']:  # filter out root/special partition
                    continue
                major, minor = map(int, child['maj:min'].split(':'))
                blockdevices_id[major, minor] = child
                blockdevices_name[child['name']] = child
                if (child['fstype'] == 'ntfs'):
                    NTFSid.append((major, minor))
                    NTFSblock.append(child['name'])
                    if (child['mountpoint']):
                        mountNTFSpath.append(child['mountpoint'])
                        # blockdevices.append(child)
        print '\nblockdevices_id:'
        for i, j in blockdevices_id.items():
            print i, j
        print '\nblockdevices_name:'
        for i, j in blockdevices_name.items():
            print i, j

        print '\n', 'NTFSblock:'
        print NTFSblock
        print '\n', 'NTFSid:'
        print NTFSid
        print '\n', 'mountNTFSpath:'
        print mountNTFSpath

        # # cat  /proc/self/mounts | grep /dev/sd
        # # mount | grep /dev/sd
        # for line in os.popen('cat /proc/self/mounts | grep /dev/s').read().split('\n'):
        #     if '/dev/' in line:
        #         dev,path = line.split(' ')[0:2]
        #         dev = dev.replace('/dev/','')
        #         mountPath_dev[dev] = path
        #         mountPath_path[path] = dev
        # mountNTFSpath = [mountPath_dev[x] for x in NTFSblock if x in mountPath_dev]
        # print '==============='
        # print 'mountPath_dev: \n', mountPath_dev
        #
        # print 'mountPath_path: \n', mountPath_path,'\nmountNTFSpath:\n', mountNTFSpath

        # NTFSblock:
        # [u'sda1', u'sda5', u'sda6', u'sda7', u'sda8', u'sda9']
        # [(8, 1), (8, 5), (8, 6), (8, 7), (8, 8), (8, 9)]
        # ===============
        # mountPath:  {'sda10': '/', '/boot/efi': 'sda2', '/': 'sda10', 'sda2': '/boot/efi', '/media/cc/D_disk': 'sda8', 'sda8': '/media/cc/D_disk'}
        # ['/media/cc/D_disk']

        # Todo: mount point     df -a --output=source,target


        self.blockdevices_id = blockdevices_id
        self.blockdevices_name = blockdevices_name
        self.NTFSblock = NTFSblock
        self.NTFSid = NTFSid
        self.mountPath_dev = mountPath_dev
        self.mountPath_path = mountPath_path
        self.mountNTFSpath = mountNTFSpath

    def mounted_uuid(self):
        return [self.blockdevices_name[dev]['uuid'] \
                for dev in self.mountPath_dev]

    def deviceID_to_UUID(self, device_id):
        if device_id in self.blockdevices_id:
            return self.blockdevices_id[device_id]['uuid']
        else:
            return "%s:%s" % (device_id[0], device_id[1])


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
                print(e.message)
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
    # print(a.mounted_uuid())
