#include "MainWindow.h"
#include "MainWindow.h"
#include "ui_Ui_mainwindow.h"

void MainWindow::refresh_table_uuid_from_db_slot(QList<QVariantList> rst){
    // python:  get_table_widget_uuid_back_slot
    //qDebug()<< __FILE__<< __LINE__<< __FUNCTION__ << "\n\t"<<rst;

    ui->tableWidget_uuid->setSortingEnabled(false);
    for(const QVariantList& varlist: rst)
    {
        if(varlist[UUID_HEADER.uuid].toString() == "")
        {
            qDebug()<<"EMPTY UUID: "<<__FILE__<< __LINE__<< __FUNCTION__<<"\n\t"<<rst;
            continue;
        }
        long row = _find_row_number_of_uuid(varlist[UUID_HEADER.uuid].toString());
        if (row<0)
        {// check whether uuid exists. If so, overide. If not, add new row.
            ui->tableWidget_uuid->insertRow(ui->tableWidget_uuid->rowCount());
            row = ui->tableWidget_uuid->rowCount()-1;
        }
        bool uuid_excluded_flag = EXCLUDED_UUID.contains(varlist[UUID_HEADER.uuid].toString());
        for(int idx=0; idx< varlist.length();idx++){
            QVariant col = varlist[idx];
            //            if (col.isNull())
            //                col = QVariant("");
            QTableWidgetItem * newitem;
            newitem = new QTableWidgetItem("");
            if (idx == UUID_HEADER.major_dnum || idx == UUID_HEADER.minor_dnum
                    || idx == UUID_HEADER.rows)
            {
                newitem->setData(Qt::DisplayRole, col.toInt());
            }
            else if ( idx == UUID_HEADER.included )
            {
                //                newitem = new QTableWidgetItem(col);
                //                newitem->setData(Qt::DisplayRole,"");
                if (col.toBool())
                    newitem->setCheckState(Qt::Checked);
                else
                    newitem->setCheckState(Qt::Unchecked);
                newitem->setIcon(QIcon(QPixmap(":/ui/icon/tab-close-other.png")));
                newitem->setData(Qt::DisplayRole,0);
                // hack : hide text
                QFont temp_font = newitem->font();
                temp_font.setPointSizeF(0.1);
                newitem->setFont(temp_font);
            }
            else if (idx == UUID_HEADER.updatable)
            {
                //                newitem = new QTableWidgetItem(col);
                newitem->setData(Qt::DisplayRole,"");
                if (col.toBool())
                    newitem->setCheckState(Qt::Checked);
                else
                    newitem->setCheckState(Qt::Unchecked);
            }
            else{
                newitem->setData(Qt::DisplayRole,col.toString());
            }

            if (idx > UUID_HEADER.fstype)
                newitem->setTextAlignment(Qt::AlignHCenter | Qt::AlignVCenter);

            // Excluded
            if (uuid_excluded_flag)
            {
                newitem->setForeground(Qt::gray);
                QFont temp_font = newitem->font();
                temp_font.setItalic(true);
                newitem->setFont(temp_font);
            }
            if (idx != UUID_HEADER.alias)
                newitem->setFlags((newitem->flags()) ^ Qt::ItemIsEditable  );
            else
                newitem->setForeground(Qt::blue);

            ui->tableWidget_uuid->setItem(row, idx, newitem);

        }
        if (uuid_excluded_flag && (! ui->actionShow_All->isChecked()) )
            ui->tableWidget_uuid->setRowHidden(row,true);
    }
    ui->tableWidget_uuid->setSortingEnabled(true);
//    ui->statusBar->showMessage( QCoreApplication::translate("statusbar","Almost done."), 1000 );

}


void MainWindow::refresh_table_uuid_mount_state_slot(){

    ui->tableWidget_uuid->setSortingEnabled(false);

    for(long row =0; row< ui->tableWidget_uuid->rowCount();row++){
        QString uuid = ui->tableWidget_uuid->item(row, UUID_HEADER.uuid)->data( Qt::DisplayRole).toString();
        if (! Partition_Information::uuid_set.contains(uuid))
        {
            ui->tableWidget_uuid->item(row,UUID_HEADER.included)->setIcon(
                        QIcon(QPixmap(":/icon/ui/icon/tab-close-other.png"))   );
            ui->tableWidget_uuid->item(row,UUID_HEADER.included)->setData(
                        Qt::DisplayRole,0);
        }
    }

    foreach (const Mnt_Info_Struct & device, Partition_Information::mnt_info) {
        QString uuid = device.uuid;
        long row = _find_row_number_of_uuid(uuid);
        bool uuid_excluded_flag = EXCLUDED_UUID.contains(uuid);

        if(uuid == "")
        {
            qDebug()<<"EMPTY UUID: "<<__FILE__<< __LINE__<< __FUNCTION__<<"\n\t"<<device.maj<<device.min;
            continue;
        }

        if (row<0){
            //uuid does not exist, insert now row
            //qDebug()<<"ui->tableWidget_uuid->rowCount() "<<ui->tableWidget_uuid->rowCount();
            ui->tableWidget_uuid->insertRow(ui->tableWidget_uuid->rowCount());
            //qDebug()<<"ui->tableWidget_uuid->rowCount() "<<ui->tableWidget_uuid->rowCount();
            row = ui->tableWidget_uuid->rowCount()-1;
            {
                QTableWidgetItem * newitem = new QTableWidgetItem("");
                newitem->setCheckState(Qt::Unchecked);
                newitem->setData(Qt::DisplayRole, UUID_HEADER.included);
                // Hack: hide text
                QFont temp_font = newitem->font();
                temp_font.setPointSizeF(0.1);
                newitem->setFont(temp_font);
                ui->tableWidget_uuid->setItem(row, UUID_HEADER.included, newitem);
            }
            {
                // TODO: which is better?
                QTableWidgetItem * newitem = new  QTableWidgetItem("");
                newitem->setCheckState(Qt::Unchecked);
                ui->tableWidget_uuid->setItem(row, UUID_HEADER.updatable, newitem);
            }
            {
                //                QTableWidgetItem newitem (device.uuid);
                QTableWidgetItem * newitem = new QTableWidgetItem(device.uuid);
                ui->tableWidget_uuid->setItem(row, UUID_HEADER.uuid, newitem);
            }
            QList<int> col_list;
            col_list<<UUID_HEADER.path<<UUID_HEADER.alias<<UUID_HEADER.name<<UUID_HEADER.label<<UUID_HEADER.fstype<<
                      UUID_HEADER.major_dnum<<UUID_HEADER.minor_dnum<<UUID_HEADER.rows<<UUID_HEADER.processbar;
            for (int col: col_list ) {
                ui->tableWidget_uuid->setItem(row,col,new QTableWidgetItem());
            }

            for (int col=0; col< UUID_HEADER.len;col++)
            {
                QTableWidgetItem * newitem =  ui->tableWidget_uuid->item(row,col);
                if (col != UUID_HEADER.alias)
                    newitem->setFlags((newitem->flags()) ^ Qt::ItemIsEditable  );
                else
                    newitem->setForeground(Qt::blue);
                if (col > UUID_HEADER.fstype)
                    newitem->setTextAlignment(Qt::AlignHCenter | Qt::AlignVCenter);
            }
            if (uuid_excluded_flag)
            {
                for(int col=0; col<UUID_HEADER.len;col++){
                    QTableWidgetItem * newitem =  ui->tableWidget_uuid->item(row,col);
                    if (newitem==NULL)
                    {
                        qDebug()<<"NULL item row: "<<row<<"  col: "<<col;
                        continue;
                    }
                    newitem->setForeground(Qt::gray);
                    QFont temp_font = newitem->font();
                    temp_font.setItalic(true);
                    newitem->setFont(temp_font);
                }
                if(! ui->actionShow_All->isChecked())
                    ui->tableWidget_uuid->setRowHidden(row,true);
            }
        }
        if (device.path.length()>0)
        {
            // device is mounted
            ui->tableWidget_uuid->item(row,UUID_HEADER.included)->setIcon(
                        device_mounted_icon  );
            ui->tableWidget_uuid->item(row,UUID_HEADER.included)->setData(Qt::DisplayRole,1);
        }else{
            ui->tableWidget_uuid->item(row,UUID_HEADER.included)->setIcon(
                        device_unmounted_icon   );
            ui->tableWidget_uuid->item(row,UUID_HEADER.included)->setData(Qt::DisplayRole,0);
        }

        ui->tableWidget_uuid->item(row,UUID_HEADER.path)->setData(Qt::DisplayRole,
                                                                  device.path);
        ui->tableWidget_uuid->item(row,UUID_HEADER.label)->setData(Qt::DisplayRole,
                                                                   device.label);
        ui->tableWidget_uuid->item(row,UUID_HEADER.fstype)->setData(Qt::DisplayRole,
                                                                    device.fstype);
        ui->tableWidget_uuid->item(row,UUID_HEADER.name)->setData(Qt::DisplayRole,
                                                                  device.name);
        ui->tableWidget_uuid->item(row,UUID_HEADER.major_dnum)->setData(Qt::DisplayRole,
                                                                        device.maj);
        ui->tableWidget_uuid->item(row,UUID_HEADER.minor_dnum)->setData(Qt::DisplayRole,
                                                                        device.min);
//        if (idx > UUID_HEADER.fstype)
//            newitem->setTextAlignment(Qt::AlignHCenter | Qt::AlignVCenter);
    }
    ui->tableWidget_uuid->setSortingEnabled(true);

    if (FIRST_TIME_LOAD_FLAG )
    {
        FIRST_TIME_LOAD_FLAG =false;

        if (DB_READ_ONLY_FLAG)
            setWindowTitle(windowTitle() + QCoreApplication::translate("statusbar"," [Read Only Mode]"));
        else
            ui->statusBar->showMessage( QCoreApplication::translate("statusbar","Ready."), 3000 );
    }

}

long MainWindow::_find_row_number_of_uuid(QString uuid)
{
    //qDebug()<<"  "<<uuid;
    if (ui->tableWidget_uuid->rowCount()==0)
        return -1;
    for(long row=0; row < ui->tableWidget_uuid->rowCount(); row++)
    {
        if ( uuid == ui->tableWidget_uuid->item(row, UUID_HEADER.uuid)->data(Qt::DisplayRole)) //ui->tableWidget_uuid->item(row, UUID_HEADER.uuid)->data(Qt::DisplayRole)
            return row;
    }
    return -1;

}

void MainWindow::refresh_table_uuid_row_id_slot(QList<QPair<QString,QVariant> > results){
    ui->tableWidget_uuid->setSortingEnabled(false);
    for ( const QPair<QString,QVariant> & qpair: results) {
        QString uuid = qpair.first;
        QVariant rowid = qpair.second;
        long row = _find_row_number_of_uuid(uuid);
        // uuid does not exist, continue
        if (row <0)
            continue;
        ui->tableWidget_uuid->item(row,UUID_HEADER.rows)->setData(Qt::DisplayRole,
                                                                  rowid.toInt() );
    }
    ui->tableWidget_uuid->setSortingEnabled(true);
};

