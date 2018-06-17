#include "partition_information.h"



QList<Mnt_Info_Struct> Partition_Information::mnt_info;

QString Partition_Information::lsblk_history;
QSet<QString> Partition_Information::uuid_set;

QString Partition_Information::uuid_to_fstype(QString uuid)
{
    foreach(const Mnt_Info_Struct& item, mnt_info){
        if (item.uuid == uuid)
            return item.fstype;
    }
    return "unknow";
}

Partition_Information::Partition_Information()
{

    //    // https://github.com/1995eaton/dotfiles/blob/master/scripts/vim_test/test.cpp
    //    // windows: https://gist.github.com/a-andreyev/5815525
    //    struct mntent *m;
    //    FILE *f = NULL;
    //    f = setmntent(_PATH_MOUNTED,"r"); //open file for describing the mounted filesystems
    //    if(!f)
    //        printf("error:%s\n",strerror(errno));
    //    while ((m = getmntent(f)))        //read next line
    //    {
    // //        char *mnt_fsname;		/* Device or server for filesystem.  */
    // //        char *mnt_dir;		/* Directory mounted on.  */
    // //        char *mnt_type;		/* Type of filesystem: ufs, nfs, etc.  */
    // //        char *mnt_opts;		/* Comma-separated options for fs.  */
    // //        int mnt_freq;		/* Dump frequency (in days).  */
    // //        int mnt_passno;		/* Pass number for `fsck'.  */
    //      printf("Drive: %s, name: %s,type:  %s,opt:  %s\n",
    //             m->mnt_dir, m->mnt_fsname,m->mnt_type,m->mnt_opts );
    //      // Drive: /, name: /dev/mapper/isw_bbigfacfdg_RADI_Vol1p5,type:  ext4
    //      qDebug()<<"symLinkTarget: "<<
    //             QFileInfo(QString::fromLatin1(m->mnt_fsname)).symLinkTarget();
    //    }
    //    endmntent(f);   //close file for describing the mounted filesystems


    // QFileInfoList fileinfolist = QDir(QString(QStringLiteral("/dev/disk/by-uuid/"))).entryInfoList(QDir::AllEntries | QDir::NoDot | QDir::NoDotDot);

    // foreach (const QFileInfo &a, fileinfolist) {
    //     qDebug()<<a.fileName()<<a.symLinkTarget();
    //     // "111-111-111-111" "/dev/dm-5"
    // }

    // QFileInfoList fileinfolist = QDir(QString(QStringLiteral("/dev/disk/by-uuid/"))).entryInfoList(QDir::AllEntries | QDir::NoDot | QDir::NoDotDot);
    //     if (!fileinfolist.isEmpty()) {
    //         FILE *fsDescription = setmntent(_PATH_MOUNTED, "r");
    //         struct mntent entry;
    //         char buffer[512];
    //         QString uri;
    //         while ((getmntent_r(fsDescription, &entry, buffer, sizeof(buffer))) != NULL) {
    //             if (drive != QString::fromLatin1(entry.mnt_dir))
    //                 continue;
    //             int idx = fileinfolist.indexOf(QString::fromLatin1(entry.mnt_fsname));
    //             if (idx != -1)
    //                 uri = fileinfolist[idx].fileName();
    //             break;
    //         }
    //         endmntent(fsDescription);

    //         if (!uri.isEmpty())
    //             return uri;
    //}

}
bool Partition_Information::lsblk_prefix_path_init = false;
QString Partition_Information::lsblk_prefix_path = "";
bool Partition_Information::refresh_state(){
    // TODO: windows
    if (!lsblk_prefix_path_init)
    {
        QString app_path = QFileInfo(QCoreApplication::applicationFilePath()).path()  + QDir::separator() ;
        if(QFile::exists( app_path + "lsblk" ))
            lsblk_prefix_path = app_path  ;
        else
            lsblk_prefix_path = "";
        lsblk_prefix_path_init = true;
        qDebug()<<"lsblk path: "<<lsblk_prefix_path;
    }

    QProcess process;
    //  -s, --inverse        inverse dependencies
    //  -d, --nodeps         don't print slaves or holders
    process.start(lsblk_prefix_path + "lsblk -o MOUNTPOINT,LABEL,UUID,FSTYPE,name,MAJ:MIN -J -s -d");
    process.waitForFinished(-1); // will wait forever until finished

    QString stdout = process.readAllStandardOutput();

    if (stdout == lsblk_history)
    {
        return false;
    }
    lsblk_history = stdout;

    //     QList<Mnt_Info_Struct> mnt_tmp;
    mnt_info.clear();
    uuid_set.clear();

    QJsonDocument doc = QJsonDocument::fromJson(stdout.toUtf8());
    if (doc.isObject() && doc.object().contains("blockdevices"))
    {
        QString formattedJsonString = doc.toJson(QJsonDocument::Compact);
        QJsonArray array = doc.object()["blockdevices"].toArray();

        foreach (QJsonValue val, array) {
            QJsonObject obj = val.toObject();
            QString path = obj["mountpoint"].toString();
            QString label = obj["label"].toString();
            QString uuid = obj["uuid"].toString();
            QString fstype = obj["fstype"].toString();
            QString name = obj["name"].toString();

            if (uuid=="")
                uuid = name;
            if (QStringList({"swap"}).contains(fstype))
                continue;
            int maj=-1,min=-1;
            QStringList list;
            list = obj["maj:min"].toString().split(":");
            maj = list[0].toInt();
            min = list[1].toInt();

            uuid_set << uuid;
            mnt_info << Mnt_Info_Struct({
                                            path,
                                            label,
                                            uuid,
                                            fstype,
                                            name,
                                            maj,min});
        }

    }
    else
    {

    }
    return true;

}
