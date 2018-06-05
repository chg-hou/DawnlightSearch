#ifndef HTML_DELEGATE_H
#define HTML_DELEGATE_H

#include <QObject>
#include <QStyledItemDelegate>
#include <QPainter>
#include <QTextDocument>
#include <QAbstractTextDocumentLayout>
#include <QStandardItemModel>
#include <QList>
#include <QString>
#include <QIcon>
#include <QDateTime>
#include <QMimeType>
#include <QMimeDatabase>
#include <QSet>

#include "globals.h"

//class HTMLDelegate : public QObject
//{
//    Q_OBJECT
//public:
//    explicit HTMLDelegate(QObject *parent = nullptr);

//signals:

//public slots:
//};

//http://www.qtcentre.org/threads/22863-HTML-and-QStandardItem
//https://stackoverflow.com/questions/1956542/how-to-make-item-view-render-rich-html-text-in-qt
class HTMLDelegate : public QStyledItemDelegate
{
public:
    HTMLDelegate(QStandardItemModel * model_in);
    //HTMLDelegate();
    void update_item_icon(int col, int row) const;

protected:

    void paint ( QPainter * painter, const QStyleOptionViewItem & option,
                 const QModelIndex & index ) const;
    QSize sizeHint ( const QStyleOptionViewItem & option,
                     const QModelIndex & index ) const;

private:

    QStandardItemModel * model;
    QString highlight_html(QString html, QSet<QPair<bool,QString >> & word_list) const;
};
#endif // HTML_DELEGATE_H
