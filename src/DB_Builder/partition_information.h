#ifndef PARTITION_INFORMATION_H
#define PARTITION_INFORMATION_H

// #include <QFileInfoList>
// #include <mntent.h>
#include <QProcess>
#include "globals.h"
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>
//class UUID_HEADER_class
//{
//public:
//    const int  included=0;
//    const int  path=1;
//    const int  label=2;
//    const int  uuid=3;
//    const int  alias=4;
//    const int  fstype=5;
//    const int  name=6;
//    const int  major_dnum=7;
//    const int  minor_dnum=8;
//    const int  rows=9;
//    const int  updatable=10;
//    const int  processbar=11;
//};

//struct mntent
//  {
//    char *mnt_fsname;		/* Device or server for filesystem.  */
//    char *mnt_dir;		/* Directory mounted on.  */
//    char *mnt_type;		/* Type of filesystem: ufs, nfs, etc.  */
//    char *mnt_opts;		/* Comma-separated options for fs.  */
//    int mnt_freq;		/* Dump frequency (in days).  */
//    int mnt_passno;		/* Pass number for `fsck'.  */
//  };
struct Mnt_Info_Struct
{
    // lsblk -o MOUNTPOINT,LABEL,UUID,FSTYPE,name,MAJ:MIN -r
    QString path; // *mnt_dir,     QStorageInfo.displayName:     directory mounted on
    QString label; //                                      :     NTFS vol only,
    QString uuid; // ------------, symLinkTarget of /dev/disk/by-uuid/ <-> mnt_fsname :  device uuid
    QString fstype;// *mnt_type,   QStorageInfo.fileSystemType:  Type of filesystem: ufs, nfs, etc.
    QString name; //  *mnt_fsname, QStorageInfo.device     :     device or server name
    int maj;
    int min;
};

class Partition_Information
{
public:
    static QList<Mnt_Info_Struct> mnt_info ;
    static bool refresh_state();
    static QString lsblk_history;
    static QString uuid_to_fstype(QString);
    static QSet<QString> uuid_set;
    Partition_Information();
};

#endif // PARTITION_INFORMATION_H
