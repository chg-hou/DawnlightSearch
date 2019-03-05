#include "my_qstandarditemmodel.h"

MyQStandardItemModel::MyQStandardItemModel() {}

QStringList MyQStandardItemModel::mimeTypes() const
{
    QStringList types;
    //types << "text/plain";
    types  << "text/plain" << "text/uri-list"<< "application/x-kde4-urilist";
    //qDebug()<<"types: "<<types;
    return types;
}

QMimeData* MyQStandardItemModel::mimeData(const QModelIndexList& indexes) const
{
//    QMimeData* mimeData = new QMimeData();
//    QByteArray encodedData;

//    QDataStream stream(&encodedData, QIODevice::WriteOnly);

//    foreach (QModelIndex index, indexes) {
//        if (index.isValid()) {
//            QString text = data(index, Qt::DisplayRole).toString();
//            stream << text;
//        }
//    }

//    mimeData->setData("text/plain", encodedData);
//    return mimeData;


    QMimeData* mimeData = new QMimeData();
//    QByteArray encodedData;
//    QDataStream stream(&encodedData, QIODevice::WriteOnly);
    QSet<int> row_set;
    for ( const QModelIndex & idx: indexes)
    {
        int row = idx.row();
        row_set.insert(row);
    }

    QList<QUrl>  urllist;
//    QList<QString > rst;
    for ( int row: row_set)
    {
        QString filename =  this->item(row, DB_HEADER.Filename)->data(HACKED_QT_EDITROLE).toString();
        QString path   =  this->item(row, DB_HEADER.Path)->data(HACKED_QT_EDITROLE).toString();
        QString fullpath = path + QDir::separator() + filename;

        fullpath.replace("//","/");
        //bool isfolder = this->item(row, DB_HEADER.IsFolder)->data(HACKED_QT_EDITROLE).toBool();

//        rst << fullpath;
        urllist<< QUrl("file://" + fullpath);
    }
//    stream << rst.join('\n');
//    qDebug()<<rst.join('\n');

    //mimeData->setData("text/plain", encodedData);
    mimeData->setUrls(urllist);

    return mimeData;
}

bool MyQStandardItemModel::dropMimeData(const QMimeData *data, Qt::DropAction , int , int , const QModelIndex &)
{
    qDebug()<<"text: "<<data->text();
    qDebug()<<"formats: "<<data->formats();
    qDebug()<<"hasColor: "<<data->hasColor();
    qDebug()<<"hasText: "<<data->hasText();
    qDebug()<<"hasUrls: "<<data->hasUrls();
    qDebug()<<"html: "<<data->html();
    for(QUrl qurl : data->urls())
    {
        qDebug()<<"tostring: "<<qurl.toString();
        qDebug()<<"    urls: "<<qurl.fileName();
        qDebug()<<"    host: "<<qurl.host();
    }
    return true;
}
