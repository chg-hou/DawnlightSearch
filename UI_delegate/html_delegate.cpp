#include "html_delegate.h"
#include <algorithm>

QIcon build_qicon(QString filename, bool IsFolder) // int size = 32
{
    QString iconname;
    if (IsFolder)
        iconname = "folder";
    else{
        // TODO: set setting item:  QMimeDatabase::MatchDefault,  MatchContent
        QMimeType type = QMimeDatabase().mimeTypeForFile(filename, QMimeDatabase::MatchExtension);
        iconname = type.iconName();
    }
    QIcon icon = QIcon::fromTheme(iconname);
    return icon;
}
QString size_to_str(QString value_in, QString unit = SIZE_UNIT)
{
    if (value_in =="" )
        return "";
    const static QStringList suffixes = {"B", "KB", "MB", "GB", "TB", "PB"};
    if (!suffixes.contains(unit))
        unit = "";

    bool ok;
    qint64 value = value_in.toLongLong(&ok);

    if (unit =="B")
        return value_in + " B";

    if (ok && value ==0)
    {
        return "0 B";
    }
    double value_double = value;
    int i = 0;

    while( (value_double >= 1024) &&
           (i < suffixes.length()-1)   )
    {
        value_double/= 1024.0;
        i++;
        if (unit == suffixes[i])
            break;
    };
    QString f = QString::asprintf("%.2f", value_double);
    while(f.endsWith("0")) f.chop(1);
    while(f.endsWith(".")) f.chop(1);

    return   f + " " + suffixes[i];


}

HTMLDelegate::HTMLDelegate(QStandardItemModel *model_in)
{
    model = model_in;
}
inline QString html_escape_and_bold(    QString html)
{
    // FIXME
    //    html = html.replace("<", "&lt;").replace(">", "&gt;").replace("&", "&amp;");
    return "<b>" + html + "</b>";
}

bool QPairLessThan(const QPair<int,int> &v1, const QPair<int,int> &v2)
{
    if (v1.first<v2.first)
        return true;
    else if (v1.first>v2.first)
        return false;
    else{
        return v1.second<v2.second;
    }
}
bool QPairMoreThan(const QPair<int,int> &v2, const QPair<int,int> &v1)
{
    if (v1.first<v2.first)
        return true;
    else if (v1.first>v2.first)
        return false;
    else{
        return v1.second<v2.second;
    }
}

QString HTMLDelegate::highlight_html(QString html, QSet<QPair<bool, QString> > &word_list) const
{
    QString html_UPPER = html.toUpper();
    QList<QPair<int,int>> seg_list;
    for(const QPair<bool, QString>& case_word: word_list)
    {
        bool case_ = case_word.first;
        QString word = case_word.second;
        int len_word = word.length();
        if (case_)
        {
            int idx = html.indexOf(word,0);
            while(idx>=0)
            {
                seg_list.append(QPair<int,int>( {idx,  len_word}  ));
                idx = html.indexOf(word,idx+1);
            }
        }else
        {
            QString word_UPPER = word.toUpper();
            int idx = html_UPPER.indexOf(word_UPPER,0);
            while(idx>=0)
            {
                seg_list.append(QPair<int,int>( {idx,  len_word}  ));
                idx = html_UPPER.indexOf(word_UPPER,idx+1);
            }
        }
    }

    std::sort(seg_list.begin(), seg_list.end(), QPairMoreThan);
    int last_begin = html.length();
    for (const QPair<int,int> & seg: seg_list)
    {
        if(seg.first+seg.second>last_begin)
            continue;
        html = html.mid(0, seg.first) + html_escape_and_bold(
                    html.mid(seg.first,  seg.second)
                    )
                + html.mid(seg.first+seg.second);
    }
    return html;

}

void HTMLDelegate::update_item_icon(int col, int row) const
{
    //    int col = index.column();
    if (col >0)
        return;

    //    int row = index.row();

    QString filename = model->item(row, DB_HEADER.Filename)->data(HACKED_QT_EDITROLE).toString();
    // TODO: improve this
    //    if (model->item(row, DB_HEADER.Filename)->data( Qt::ToolTip).toString()==filename && filename !="")
    //        return;

    int  new_highlight_words = Query_Text_ID;
    int old_highlight_words = model->item(row, DB_HEADER.Filename)->data(Qt::AccessibleDescriptionRole).toInt();
    QString new_display_role;
    if (new_highlight_words != old_highlight_words)
    {
        model->item(row, DB_HEADER.Filename)->setData(new_highlight_words,Qt::AccessibleDescriptionRole);
        new_display_role =highlight_html(filename, HIGHLIGHT_WORDS_NAME);
        model->item(row, DB_HEADER.Filename)->setData(new_display_role,Qt::DisplayRole);

        QString path = model->item(row, DB_HEADER.Path)->data(HACKED_QT_EDITROLE).toString();
        new_display_role =highlight_html(path, HIGHLIGHT_WORDS_PATH);
        model->item(row, DB_HEADER.Path)->setData(new_display_role,Qt::DisplayRole);


    }


    //    QMap<int, QVariant> itemData = model->itemData(row, DB_HEADER.Filename);
    //    if ( itemData.contains(Qt::DecorationRole) || filename =="")

    // TODO: ? typo, should use Qt::DecorationRole (in python) or Qt::AccessibleDescriptionRole
    // CORRECT
    if ( model->item(row, DB_HEADER.Filename)->data( Qt::ToolTip).toString()==filename || filename =="")
    {

    }
    else{
        model->item(row, DB_HEADER.Filename)->setData(filename,  Qt::ToolTip);
        model->item(row, DB_HEADER.Filename)->setData(filename,  Qt::AccessibleDescriptionRole);

        bool IsFolder = model->item(row, DB_HEADER.IsFolder)->data(HACKED_QT_EDITROLE).toBool();
        QIcon newicon = build_qicon(filename, IsFolder);

        model->item(row, DB_HEADER.Filename)->setData(newicon, Qt::DecorationRole);

        QString size_data;
        if (IsFolder)
        {}
        else
        {
            size_data = model->item(row, DB_HEADER.Size)->data(HACKED_QT_EDITROLE).toString();
            size_data = size_to_str(size_data);
        }

// html align right does not work
//        size_data = "<div align=\"right\">" + size_data + "</div>";
        model->item(row, DB_HEADER.Size)->setData(size_data, Qt::DisplayRole);

        // Alignment is controled by html_delegate, no effect here
//        model->item(row, DB_HEADER.Size)->setTextAlignment(Qt::AlignRight|Qt::AlignVCenter);
//        model->item(row, DB_HEADER.IsFolder)->setTextAlignment(Qt::AlignHCenter|Qt::AlignVCenter);

        for(int col: QList<int>({ DB_HEADER.ctime, DB_HEADER.atime, DB_HEADER.mtime  }))
        {
            QDateTime date;
            date.setTime_t( model->item(row, col)->data(HACKED_QT_EDITROLE).toInt() );
            model->item(row, col)->setData( date.toString(), Qt::DisplayRole);
        }
    }


}



void HTMLDelegate::paint(QPainter* painter, const QStyleOptionViewItem & option, const QModelIndex &index) const
{

    int col = index.column();
    int row = index.row();
    update_item_icon(col, row);


    QStyleOptionViewItem options = option;
    initStyleOption(&options, index);

    painter->save();

    QTextDocument doc;
    doc.setHtml(options.text);

    options.text = "";
    options.widget->style()->drawControl(QStyle::CE_ItemViewItem, &options, painter);

    QRect clip;

    if (col == DB_HEADER.Filename)
    {
        // left align with icon
        // shift text right to make icon visible
        QSize iconSize = options.icon.actualSize(options.rect.size());
        //painter->translate(options.rect.left()+iconSize.width(), options.rect.top());

        //    if (row ==0 && (col ==0 || col ==1))
        //    qDebug()<<"Col "<<col<<" "<<options.rect.size()<<iconSize<<options.rect
        //           <<options.icon;

        painter->translate(options.rect.left()+std::min(iconSize.height(),iconSize.width())*ICON_TEXT_SHIFT_COEFF, options.rect.top());
        //    QRect clip(0, 0, options.rect.width()+iconSize.width(), options.rect.height());
        clip = QRect(0, 0, options.rect.width()-std::min(iconSize.height(),iconSize.width())*ICON_TEXT_SHIFT_COEFF, options.rect.height());

        //doc.drawContents(painter, clip);

        painter->setClipRect(clip);
    }
    else if (col == DB_HEADER.IsFolder)
    {
        // middle
        painter->translate(options.rect.left() + options.rect.width()/2-doc.size().width()/2, options.rect.top());
        //    QRect clip(0, 0, options.rect.width()+iconSize.width(), options.rect.height());
        clip = QRect(0, 0, options.rect.width()/2, options.rect.height());

        //doc.drawContents(painter, clip);

        painter->setClipRect(clip);
    }
    else if (col == DB_HEADER.Size || col == DB_HEADER.atime || col == DB_HEADER.ctime || col == DB_HEADER.mtime || col == DB_HEADER.Extension)
    {
        // right align
        int left_shift = options.rect.width() - doc.size().width();
        if (left_shift>0)
        {painter->translate(options.rect.left() + left_shift, options.rect.top());
        clip = QRect(0, 0, options.rect.width()-left_shift, options.rect.height());}
        else
        {left_shift=0;
            painter->translate(options.rect.left() + left_shift, options.rect.top());
                    clip = QRect(0, 0, options.rect.width()-left_shift, options.rect.height());
        }
        painter->setClipRect(clip);
    }
    else
    {
        // left align
        painter->translate(options.rect.left(), options.rect.top());
        clip = QRect(0, 0, options.rect.width(), options.rect.height());
        painter->setClipRect(clip);
    }

    QAbstractTextDocumentLayout::PaintContext ctx;
    // set text color to red for selected item
    //    if (option.state & QStyle::State_Selected)
    //        ctx.palette.setColor(QPalette::Text, QColor("red"));
    if (option.state & QStyle::State_Selected)
        ctx.palette.setColor(QPalette::Text,
                             option.palette.color(QPalette::Active, QPalette::HighlightedText));
    else
        ctx.palette.setColor(QPalette::Text,
                             option.palette.color(QPalette::Active, QPalette::Text));

    ctx.clip = clip;
    doc.documentLayout()->draw(painter, ctx);

    painter->restore();
}

//void HTMLDelegate::paint(QPainter* painter, const QStyleOptionViewItem & option, const QModelIndex &index) const
//{
//    QStyleOptionViewItemV4 options = option;
//    initStyleOption(&options, index);

//    painter->save();

//    QTextDocument doc;
//    doc.setHtml(options.text);

//    options.text = "";
//    options.widget->style()->drawControl(QStyle::CE_ItemViewItem, &options, painter);

//    painter->translate(options.rect.left(), options.rect.top());
//    QRect clip(0, 0, options.rect.width(), options.rect.height());
//    doc.drawContents(painter, clip);

//    painter->restore();
//}

QSize HTMLDelegate::sizeHint ( const QStyleOptionViewItem & option, const QModelIndex & index ) const
{
    //QStyleOptionViewItemV4 options = option;
    QStyleOptionViewItem options = option;
    initStyleOption(&options, index);

    QTextDocument doc;
    doc.setHtml(options.text);
    doc.setTextWidth(options.rect.width());
    return QSize(doc.idealWidth(), doc.size().height());
}


