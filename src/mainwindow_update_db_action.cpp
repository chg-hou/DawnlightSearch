#include "MainWindow.h"
#include "ui_Ui_mainwindow.h"



void MainWindow::_on_push_button_updatedb_clicked()
{
    qDebug() << "on_push_button_updatedb_clicked";

    QList<QStringList> update_path_list;
    for(int row = 0; row <ui->tableWidget_uuid->rowCount();row++)
    {
        bool updatable = ( ui->tableWidget_uuid->item(row, UUID_HEADER.updatable)->data(Qt::CheckStateRole) == Qt::Checked);
        if (!updatable)
            continue;
        QString uuid = ui->tableWidget_uuid->item(row, UUID_HEADER.uuid)->data(Qt::DisplayRole).toString();
        QString path = ui->tableWidget_uuid->item(row, UUID_HEADER.path)->data(Qt::DisplayRole).toString();
        // bool included  = ( ui->tableWidget_uuid->item(row, UUID_HEADER.included)->data(Qt::CheckStateRole) == Qt::Checked);
        update_path_list << ( QStringList({path, uuid}) );
    }
    qDebug()<<"Update db SIGNAL: "<<__FILE__<< __LINE__<< __FUNCTION__<<"\n\t"<<update_path_list;
    emit update_db_SIGNAL(update_path_list);
}
void MainWindow::_on_push_button_updatedb_only_selected_clicked(){
    qDebug() << "_on_push_button_updatedb_only_selected_clicked";

    QList<QStringList> update_path_list;
    QSet<int> selected_rows;

    for (const QModelIndex & selected_index: ui->tableWidget_uuid->selectionModel()->selectedIndexes())
        selected_rows << selected_index.row();

    for (const int & row: selected_rows)
    {
        QString uuid = ui->tableWidget_uuid->item(row, UUID_HEADER.uuid)->data(Qt::DisplayRole).toString();
        QString path = ui->tableWidget_uuid->item(row, UUID_HEADER.path)->data(Qt::DisplayRole).toString();
        update_path_list << ( QStringList({path, uuid}) );
    }

    qDebug()<<"Update db only selected SIGNAL: "<<__FILE__<< __LINE__<< __FUNCTION__<<"\n\t"<<update_path_list;
    emit update_db_SIGNAL(update_path_list);
}
void MainWindow::_on_push_button_stopupdatedb_clicked()
{
    QList<QStringList> update_path_list;

    qDebug() << "on_push_button_stopupdatedb_clicked";

    qDebug()<<"Stop updating db SIGNAL: "<<__FILE__<< __LINE__<< __FUNCTION__<<"\n\t"<<update_path_list;
    emit update_db_SIGNAL(update_path_list);
}

void MainWindow::_on_db_progress_update(long num_records,long total_files,QString uuid_updating){
//    if (num_records<0)
//        qDebug()<< __FILE__<< __LINE__<< __FUNCTION__ << "\n\t"<<num_records<<total_files<<uuid_updating;

    for(int row = 0; row<ui->tableWidget_uuid->rowCount(); row++)
    {
        QString uuid = ui->tableWidget_uuid->item(row, UUID_HEADER.uuid)->data(Qt::DisplayRole).toString();

        // restart when value == -4
        QProgressBar * progressbar = (QProgressBar *) ui->tableWidget_uuid->cellWidget(row,UUID_HEADER.processbar);
        if (progressbar != NULL && total_files==-4)
            progressbar->hide();

        if (uuid == uuid_updating)
        {
           // QProgressBar * progressbar = (QProgressBar *) ui->tableWidget_uuid->cellWidget(row,UUID_HEADER.processbar);
            if (progressbar == NULL )
            {
                progressbar = new QProgressBar(   ); //ui->tableWidget_uuid->item(row, UUID_HEADER.uuid)
                progressbar->setMaximum(100);
                ui->tableWidget_uuid->setCellWidget(row, UUID_HEADER.processbar,progressbar);
                progressbar->hide();
            }
            switch (num_records) {
            case -1:
                progressbar->show();
                progressbar->setVisible(true);
                progressbar->setTextVisible(true);
                progressbar->setMaximum(100);
                progressbar->setMinimum(0);
                progressbar->setValue(0);
                progressbar->setFormat("%p%");
                break;
            case -2:
                progressbar->setMaximum(100);
                progressbar->setMinimum(0);
                progressbar->setValue(100);
                progressbar->setFormat("Merging...");
                //QApplication::processEvents();
                break;
            case -3:
                progressbar->setFormat("Done");
                break;
            case -4:
                // restart, hide all
                break;
            default:
                if (total_files<0)
                {
                    progressbar->setMinimum(0);
                    progressbar->setMaximum(0);
                    progressbar->setFormat(QString::number(num_records));
                }
                else{
                    QString str;
                    str.sprintf("%ld/%ld ", num_records, total_files);
                     progressbar->setFormat(str + "%p%");
                     progressbar->setValue(num_records * 100 / total_files);
                }
                break;
            }

        }
    }
//    if num_records == -2:
//                logger.debug("DB progress update: " + "merge temp db.")
};
