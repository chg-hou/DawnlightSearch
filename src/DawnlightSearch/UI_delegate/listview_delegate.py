#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .._Global_Qt_import import *
from .._Global_DawnlightSearch import *
from .listitem_formatter import *

def highlight_html(html,word_list):
    def html_highlight(html):
        html = html.replace("<", "&lt;").replace(">", "&gt;").replace("&", "&amp;")
        return '<b>' + html + '</b>'

    html_UPPER =html.upper()
    seg_list = []
    for case,word in word_list:
        len_word = len(word)
        if case:    #case sensitive
            idx = html.find(word, 0)
            while idx>=0:
                seg_list.append([idx, len_word])
                idx = html.find(word, idx+1)
        else:
            word_UPPER = word.upper()
            idx = html_UPPER.find(word_UPPER, 0)
            while idx >= 0:
                seg_list.append([idx, len_word])
                idx = html_UPPER.find(word_UPPER, idx + 1)
    i = 0
    seg_list.sort(reverse=True)
    last_begin = len(html)
    for i,seg in enumerate(seg_list):
        if seg[0]+seg[1]>last_begin:
            continue
        html = html[:seg[0]] + html_highlight(html[seg[0]:seg[0]+seg[1]]) +html[seg[0]+seg[1]:]
        last_begin = seg[0]

    return html


            # CUSTOM DELEGATE TO GET HTML RICH TEXT IN LISTVIEW
# ALLOWS USE OF <b></b> TAGS TO HIGHLIGHT SEARCHED PHRASE IN RESULTS
class HTMLDelegate_VC_HL(QtWidgets.QStyledItemDelegate):
    # http://www.qtcentre.org/threads/65246-Use-of-QStyledItemDelegate-prevents-certain-Stylesheets-from-working-gif
    def __init__(self, parent=None):
        super(self.__class__, self).__init__()
        self.doc = QtGui.QTextDocument(self)

    def update_item_icon(self, index):
        if index.column() > 0:
            return
        m = index.model()
        ui = m.parent().parent().parent().parent()  # TODO: Ugly, unsafe
        row = index.row()  # TODO: check proxy, hidden row

        filename = m.data(m.index(row, 0), HACKED_QT_EDITROLE)
        # logger.warning(m.data(m.index(row, 0), HACKED_QT_EDITROLE))
        # logger.warning(m.data(m.index(row, 0), QtCore.Qt.DisplayRole))

        new_highlight_words = GlobalVar.Query_Text_ID
        old_highlight_words = m.data(m.index(row, 0), QtCore.Qt.AccessibleDescriptionRole)
        if (new_highlight_words != old_highlight_words):
            m.setData(m.index(row, 0), new_highlight_words, QtCore.Qt.AccessibleDescriptionRole)
            new_display_role = highlight_html(filename, GlobalVar.HIGHLIGHT_WORDS['Name'])
            m.setData(m.index(row, 0), new_display_role, QtCore.Qt.DisplayRole)

            path = m.data(m.index(row, 1), HACKED_QT_EDITROLE)
            new_display_role = highlight_html(path, GlobalVar.HIGHLIGHT_WORDS['Path'])
            m.setData(m.index(row, 1), new_display_role, QtCore.Qt.DisplayRole)

        itemdata = m.itemData(m.index(row, 0))
        if (QtCore.Qt.DecorationRole in itemdata or not (filename)):
            pass
        else:
            m.setData(m.index(row, 0), filename, QtCore.Qt.ToolTipRole)
            m.setData(m.index(row, 0), filename, QtCore.Qt.AccessibleDescriptionRole)

            isPath = m.data(m.index(row, 3)) == '1'
            newicon = build_qicon(filename, isPath, size=32)

            m.setData(m.index(row, 0), newicon, QtCore.Qt.DecorationRole)


            size_data = m.data(m.index(row, 2), HACKED_QT_EDITROLE)
            size_data = size_to_str(size_data)

            m.setData(m.index(row, 2), size_data, QtCore.Qt.DisplayRole)
            m.setData(m.index(row, 2), QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter, QtCore.Qt.TextAlignmentRole)

            for col in [4, 5, 6]:
                date = QtCore.QDateTime()
                date.setTime_t(int(m.data(m.index(row, col), HACKED_QT_EDITROLE)))
                m.setData(m.index(row, col), date.toString(), QtCore.Qt.DisplayRole)
                # logger.debug(str(m.itemData(m.index(row, 0))))

    def paint(self, painter, option, index):

        if index.column()>1:
            return super(self.__class__, self).paint(painter, option, index)

        self.update_item_icon(index)
        options = QtWidgets.QStyleOptionViewItem(option)

        self.initStyleOption(options, index)
        self.doc.setHtml(options.text)
        options.text = ''

        style = QtWidgets.QApplication.style() if options.widget is None  else options.widget.style()

        style.drawControl(QtWidgets.QStyle.CE_ItemViewItem, options, painter)  # QtWidgets.QStyle.CT_ItemViewItem

        ctx = QtGui.QAbstractTextDocumentLayout.PaintContext()

        if option.state & QtWidgets.QStyle.State_Selected:
            ctx.palette.setColor(QtGui.QPalette.Text, option.palette.color(
                QtGui.QPalette.Active, QtGui.QPalette.HighlightedText))
        else:
            ctx.palette.setColor(QtGui.QPalette.Text, option.palette.color(
                QtGui.QPalette.Active, QtGui.QPalette.Text))

        textRect = style.subElementRect(
            QtWidgets.QStyle.SE_ItemViewItemText, options)

        thefuckyourshitup_constant = 4
        margin = (option.rect.height() - options.fontMetrics.height()) // 2  #
        margin = margin - thefuckyourshitup_constant
        textRect.setTop(textRect.top() + margin)

        painter.save()
        painter.translate(textRect.topLeft())
        painter.setClipRect(textRect.translated(-textRect.topLeft()))
        self.doc.documentLayout().draw(painter, ctx)

        painter.restore()


# CUSTOM DELEGATE TO GET HTML RICH TEXT IN LISTVIEW
# ALLOWS USE OF <b></b> TAGS TO HIGHLIGHT SEARCHED PHRASE IN RESULTS
class HTMLDelegate_VC_HL_bak(QtWidgets.QStyledItemDelegate):
    # http://www.qtcentre.org/threads/65246-Use-of-QStyledItemDelegate-prevents-certain-Stylesheets-from-working-gif
    def __init__(self, parent=None):
        super(self.__class__, self).__init__()
        self.doc = QtGui.QTextDocument(self)

    def update_item_icon(self, index):
        if index.column() > 0:
            return
        m = index.model()
        ui = m.parent().parent().parent().parent()      # TODO: Ugly, unsafe
        row = index.row()  # TODO: check proxy, hidden row

        filename = m.data(m.index(row, 0), HACKED_QT_EDITROLE)
        # logger.warning(m.data(m.index(row, 0), HACKED_QT_EDITROLE))
        # logger.warning(m.data(m.index(row, 0), QtCore.Qt.DisplayRole))

        new_highlight_words = ui.lineEdit_search.text().strip()
        old_highlight_words = m.data(m.index(row, 0), QtCore.Qt.AccessibleDescriptionRole)
        if (new_highlight_words != old_highlight_words):
            m.setData(m.index(row, 0), new_highlight_words, QtCore.Qt.AccessibleDescriptionRole)
            new_display_role = filename
            # new_display_role = filename.replace("<", "&lt;").replace(">", "&gt;").replace("&", "&amp;")
            # TODO: verify html escape
            for new_word in new_highlight_words.split():
                if not new_word:
                    continue
                new_display_role = new_display_role.replace(new_word, "<b>" + new_word + "</b>")
                # TODO: case sensitive    "Abc"  "abc"
            m.setData(m.index(row, 0), new_display_role, QtCore.Qt.DisplayRole)

        itemdata = m.itemData(m.index(row, 0))
        if (QtCore.Qt.DecorationRole in itemdata or not (filename)):
            pass
        else:
            m.setData(m.index(row, 0), filename, QtCore.Qt.ToolTipRole)
            m.setData(m.index(row, 0), filename, QtCore.Qt.AccessibleDescriptionRole)

            isPath = m.data(m.index(row, 3)) == '1'
            # print 'Item filename:', filename
            newicon = build_qicon(filename, isPath, size=32)
            # itemdata = m.itemData(m.index(row, 0))
            # itemdata[QtCore.Qt.DecorationRole] = newicon
            # import random
            # order = random.randint(0, 100)
            # # print order
            # itemdata[QtCore.Qt.InitialSortOrderRole] = order
            # itemdata[QtCore.Qt.TextAlignmentRole] = QtCore.Qt.AlignRight
            # m.setItemData(m.index(row, 0), itemdata)
            m.setData(m.index(row, 0), newicon, QtCore.Qt.DecorationRole)
            # print 'Updated icon row:', row

            size_data = m.data(m.index(row, 2), HACKED_QT_EDITROLE)
            size_data = size_to_str(size_data)
            # print 'size_data: ', size_data
            m.setData(m.index(row, 2), size_data, QtCore.Qt.DisplayRole)
            m.setData(m.index(row, 2), QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter, QtCore.Qt.TextAlignmentRole)

            for col in [4, 5, 6]:
                date = QtCore.QDateTime()
                date.setTime_t(int(m.data(m.index(row, col), HACKED_QT_EDITROLE)))
                m.setData(m.index(row, col), date.toString(), QtCore.Qt.DisplayRole)
                # logger.debug(str(m.itemData(m.index(row, 0))))

    def paint(self, painter, option, index):
        self.update_item_icon(index)
        # print "paint ", index
        # http://www.cnblogs.com/hangxin1940/archive/2012/12/07/2806449.html
        # 首先，从索引获取数据，这里获取当前索引角色为DisplayQole的数据
        # item_var = index.data(Qt.DisplayRole)  # [QVariant]
        # 数据是C格式，我们再转为Python格式，记住这点
        # item_str = item_var.toPyObject()  # [QVariant] -&gt; str

        options = QtWidgets.QStyleOptionViewItem(option)

        self.initStyleOption(options, index)
        self.doc.setHtml(options.text)
        options.text = ''

        style = QtWidgets.QApplication.style() if options.widget is None  else options.widget.style()

        style.drawControl(QtWidgets.QStyle.CE_ItemViewItem, options, painter)  # QtWidgets.QStyle.CT_ItemViewItem

        ctx = QtGui.QAbstractTextDocumentLayout.PaintContext()

        if option.state & QtWidgets.QStyle.State_Selected:
            ctx.palette.setColor(QtGui.QPalette.Text, option.palette.color(
                QtGui.QPalette.Active, QtGui.QPalette.HighlightedText))
        else:
            ctx.palette.setColor(QtGui.QPalette.Text, option.palette.color(
                QtGui.QPalette.Active, QtGui.QPalette.Text))

        textRect = style.subElementRect(
            QtWidgets.QStyle.SE_ItemViewItemText, options)

        # if index.column() != 0:
        #     textRect.adjust(5, 0, 0, 0)

        thefuckyourshitup_constant = 4
        margin = (option.rect.height() - options.fontMetrics.height()) // 2  #
        margin = margin - thefuckyourshitup_constant
        textRect.setTop(textRect.top() + margin)

        painter.save()
        painter.translate(textRect.topLeft())
        painter.setClipRect(textRect.translated(-textRect.topLeft()))
        self.doc.documentLayout().draw(painter, ctx)

        painter.restore()

        # def sizeHint(self, option, index):
        #     return QtCore.QSize(self.doc.idealWidth(), self.doc.size().height())


# http://devbean.blog.51cto.com/448512/271255
# void TrackDelegate::paint(QPainter *painter, const QStyleOptionViewItem &option, const QModelIndex &index) const
# {
#         if (index.column() == durationColumn) {
#                 int secs = index.model()->data(index, Qt::DisplayRole).toInt();
#                 QString text = QString("%1:%2").arg(secs / 60, 2, 10, QChar('0')).arg(secs % 60, 2, 10, QChar('0'));
#                 QTextOption o(Qt::AlignRight | Qt::AlignVCenter);
#                 painter->drawText(option.rect, text, o);
#         } else {
#                 QStyledItemDelegate::paint(painter, option, index);
#         }
# }
class HTMLDelegate_VU_HL(QtWidgets.QStyledItemDelegate):
    # http://www.qtcentre.org/threads/62127-PyQt-Custom-delegate-for-html-format-text-causes-jittery-refreshing-GIF-included
    # def __init__(self, parent=None):
    #     super(self.__class__, self).__init__()
    #     self.doc = QtGui.QTextDocument(self)

    def paint(self, painter, option, index):
        self.doc = QtGui.QTextDocument(self)
        options = QtWidgets.QStyleOptionViewItem(option)
        self.initStyleOption(options, index)
        style = QApplication.style()

        self.doc.setHtml(options.text)

        options.text = ""
        style.drawControl(QtWidgets.QStyle.CE_ItemViewItem, options, painter)

        ctx = QtGui.QAbstractTextDocumentLayout.PaintContext()

        if option.state & QtWidgets.QStyle.State_Selected:
            ctx.palette.setColor(QtGui.QPalette.Text, option.palette.color(
                QtGui.QPalette.Active, QtGui.QPalette.HighlightedText))

        textRect = style.subElementRect(QtWidgets.QStyle.SE_ItemViewItemText, options)
        painter.save()
        painter.translate(textRect.topLeft())
        painter.setClipRect(textRect.translated(-textRect.topLeft()))
        self.doc.documentLayout().draw(painter, ctx)

        painter.restore()

        # def sizeHint(self, option, index):
        #     options = QtWidgets.QStyleOptionViewItem(option)
        #     self.initStyleOption(options, index)
        #
        #     self.doc.setDocumentMargin(1)
        #     self.doc.setHtml(options.text)
        #     return QtCore.QSize(self.doc.idealWidth(), 23)


class HTMLDelegate22(QtWidgets.QStyledItemDelegate):
    """QStyledItemDelegate implementation. Draws HTML

    http://stackoverflow.com/questions/1956542/how-to-make-item-view-render-rich-html-text-in-qt/1956781#1956781
    """

    def paint(self, painter, option, index):
        """QStyledItemDelegate.paint implementation
        """
        doc = QtGui.QTextDocument()
        doc.setDocumentMargin(1)
        option.state &= ~QtWidgets.QStyle.State_HasFocus  # never draw focus rect

        options = QtWidgets.QStyleOptionViewItem(option)

        self.initStyleOption(options, index)
        doc.setHtml(options.text)

        print "options: ", options, options.text

        style = QtWidgets.QApplication.style() if options.widget is None else options.widget.style()

        #  bad long (multiline) strings processing doc.setTextWidth(options.rect.width())

        options.text = ""
        style.drawControl(QtWidgets.QStyle.CE_ItemViewItem, options, painter);

        ctx = QtGui.QAbstractTextDocumentLayout.PaintContext()

        # Highlighting text if item is selected
        # if (optionV4.state & QStyle::State_Selected)
        # ctx.palette.setColor(QPalette::Text, optionV4.palette.color(QPalette::Active, QPalette::HighlightedText));

        textRect = style.subElementRect(QtWidgets.QStyle.SE_ItemViewItemText, options)
        painter.save()
        painter.translate(textRect.topLeft())
        painter.setClipRect(textRect.translated(-textRect.topLeft()))
        doc.documentLayout().draw(painter, ctx)

        painter.restore()

    def sizeHint(self, option, index):
        """QStyledItemDelegate.sizeHint implementation
        """
        options = QtWidgets.QStyleOptionViewItem(option)
        self.initStyleOption(options, index)

        doc = QtGui.QTextDocument()
        doc.setDocumentMargin(1)
        #  bad long (multiline) strings processing doc.setTextWidth(options.rect.width())
        doc.setHtml(options.text)
        return QtCore.QSize(doc.idealWidth(), doc.size().height())


class HTMLDelegate2(QtWidgets.QStyledItemDelegate):
    """QStyledItemDelegate implementation. Draws HTML
    http://stackoverflow.com/questions/1956542/how-to-make-item-view-render-rich-html-text-in-qt/1956781#1956781
    """

    def paint(self, painter, option, index):
        """QStyledItemDelegate.paint implementation
        """
        options = QtWidgets.QStyleOptionViewItem(option)
        self.initStyleOption(options, index)
        style = QtWidgets.QApplication.style() if options.widget is None else options.widget.style()

        doc = QtGui.QTextDocument()
        doc.setHtml(options.text)
        # doc.setDocumentMargin(1)

        ctx = QtGui.QAbstractTextDocumentLayout.PaintContext()
        textRect = style.subElementRect(QtWidgets.QStyle.SE_ItemViewItemText, options)

        painter.save()
        painter.translate(textRect.topLeft())
        painter.setClipRect(textRect.translated(-textRect.topLeft()))
        doc.documentLayout().draw(painter, ctx)
        painter.restore()

        #  bad long (multiline) strings processing doc.setTextWidth(options.rect.width())
        # options.text = ""
        # style.drawControl(QtWidgets.QStyle.CE_ItemViewItem, options, painter)

        # Highlighting text if item is selected
        # if (optionV4.state & QStyle::State_Selected)
        # ctx.palette.setColor(QPalette::Text, optionV4.palette.color(QPalette::Active, QPalette::HighlightedText));

    def sizeHint(self, option, index):
        """QStyledItemDelegate.sizeHint implementation
        """
        options = QtWidgets.QStyleOptionViewItem(option)
        self.initStyleOption(options, index)

        doc = QtGui.QTextDocument()
        doc.setDocumentMargin(1)
        #  bad long (multiline) strings processing doc.setTextWidth(options.rect.width())
        doc.setHtml(options.text)
        doc.setTextWidth(options.rect.width())
        return QtCore.QSize(doc.idealWidth(), doc.size().height())


class FileSizeDelegate(QtWidgets.QStyledItemDelegate):
    # http://stackoverflow.com/questions/3472651/cannot-select-item-from-qlistview-with-custom-qstyleditemdelegate
    # def __init__(self, parent=None):
    #   super(self.__class__, self).__init__()

    # def paint(self, painter, option, index):
    #
    #     #print index.column()
    #     #size = index.model().data(index,QtCore.Qt.EditRole)
    #     #text = str(size/1024)
    #     text = '1'
    #
    #     painter.drawText(option.rect, QtCore.Qt.AlignCenter, text)

    # def sizeHint(self, option, index):
    #     model = index.model()
    #     record = model.listdata[index.row()]
    #     doc = QtGui.QTextDocument(self)
    #     doc.setHtml("%s" % record)
    #     doc.setTextWidth(option.rect.width())
    #     return QtCore.QSize(doc.idealWidth(), doc.size().height())
    def displayText(self, value, locale):
        # return value
        return size_to_str(value)

        # http://pyqt.sourceforge.net/Docs/PyQt4/qstyleditemdelegate.html

        # def sizeHint(self, option, index):
        #    return QtCore.QSize(self.doc.idealWidth(), self.doc.size().height())
