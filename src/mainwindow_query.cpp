#include "MainWindow.h"
#include "ui_Ui_mainwindow.h"

bool MainWindow::eventFilter(QObject *obj, QEvent *event)
{

    if (obj == ui->comboBox_search || obj == ui->comboBox_search->lineEdit())
    {
        if (event->type() == QEvent::FocusOut)
            emit ui->comboBox_search->lineEdit()->returnPressed();
    }

    //    if (obj == this && event->type() == QEvent::Resize)
    //    {
    //        QResizeEvent *resizeEvent = static_cast<QResizeEvent*>(event);
    //        qDebug("Mainwindow - Width: %d Height: %d",
    //                     width(),
    //                     height());
    //        qDebug("Dock - Width: %d Height: %d",
    //                     ui->dockWidget_result->width(),
    //                     ui->dockWidget_result->height());
    //        qDebug()<<ui->dockWidget_result->isVisible() << !ui->dockWidget_result->isFloating();
    //        if (ui->dockWidget_result->isVisible() && !ui->dockWidget_result->isFloating())
    //        {
    //            int dw = width() - last_width;
    //            int dh = height() - last_height;

    //            dw = std::max(dw,0);
    //            dh = std::max(dh,0);
    //             qDebug()<< dw<<dh;
    //            ui->dockWidget_result->resize(ui->dockWidget_result->width()+dw*6,
    //                                          ui->dockWidget_result->height()+dh*6);
    //        }

    //        last_width = width();
    //        last_height = height();
    //    }
    //    if (obj == ui->dockWidget_result && event->type() == QEvent::Resize)
    //    {
    //        if(ui->dockWidget_result->isVisible() && !ui->dockWidget_result->isFloating())
    //            return true;
    //    }
    return QMainWindow::eventFilter(obj, event);

}

void MainWindow::_on_lineedit_text_changed(QString text){
    qDebug()<<"_on_lineedit_text_changed"<< text;

    ui->toolButton_query_ok->setIcon(query_ok_icon);


    if (INSTANT_SEARCH)
        _on_query_text_changed();
};
void MainWindow::_on_lineedit_enter_pressed(){
    _on_query_text_changed();
}
void MainWindow::_on_query_text_changed()
{
    QMutexLocker locker(&mutex_table_result);

    QString sql_text =  lineEdit_search->text().trimmed();
    if ( _Former_search_text == sql_text)
        return;

    Query_Text_ID++;
    _Former_search_text = sql_text;

    if (sql_text=="")
    {
        ui->toolButton_query_ok->setIcon(query_empty_icon);
        return;

    }

    Format_Sql_Result format_sql_result =
            format_sql_cmd("pathname", "uuid", sql_text, 0,0);

    HIGHLIGHT_WORDS_NAME = format_sql_result.highlight_words_Name;
    HIGHLIGHT_WORDS_PATH = format_sql_result.highlight_words_Path;

    ui->plainTextEdit_sql_where->setPlainText(format_sql_result.sql_cmd);
    if (format_sql_result.ok)
        ui->toolButton_query_ok->setIcon(query_ok_icon);
    else
    {
        ui->toolButton_query_ok->setIcon(query_error_icon);
        return;
    }
    lazy_query_timer->start();  //  --> update_query_result()

}

QList<QStringList> MainWindow::get_search_included_uuid()
{
    // TODO: update a global var, when loaded uuid table or table clicked
    QList<QStringList> rst;

    for(int row=0; row < ui->tableWidget_uuid->rowCount();row++){
        if (! (
                    ui->tableWidget_uuid->item(row,
                                               UUID_HEADER.included)->data(Qt::CheckStateRole)
                    ==  Qt::Checked))
            continue;
        QStringList tmp;
        QString uuid = ui->tableWidget_uuid->item(row,UUID_HEADER.uuid)
                ->data(Qt::DisplayRole).toString();
        QString path = ui->tableWidget_uuid->item(row,UUID_HEADER.path)
                ->data(Qt::DisplayRole).toString();
        QString alias = ui->tableWidget_uuid->item(row,UUID_HEADER.alias)
                ->data(Qt::DisplayRole).toString();
        QString rows = ui->tableWidget_uuid->item(row,UUID_HEADER.rows)
                ->data(Qt::DisplayRole).toString();
        tmp << uuid<<path<<rows<< alias;
        rst << tmp;
    }
    return rst;
}

void MainWindow::update_query_result(){

    //Returns a string that has whitespace removed from the start and the end, and that has each sequence of internal
    // whitespace replaced with a single space.
    // QString QString::trimmed() const

    // TODO: necessary?
    QMutexLocker locker(&mutex_table_result);

    QString sql_text =  lineEdit_search->text().trimmed();
    int query_id = Query_Text_ID;

    QList<QStringList> uuid_path_list = get_search_included_uuid(); //uuid<<path<<rows<< alias

    // model.clear()    # will clear header too.
    model->setRowCount(0);


    //model->setRowCount(10);
    CURRENT_MODEL_ITEMS = 0;


    emit send_query_to_worker_SIGNAL(query_id, uuid_path_list, sql_text);

    if (uuid_path_list.length()==0 || sql_text.length() ==0)
    {
        progressBar.setVisible(false);
        return;
    }
    progressBar.setVisible(true);
    progressBar.setValue(0);



}

// ============================================================ receive results

void MainWindow::_on_model_receive_new_row(int query_id, QList<QList<QVariant> > list_of_row_to_insert)
{
    if (query_id!= Query_Text_ID)
        return;
    //    qDebug()<<"receive new row";
    QStandardItem * newitem;
    QStandardItem *  extension_item;

    ui->tableView->setSortingEnabled(false);

    unsigned int row = model->rowCount();
    CURRENT_MODEL_ITEMS = row;

    if (row < MODEL_MAX_ITEMS)
    {
        for(const QList<QVariant> & list: list_of_row_to_insert)
        {
            QList<QStandardItem *> row_to_insert;
            for(int idx=0; idx< QUERY_HEADER.len;idx++)
            {
                newitem = new QStandardItem();
                QVariant current_value = list[idx];
                if (current_value.isNull() || (!current_value.isValid()))
                    current_value = QVariant(1);
                //                            newitem->setData(cur.value(idx), Qt::DisplayRole);
                //                            newitem->setData(cur.value(idx), HACKED_QT_EDITROLE);
                switch (idx) {
                case QUERY_HEADER_class::Filename_:
                {
                    QString pathname = current_value.toString();
                    //                    pathname = "<b>" + pathname + "</b>";
                    newitem->setData(pathname, Qt::DisplayRole);
                    newitem->setData(pathname, HACKED_QT_EDITROLE);
                    row_to_insert << newitem;}
                    break;
                case QUERY_HEADER_class::Path_:
                    //                                newitem->setData(cur.value(idx), HACKED_QT_EDITROLE);
                {QString pathname = current_value.toString();
                    if(pathname.mid(0,2)=="//")  // modify path  like    //usr/bin
                        pathname = pathname.mid(1);
                    newitem->setData(pathname, Qt::DisplayRole);
                    newitem->setData(pathname, HACKED_QT_EDITROLE);
                    row_to_insert << newitem;}
                    break;
                case QUERY_HEADER_class::Size_:
                case QUERY_HEADER_class::atime_:
                case QUERY_HEADER_class::ctime_:
                case QUERY_HEADER_class::mtime_:
                    //                                newitem->setData(cur.value(idx), HACKED_QT_EDITROLE);
                    newitem->setData(current_value, Qt::DisplayRole);
                    newitem->setData(current_value, HACKED_QT_EDITROLE);
                    row_to_insert << newitem;
                    break;
                case QUERY_HEADER_class::IsFolder_:
                    newitem->setTextAlignment(Qt::AlignHCenter|Qt::AlignVCenter);
                    //                    newitem->setData(current_value.toBool(), Qt::DisplayRole);
                    if (current_value.toBool())
                        newitem->setData(QString("     ✓"), Qt::DisplayRole);
                    else
                        newitem->setData(QString(""), Qt::DisplayRole);

                    newitem->setData(current_value.toBool(), HACKED_QT_EDITROLE);
                    //                                newitem->setData(cur.value(idx), HACKED_QT_EDITROLE);
                    row_to_insert << newitem;
                    extension_item =new QStandardItem();
                    if (current_value.toBool())
                    {
                    }
                    else{
                        QString extension = list[QUERY_HEADER_class::Filename_].toString();
                        if (extension.contains("."))
                            extension = extension.split(".").last();
                        else
                            extension = "";
                        extension_item->setData(extension, HACKED_QT_EDITROLE);
                        extension_item->setData(extension, Qt::DisplayRole);
                    }
                    row_to_insert << extension_item;
                    break;
                default:
                    Q_ASSERT(false);
                    break;
                }
                //                QVariant test =  newitem->data(Qt::DisplayRole);
                //                Q_ASSERT((row_to_insert.last() != nullptr));

            }

            model->insertRow(model->rowCount(), row_to_insert);
        }
    }

    if (!lazy_sort_timer->isActive())
        lazy_sort_timer->start();
}

void MainWindow::_on_update_progress_bar(int query_text_id, int remained){

    if (query_text_id == Query_Text_ID)
    {
        progressBar.setRange(0, QUERY_SQL_QUEUE_TOTAL_LENGTH);
        progressBar.setValue(QUERY_SQL_QUEUE_TOTAL_LENGTH-remained);
        if (remained==0)
            progressBar.setVisible(false);
    }
};

void MainWindow::lazy_tableview_sort_slot(){
    ui->tableView->setSortingEnabled(True);
    //    QApplication::processEvents();

}
//========================================================= backup

void MainWindow::_on_model_receive_new_row_old_2(int , QList<QList<QStandardItem *> > )
{
    // _on_model_receive_new_row_old_2(int query_id, QList<QList<QStandardItem *> > list_of_row_to_insert)
    //
//    QMutexLocker locker(&mutex_table_result);
//    if (query_id!= Query_Text_ID)
//    {
//        // free memory
//        for(const QList<QStandardItem *>& list: list_of_row_to_insert)
//        {
//            for(QStandardItem * item: list)
//                delete item;
//        }
//    }

//    ui->tableView->setSortingEnabled(false);

//    unsigned int row = model->rowCount();
//    CURRENT_MODEL_ITEMS = row;

//    //qDebug()<<Query_Text_ID;
////    int Query_Text_ID_tmp1 = Query_Text_ID;

//    if (row < MODEL_MAX_ITEMS)
//    {
//        int new_row_count = row+list_of_row_to_insert.length();
//        //        // FIXME
//        //        model->setRowCount(new_row_count);
//        for( QList<QStandardItem *> list: list_of_row_to_insert)
//        {
//            //model->setRowCount(row+1);
////            int current_row = row;
//            for(int col=0; col < list.length(); col++)
//            {
//                Q_ASSERT(list[col]!=nullptr);

////                int Query_Text_ID_tmp2 = Query_Text_ID;
//                Q_ASSERT(list[col]!=nullptr);
//                //Q_ASSERT( (!(list[col]->data(Qt::DisplayRole).isNull())));

//                // FIXME
//                QVariant aaa = list[col]->data(Qt::DisplayRole);
//                model->setItem(0, col, list[col]);
//                //                model->setItem(current_row, col, list[col]);
//                //                if (list[col]!=nullptr && (list[col]->data(HACKED_QT_EDITROLE).isValid()))
//                //                    model->setItem(current_row, col, list[col]);
//                //                else
//                //                    qDebug()<<" ERROR: "<<__FILE__<< __LINE__<< __FUNCTION__<<
//                //                                              "\n\t null pointer: col"<<col;
//                //                if (col==0)
//                //                {
//                //                    current_row = list[0]->row();
//                //                    qDebug()<<"\current_row: "<<current_row;
//                //                }

//            }
//            row++;
//            qDebug()<<"row: "<<new_row_count<<row;

//            // TODO: check memory leak
//        }
//    }
//    else{
//        // free memory
//        for( QList<QStandardItem *> list: list_of_row_to_insert)
//        {
//            for(QStandardItem * item: list)
//            {
//                Q_ASSERT(item!=nullptr);
//                if(item==nullptr)
//                    qDebug()<<" ERROR: "<<__FILE__<< __LINE__<< __FUNCTION__<<
//                              "\n\t null pointer:";
//                else
//                    delete item;
//            }
//        }
//    }

//    //FIXME
//    //    if (!lazy_sort_timer->isActive())
//    //        lazy_sort_timer->start();

}



void MainWindow::_on_model_receive_new_row_old(int , QList<QList<QStandardItem *> > )
{
    // _on_model_receive_new_row_old(int query_id, QList<QList<QStandardItem *> > list_of_row_to_insert)
    //
    // bug? crash sometime when access list[col]->data(Qt::DisplayRole)
//    if (query_id!= Query_Text_ID)
//    {
//        // free memory
//        for(const QList<QStandardItem *>& list: list_of_row_to_insert)
//        {
//            for(QStandardItem * item: list)
//                delete item;
//        }
//    }

//    ui->tableView->setSortingEnabled(false);

//    int row = model->rowCount();
//    CURRENT_MODEL_ITEMS = row;

//    if (row < MODEL_MAX_ITEMS)
//    {
//        for( QList<QStandardItem *> list: list_of_row_to_insert)
//        {

//            for(QStandardItem * test: list)
//            {
//                Q_ASSERT(test!=nullptr);
//                if(test==nullptr)
//                    qDebug()<<" ERROR: "<<__FILE__<< __LINE__<< __FUNCTION__<<
//                              "\n\t null pointer:";
//            }
//            //             continue;
//            try
//            {
//                if (list[0]!=nullptr && list[1]!=nullptr)
//                {
//                    //      qDebug()<<"receive row: "<<list[0]->data(HACKED_QT_EDITROLE).toString()<<list[1]->data(HACKED_QT_EDITROLE).toString();
//                    //                model->insertRow(row, list);

//                }
//                else
//                {
//                    qDebug()<<"model->insertRow ERROR: "<<__FILE__<< __LINE__<< __FUNCTION__<<
//                              "\n\t null pointer";
//                }
//            }
//            catch (const std::exception &exc)
//            {
//                qDebug()<<"model->insertRow ERROR: "<<__FILE__<< __LINE__<< __FUNCTION__<<
//                          "\n\t Exception:"<<exc.what();
//            }
//            catch (...)
//            {
//                qDebug()<<"model->insertRow ERROR: "<<__FILE__<< __LINE__<< __FUNCTION__<<
//                          "\n\t unknown Exception:";
//            }
//            // TODO: check memory leak
//        }
//    }
//    else{
//        // free memory
//        for( QList<QStandardItem *> list: list_of_row_to_insert)
//        {
//            for(QStandardItem * item: list)
//            {
//                //                Q_ASSERT(item!=nullptr);
//                if(item==nullptr)
//                    qDebug()<<" ERROR: "<<__FILE__<< __LINE__<< __FUNCTION__<<
//                              "\n\t null pointer:";
//                else
//                    delete item;
//            }
//        }
//    }

//    if (!lazy_sort_timer->isActive())
//        lazy_sort_timer->start();

}

