#include "partition_information.h"



QList<Mnt_Info_Struct> Partition_Information::mnt_info;
QString Partition_Information::lsblk_history;
QSet<QString> Partition_Information::uuid_set;

QFileInfo Partition_Information::mtab_info;
bool Partition_Information::mtab_use_flag;
QDateTime Partition_Information::mtab_lastModified;

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

        // ==========================================================

        mtab_info = QFileInfo("/etc/mtab");
        if (!mtab_info.exists())
            mtab_use_flag=false;
        else
            mtab_use_flag=true;
        // https://doc.qt.io/qt-5/qfileinfo.html#details
        // There is a function that refreshes the file information: refresh(). If you want to switch off a QFileInfo's caching and force it to access the file system every time you request information from it call setCaching(false).
        mtab_info.setCaching(false);

    }

    QProcess process;
    //  -s, --inverse        inverse dependencies
    //  -d, --nodeps         don't print slaves or holders
    process.start(lsblk_prefix_path + "lsblk -o MOUNTPOINT,LABEL,UUID,PARTUUID,FSTYPE,name,MAJ:MIN -J -s -d");
    process.waitForFinished(-1); // will wait forever until finished

    QString stdout = process.readAllStandardOutput();

    if (stdout == lsblk_history
            && (!mtab_use_flag || mtab_lastModified == mtab_info.lastModified() )  //mtab
            )
    {
        return false;
    }
    lsblk_history = stdout;
    if (mtab_use_flag) mtab_lastModified = mtab_info.lastModified();              //mtab

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
            QString uuid = obj["uuid"].toString() +":"+ obj["partuuid"].toString();
            QString fstype = obj["fstype"].toString();
            QString name = obj["name"].toString();

            qDebug( )<< path<<" "<<label<<" "<<uuid<<" "<<fstype<<" "<<name;
            if (EXCLUDED_MOUNT_PATH_RE.match(path).hasMatch())
            {
                qDebug()<<" xxx reg match, lsblk skip xxx" <<  path;
                continue;
            }

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

            for(Mnt_Info_Struct tmp : mnt_info){
                if (tmp.path!="" && path=="" && tmp.uuid.split(":").first()==uuid.split(":").first() )
                {
                    path = tmp.path;
                    break;
                }
            }

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

    if (mtab_use_flag)
    {
        QSet<QString> mount_path_set;
        for(Mnt_Info_Struct i_mnt_info: mnt_info)
            mount_path_set<<i_mnt_info.path;

        struct mntent *m;
        FILE *f = NULL;
        f = setmntent(_PATH_MOUNTED,"r"); //open file for describing the mounted filesystems
        if(!f)
            printf("error:%s\n",strerror(errno));
        while ((m = getmntent(f)))        //read next line
        {
     //        char *mnt_fsname;		/* Device or server for filesystem.  */
     //        char *mnt_dir;		/* Directory mounted on.  */
     //        char *mnt_type;		/* Type of filesystem: ufs, nfs, etc.  */
     //        char *mnt_opts;		/* Comma-separated options for fs.  */
     //        int mnt_freq;		/* Dump frequency (in days).  */
     //        int mnt_passno;		/* Pass number for `fsck'.  */
//          qDebug("Drive: %s,   name: %s,  type:  %s,   opt:  %s",
//                 m->mnt_dir, m->mnt_fsname,m->mnt_type,m->mnt_opts );
          // Drive: /, name: /dev/mapper/isw_bbigfacfdg_RADI_Vol1p5,type:  ext4
//          qDebug()<<"symLinkTarget: "<<
//                 QFileInfo(QString::fromLatin1(m->mnt_fsname)).symLinkTarget();
          qDebug("Drive: %s,   name: %s,  type:  %s",
                 m->mnt_dir, m->mnt_fsname,m->mnt_type );
          if (mount_path_set.contains(m->mnt_dir))
          {
              qDebug()<<"=============== included";
          }
          else
          {
              if (EXCLUDED_MOUNT_PATH_RE.match(m->mnt_dir).hasMatch())
              {
                  qDebug()<<" xxx reg match, mtab skip xxx" <<  m->mnt_dir;
                  continue;
              }
              //              qDebug()<<"xxxxxxxxxxxx not included";
              uuid_set << m->mnt_dir;
              mnt_info << Mnt_Info_Struct({
                                              m->mnt_dir,//path,
                                              m->mnt_fsname,//label,
                                              m->mnt_dir,//uuid,
                                              m->mnt_type,//fstype,
                                              m->mnt_fsname,//name,
                                              -1,-1});
          }
        }
        endmntent(f);   //close file for describing the mounted filesystems
    }



    return true;

}
//bool Partition_Information::refresh_state(){
//    // TODO: windows
//    if (!lsblk_prefix_path_init)
//    {
//        QString app_path = QFileInfo(QCoreApplication::applicationFilePath()).path()  + QDir::separator() ;
//        if(QFile::exists( app_path + "lsblk" ))
//            lsblk_prefix_path = app_path  ;
//        else
//            lsblk_prefix_path = "";
//        lsblk_prefix_path_init = true;
//        qDebug()<<"lsblk path: "<<lsblk_prefix_path;
//    }

//    QProcess process;
//    //  -s, --inverse        inverse dependencies
//    //  -d, --nodeps         don't print slaves or holders
//    process.start(lsblk_prefix_path + "lsblk -o MOUNTPOINT,LABEL,UUID,FSTYPE,name,MAJ:MIN -J -s -d");
//    process.waitForFinished(-1); // will wait forever until finished

//    QString stdout = process.readAllStandardOutput();

//    if (stdout == lsblk_history)
//    {
//        return false;
//    }
//    lsblk_history = stdout;

//    //     QList<Mnt_Info_Struct> mnt_tmp;
//    mnt_info.clear();
//    uuid_set.clear();

//    QJsonDocument doc = QJsonDocument::fromJson(stdout.toUtf8());
//    if (doc.isObject() && doc.object().contains("blockdevices"))
//    {
//        QString formattedJsonString = doc.toJson(QJsonDocument::Compact);
//        QJsonArray array = doc.object()["blockdevices"].toArray();

//        foreach (QJsonValue val, array) {
//            QJsonObject obj = val.toObject();
//            QString path = obj["mountpoint"].toString();
//            QString label = obj["label"].toString();
//            QString uuid = obj["uuid"].toString();
//            QString fstype = obj["fstype"].toString();
//            QString name = obj["name"].toString();

//            if (uuid=="")
//                uuid = name;
//            if (QStringList({"swap"}).contains(fstype))
//                continue;
//            int maj=-1,min=-1;
//            QStringList list;
//            list = obj["maj:min"].toString().split(":");
//            maj = list[0].toInt();
//            min = list[1].toInt();

//            uuid_set << uuid;
//            mnt_info << Mnt_Info_Struct({
//                                            path,
//                                            label,
//                                            uuid,
//                                            fstype,
//                                            name,
//                                            maj,min});
//        }

//    }
//    else
//    {

//    }
//    return true;

//}
