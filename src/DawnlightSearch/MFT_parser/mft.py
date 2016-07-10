#!/usr/bin/env python

# Author: David Kovar [dkovar <at> gmail [dot] com]
# Name: mft.py
#
# Copyright (c) 2010 David Kovar. All rights reserved.
# This software is distributed under the Common Public License 1.0
#
# Date: May 2013
#

from __future__ import print_function
import binascii
import struct
from optparse import OptionParser

try:
    import mftutils
except:
    from ..MFT_parser import mftutils

def set_default_options():
    parser = OptionParser()
    parser.set_defaults(debug=False)
    parser.set_defaults(localtz=None)
    parser.set_defaults(bodystd=False)
    parser.set_defaults(bodyfull=False)
    (options, args) = parser.parse_args()
    return options


def parse_record(record, raw_record, options):
    # record = {}
    record['filename'] = ''
    # record['notes'] = ''
    # record['ads'] = 0
    # record['datacnt'] = 0

    decodeMFTHeader(record, raw_record)

    # HACK: Apply the NTFS fixup on a 1024 byte record.
    # Note that the fixup is only applied locally to this function.
    if (record['seq_number'] == raw_record[510:512] and
                record['seq_number'] == raw_record[1022:1024]):
        raw_record = "%s%s%s%s" % (raw_record[:510],
                                   record['seq_attr1'],
                                   raw_record[512:1022],
                                   record['seq_attr2'])

    record_number = record['recordnum']

    # if options.debug:
    #     print '-->Record number: %d\n\tMagic: %s Attribute offset: %d Flags: %s Size:%d' % (
    #     record_number, record['magic'],
    #     record['attr_off'], hex(int(record['flags'])), record['size'])

    if record['magic'] == 0x44414142:
        if options.debug:
            print("BAAD MFT Record")
        record['baad'] = True
        return record

    if record['magic'] != 0x454c4946:
        if options.debug:
            print("Corrupt MFT Record")
        record['corrupt'] = True
        return record

    read_ptr = record['attr_off']

    # How should we preserve the multiple attributes? Do we need to preserve them all?
    while (read_ptr < 1024):

        ATRrecord = decodeATRHeader(raw_record[read_ptr:])
        if ATRrecord['type'] == 0xffffffff:  # End of attributes
            break

        if ATRrecord['nlen'] > 0:
            bytes = raw_record[
                    read_ptr + ATRrecord['name_off']:read_ptr + ATRrecord['name_off'] + ATRrecord['nlen'] * 2]
            ATRrecord['name'] = bytes.decode('utf-16').encode('utf-8')
        else:
            ATRrecord['name'] = ''

        if options.debug:
            print("Attribute type: %x Length: %d Res: %x" % (ATRrecord['type'], ATRrecord['len'], ATRrecord['res']))

            # if ATRrecord['type'] == 0x10:                   # Standard Information
            # if options.debug:
            #     print "Stardard Information:\n++Type: %s Length: %d Resident: %s Name Len:%d Name Offset: %d" % \
            #          (hex(int(ATRrecord['type'])),ATRrecord['len'],ATRrecord['res'],ATRrecord['nlen'],ATRrecord['name_off'])
            # SIrecord = decodeSIAttribute(raw_record[read_ptr+ATRrecord['soff']:], options.localtz)
            # record['si'] = SIrecord
            # if options.debug:
            #     print "++CRTime: %s\n++MTime: %s\n++ATime: %s\n++EntryTime: %s" % \
            #        (SIrecord['crtime'].dtstr, SIrecord['mtime'].dtstr, SIrecord['atime'].dtstr, SIrecord['ctime'].dtstr)

        # elif ATRrecord['type'] == 0x20:                 # Attribute list
        #     if options.debug:
        #         print "Attribute list"
        #     if ATRrecord['res'] == 0:
        #         ALrecord = decodeAttributeList(raw_record[read_ptr+ATRrecord['soff']:], record)
        #         record['al'] = ALrecord
        #         if options.debug:
        #             print "Name: %s"  % (ALrecord['name'])
        #     else:
        #         if options.debug:
        #             print "Non-resident Attribute List?"
        #         record['al'] = None

        if ATRrecord['type'] == 0x30:  # File name
            if options.debug: print("File name record")
            FNrecord = decodeFNAttribute(raw_record[read_ptr + ATRrecord['soff']:], options.localtz, record)
            record['fn', record['fncnt']] = FNrecord
            if options.debug: print("Name: %s (%d)" % (FNrecord['name'], record['fncnt']))
            record['fncnt'] += + 1
            # if FNrecord['crtime'] != 0:
            #     if options.debug: print "\tCRTime: %s MTime: %s ATime: %s EntryTime: %s" % (FNrecord['crtime'].dtstr,
            #             FNrecord['mtime'].dtstr, FNrecord['atime'].dtstr, FNrecord['ctime'].dtstr)

        # elif ATRrecord['type'] == 0x40:                 #  Object ID
        #     ObjectIDRecord = decodeObjectID(raw_record[read_ptr+ATRrecord['soff']:])
        #     record['objid'] = ObjectIDRecord
        #     if options.debug: print "Object ID"

        # elif ATRrecord['type'] == 0x50:                 # Security descriptor
        #     record['sd'] = True
        #     if options.debug: print "Security descriptor"

        # elif ATRrecord['type'] == 0x60:                 # Volume name
        #     record['volname'] = True
        #     if options.debug: print "Volume name"

        # elif ATRrecord['type'] == 0x70:                 # Volume information
        #     if options.debug: print "Volume info attribute"
        #     VolumeInfoRecord = decodeVolumeInfo(raw_record[read_ptr+ATRrecord['soff']:],options)
        #     record['volinfo'] = VolumeInfoRecord

        # elif ATRrecord['type'] == 0x80:                 # Data
        #     if ATRrecord['name'] != '':
        #         # record['data_name',record['ads']] = ATRrecord['name']
        #         record['ads'] = record['ads'] + 1
        #     if ATRrecord['res'] == 0:
        #         DataAttribute = decodeDataAttribute(raw_record[read_ptr+ATRrecord['soff']:],ATRrecord)
        #     else:
        #         DataAttribute = {}
        #         # DataAttribute['ndataruns'] = ATRrecord['ndataruns']
        #         # DataAttribute['dataruns'] = ATRrecord['dataruns']
        #         # DataAttribute['drunerror'] = ATRrecord['drunerror']
        #     record['data',record['datacnt']] = DataAttribute
        #     record['datacnt'] = record['datacnt'] + 1
        #
        #     if options.debug: print "Data attribute"

        # elif ATRrecord['type'] == 0x90:                 # Index root
        #     record['indexroot'] = True
        #     if options.debug: print "Index root"

        # elif ATRrecord['type'] == 0xA0:                 # Index allocation
        #     record['indexallocation'] = True
        #     if options.debug: print "Index allocation"

        # elif ATRrecord['type'] == 0xB0:                 # Bitmap
        #     record['bitmap'] = True
        #     if options.debug: print "Bitmap"

        # elif ATRrecord['type'] == 0xC0:                 # Reparse point
        #     record['reparsepoint'] = True
        #     if options.debug: print "Reparse point"

        # elif ATRrecord['type'] == 0xD0:                 # EA Information
        #     record['eainfo'] = True
        #     if options.debug: print "EA Information"

        # elif ATRrecord['type'] == 0xE0:                 # EA
        #     record['ea'] = True
        #     if options.debug: print "EA"

        # elif ATRrecord['type'] == 0xF0:                 # Property set
        #     record['propertyset'] = True
        #     if options.debug: print "Property set"

        # elif ATRrecord['type'] == 0x100:                 # Logged utility stream
        #     record['loggedutility'] = True
        #     if options.debug: print "Logged utility stream"

        # else:
        #     if options.debug: print "Found an unknown attribute"

        if ATRrecord['len'] > 0:
            read_ptr = read_ptr + ATRrecord['len']
        else:
            if options.debug: print("ATRrecord->len < 0, exiting loop")
            break

    # if options.anomaly:
    #     anomalyDetect(record)

    return record


# def add_note(record, s):
#     if record['notes'] == '':
#         record['notes'] = "%s" % s
#     else:
#         record['notes'] = "%s | %s |" % (record['notes'], s)


def decodeMFTHeader(record, raw_record):
    record['magic'] = struct.unpack("<I", raw_record[:4])[0]
    record['upd_off'] = struct.unpack("<H", raw_record[4:6])[0]
    # record['upd_cnt'] = struct.unpack("<H",raw_record[6:8])[0]
    # record['lsn'] = struct.unpack("<d",raw_record[8:16])[0]
    # record['seq'] = struct.unpack("<H",raw_record[16:18])[0]
    # record['link'] = struct.unpack("<H",raw_record[18:20])[0]
    record['attr_off'] = struct.unpack("<H", raw_record[20:22])[0]
    record['flags'] = struct.unpack("<H", raw_record[22:24])[0]
    # record['size'] = struct.unpack("<I",raw_record[24:28])[0]
    record['alloc_sizef'] = struct.unpack("<I", raw_record[28:32])[0]
    # record['base_ref'] = struct.unpack("<Lxx",raw_record[32:38])[0]
    # record['base_seq'] = struct.unpack("<H",raw_record[38:40])[0]
    # record['next_attrid'] = struct.unpack("<H",raw_record[40:42])[0]
    # record['f1'] = raw_record[42:44]                            # Padding
    record['recordnum'] = struct.unpack("<I", raw_record[44:48])[0]  # Number of this MFT Record
    record['seq_number'] = raw_record[48:50]  # Sequence number
    # Sequence attributes location are hardcoded since the record size is hardcoded too.
    # The following two lines are subject to NTFS versions. See:
    # https://github.com/libyal/libfsntfs/blob/master/documentation/New%20Technologies%20File%20System%20(NTFS).asciidoc#mft-entry-header
    if record['upd_off'] == 42:
        record['seq_attr1'] = raw_record[44:46]  # Sequence attribute for sector 1
        record['seq_attr2'] = raw_record[46:58]  # Sequence attribute for sector 2
    else:
        record['seq_attr1'] = raw_record[50:52]  # Sequence attribute for sector 1
        record['seq_attr2'] = raw_record[52:54]  # Sequence attribute for sector 2
    record['fncnt'] = 0  # Counter for number of FN attributes
    # record['datacnt'] = 0                            # Counter for number of $DATA attributes


def decodeMFTmagic(record):
    if record['magic'] == 0x454c4946:
        return "Good"
    elif record['magic'] == 0x44414142:
        return 'Bad'
    elif record['magic'] == 0x00000000:
        return 'Zero'
    else:
        return 'Unknown'


# decodeMFTisactive and decodeMFTrecordtype both look at the flags field in the MFT header.
# The first bit indicates if the record is active or inactive. The second bit indicates if it
# is a file or a folder.
#
# I had this coded incorrectly initially. Spencer Lynch identified and fixed the code. Many thanks!

def decodeMFTisactive(record):
    if record['flags'] & 0x0001:
        return 'Active'
    else:
        return 'Inactive'


def decodeMFTrecordtype(record):
    tmpBuffer = int(record['flags'])
    if int(record['flags']) & 0x0002:
        tmpBuffer = 'Folder'
    else:
        tmpBuffer = 'File'
    if int(record['flags']) & 0x0004:
        tmpBuffer = "%s %s" % (tmpBuffer, '+ Unknown1')
    if int(record['flags']) & 0x0008:
        tmpBuffer = "%s %s" % (tmpBuffer, '+ Unknown2')

    return tmpBuffer


def decodeATRHeader(s):
    d = {}
    d['type'] = struct.unpack("<L", s[:4])[0]
    if d['type'] == 0xffffffff:
        return d
    d['len'] = struct.unpack("<L", s[4:8])[0]
    d['res'] = struct.unpack("B", s[8])[0]
    d['nlen'] = struct.unpack("B", s[9])[0]
    d['name_off'] = struct.unpack("<H", s[10:12])[0]
    d['flags'] = struct.unpack("<H", s[12:14])[0]
    # d['id'] = struct.unpack("<H",s[14:16])[0]
    if d['res'] == 0:
        # d['ssize'] = struct.unpack("<L",s[16:20])[0]            # dwLength
        d['soff'] = struct.unpack("<H", s[20:22])[0]  # wAttrOffset
        # d['idxflag'] = struct.unpack("B",s[22])[0]              # uchIndexedTag
        # padding = struct.unpack("B",s[23])[0]                   # Padding
    else:
        pass
        # d['start_vcn'] = struct.unpack("<Lxxxx",s[16:24])[0]    # n64StartVCN
        # d['last_vcn'] = struct.unpack("<Lxxxx",s[24:32])[0]     # n64EndVCN
        # d['start_vcn'] = struct.unpack("<Q",s[16:24])[0]    # n64StartVCN
        # d['last_vcn'] = struct.unpack("<Q",s[24:32])[0]     # n64EndVCN
        # d['run_off'] = struct.unpack("<H",s[32:34])[0]          # wDataRunOffset (in clusters, from start of partition?)
        # d['compsize'] = struct.unpack("<H",s[34:36])[0]         # wCompressionSize
        # padding = struct.unpack("<I",s[36:40])[0]               # Padding
        # d['allocsize'] = struct.unpack("<Lxxxx",s[40:48])[0]    # n64AllocSize
        # d['realsize'] = struct.unpack("<Lxxxx",s[48:56])[0]     # n64RealSize
        # d['streamsize'] = struct.unpack("<Lxxxx",s[56:64])[0]   # n64StreamSize
        # (d['ndataruns'],d['dataruns'],d['drunerror']) = unpack_dataruns(s[64:])

    return d


# # Dataruns - http://inform.pucp.edu.pe/~inf232/Ntfs/ntfs_doc_v0.5/concepts/data_runs.html
# def unpack_dataruns(str):
#     dataruns = []
#     numruns = 0
#     pos = 0
#     prevoffset = 0
#     error = ''
#
#     c_uint8 = ctypes.c_uint8
#
#     class Length_bits(ctypes.LittleEndianStructure):
#         _fields_ = [
#             ("lenlen", c_uint8, 4),
#             ("offlen", c_uint8, 4),
#         ]
#
#     class Lengths(ctypes.Union):
#         _fields_ = [("b", Length_bits),
#                     ("asbyte", c_uint8)]
#
#     lengths = Lengths()
#
#     # mftutils.hexdump(str,':',16)
#
#     while (True):
#         lengths.asbyte = struct.unpack("B", str[pos])[0]
#         pos += 1
#         if lengths.asbyte == 0x00:
#             break
#
#         if (lengths.b.lenlen > 6 or lengths.b.lenlen == 0):
#             error = "Datarun oddity."
#             break
#
#         len = bitparse.parse_little_endian_signed(str[pos:pos + lengths.b.lenlen])
#
#         # print lengths.b.lenlen, lengths.b.offlen, len
#         pos += lengths.b.lenlen
#
#         if (lengths.b.offlen > 0):
#             offset = bitparse.parse_little_endian_signed(str[pos:pos + lengths.b.offlen])
#             offset = offset + prevoffset
#             prevoffset = offset
#             pos += lengths.b.offlen
#         else:  # Sparse
#             offset = 0
#             pos += 1
#
#         dataruns.append([len, offset])
#         numruns += 1
#
#
#         # print "Lenlen: %d Offlen: %d Len: %d Offset: %d" % (lengths.b.lenlen, lengths.b.offlen, len, offset)
#
#     return numruns, dataruns, error


def decodeSIAttribute(s, localtz):
    d = {}
    # d['crtime'] = mftutils.WindowsTime(struct.unpack("<L",s[:4])[0],struct.unpack("<L",s[4:8])[0],localtz)
    d['mtime'] = mftutils.WindowsTime(struct.unpack("<L", s[8:12])[0], struct.unpack("<L", s[12:16])[0], localtz)
    d['ctime'] = mftutils.WindowsTime(struct.unpack("<L", s[16:20])[0], struct.unpack("<L", s[20:24])[0], localtz)
    d['atime'] = mftutils.WindowsTime(struct.unpack("<L", s[24:28])[0], struct.unpack("<L", s[28:32])[0], localtz)
    # d['dos'] = struct.unpack("<I",s[32:36])[0]          # 4
    # d['maxver'] = struct.unpack("<I",s[36:40])[0]       # 4
    # d['ver'] = struct.unpack("<I",s[40:44])[0]          # 4
    # d['class_id'] = struct.unpack("<I",s[44:48])[0]     # 4
    # d['own_id'] = struct.unpack("<I",s[48:52])[0]       # 4
    # d['sec_id'] = struct.unpack("<I",s[52:56])[0]       # 4
    # d['quota'] = struct.unpack("<d",s[56:64])[0]        # 8
    # d['usn'] = struct.unpack("<d",s[64:72])[0]          # 8 - end of date to here is 40

    return d


def decodeFNAttribute(s, localtz, record):
    hexFlag = False
    # File name attributes can have null dates.

    d = {}
    d['par_ref'] = struct.unpack("<Lxx", s[:6])[
        0]  # Parent reference nummber + seq number = 8 byte "File reference to the parent directory."
    # d['par_seq'] = struct.unpack("<H",s[6:8])[0]        # Parent sequence number
    # d['crtime'] = mftutils.WindowsTime(struct.unpack("<L",s[8:12])[0],struct.unpack("<L",s[12:16])[0],localtz)
    d['mtime'] = mftutils.WindowsTime(struct.unpack("<L", s[16:20])[0], struct.unpack("<L", s[20:24])[0], localtz)
    d['ctime'] = mftutils.WindowsTime(struct.unpack("<L", s[24:28])[0], struct.unpack("<L", s[28:32])[0], localtz)
    d['atime'] = mftutils.WindowsTime(struct.unpack("<L", s[32:36])[0], struct.unpack("<L", s[36:40])[0], localtz)
    d['alloc_fsize'] = struct.unpack("<q", s[40:48])[0]
    # d['real_fsize'] = struct.unpack("<q",s[48:56])[0]
    d['flags'] = struct.unpack("<d", s[56:64])[0]  # 0x01=NTFS, 0x02=DOS
    d['nlen'] = struct.unpack("B", s[64])[0]
    d['nspace'] = struct.unpack("B", s[65])[0]

    bytes = s[66:66 + d['nlen'] * 2]
    try:
        d['name'] = bytes.decode('utf-16').encode('utf-8')
    except:
        d['name'] = 'UnableToDecodeFilename'

    return d


def decodeAttributeList(s, record):
    hexFlag = False

    d = {}
    d['type'] = struct.unpack("<I", s[:4])[0]  # 4
    d['len'] = struct.unpack("<H", s[4:6])[0]  # 2
    d['nlen'] = struct.unpack("B", s[6])[0]  # 1
    # d['f1'] = struct.unpack("B",s[7])[0]                    # 1
    # d['start_vcn'] = struct.unpack("<d",s[8:16])[0]         # 8
    d['file_ref'] = struct.unpack("<Lxx", s[16:22])[0]  # 6
    # d['seq'] = struct.unpack("<H",s[22:24])[0]              # 2
    # d['id'] = struct.unpack("<H",s[24:26])[0]               # 4

    bytes = s[26:26 + d['nlen'] * 2]
    d['name'] = bytes.decode('utf-16').encode('utf-8')

    return d

# def decodeVolumeInfo(s, options):
#     d = {}
#     # d['f1'] = struct.unpack("<d",s[:8])[0]                  # 8
#     d['maj_ver'] = struct.unpack("B", s[8])[0]  # 1
#     d['min_ver'] = struct.unpack("B", s[9])[0]  # 1
#     d['flags'] = struct.unpack("<H", s[10:12])[0]  # 2
#     d['f2'] = struct.unpack("<I", s[12:16])[0]  # 4
#
#     if (options.debug):
#         print "+Volume Info"
#         print "++F1%d" % d['f1']
#         print "++Major Version: %d" % d['maj_ver']
#         print "++Minor Version: %d" % d['min_ver']
#         print "++Flags: %d" % d['flags']
#         print "++F2: %d" % d['f2']
#
#     return d


# Decode a Resident Data Attribute
# def decodeDataAttribute(s, ATRrecord):
#
#         d = {}
#         d['data'] = s[:ATRrecord['ssize']]
#
# #        print 'Data: ', d['data']
#         return d


# def decodeObjectID(s):
#     d = {}
#     d['objid'] = ObjectID(s[0:16])
#     d['orig_volid'] = ObjectID(s[16:32])
#     d['orig_objid'] = ObjectID(s[32:48])
#     d['orig_domid'] = ObjectID(s[48:64])
#
#     return d


# def ObjectID(s):
#     objstr = ''
#     if s == 0:
#         objstr = 'Undefined'
#     else:
#         objstr = "%s-%s-%s-%s-%s" % (binascii.hexlify(s[0:4]), binascii.hexlify(s[4:6]),
#                                      binascii.hexlify(s[6:8]), binascii.hexlify(s[8:10]), binascii.hexlify(s[10:16]))
#
#     return objstr
