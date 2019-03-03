// https://doc.qt.io/archives/4.6/model-view-dnd.html

#ifndef MY_QSTANDARDITEMMODEL_H
#define MY_QSTANDARDITEMMODEL_H

#include "globals.h"

#include <QStandardItemModel>
#include <QStringList>
#include <QMimeData>
#include <QModelIndexList>
#include <QDir>
#include <QSet>
#include <QUrl>

class MyQStandardItemModel : public QStandardItemModel
{
public:
    MyQStandardItemModel() ;

    QStringList mimeTypes() const;
    QMimeData *mimeData(const QModelIndexList &indexes) const;

    bool dropMimeData(const QMimeData *data,
                      Qt::DropAction action, int row, int column, const QModelIndex &parent);
};

#endif // MY_QSTANDARDITEMMODEL_H
