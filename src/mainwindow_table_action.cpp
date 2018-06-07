




#include "MainWindow.h"
#include "ui_Ui_mainwindow.h"


#include <QMimeType>
#include <QMimeDatabase>

QString MainWindow::_get_filetype_of_selected()
{
    QSet<QString> file_type_set;
    for (const ResultTableRow & row: get_tableview_selected())
    {
        if (row.isfolder)
            return "folder";
        // TODO: guess from content
        QMimeType type = QMimeDatabase().mimeTypeForFile(row.filename,
                                                         QMimeDatabase::MatchExtension);
        file_type_set.insert(type.name());
        if (file_type_set.count()!=1)
            return "folder";
    }
    if (file_type_set.count()==1)
        return file_type_set.toList().first();
    else
        return "";
}
QList< ResultTableRow > MainWindow::get_tableview_selected()
{
    QSet<int> row_set;
    for ( const QModelIndex & idx: ui->tableView->selectionModel()->selectedIndexes())
    {
        int row = idx.row();
        row_set.insert(row);
    }

    QList<ResultTableRow > rst;
    for ( int row: row_set)
    {
        ResultTableRow row_to_insert;
        QString filename =  model->item(row, DB_HEADER.Filename)->data(HACKED_QT_EDITROLE).toString();
        QString path   =  model->item(row, DB_HEADER.Path)->data(HACKED_QT_EDITROLE).toString();
        QString fullpath = path + QDir::separator() + filename;

//        qDebug()<<path<<filename<<fullpath;

        fullpath.replace("//","/");
        bool isfolder = model->item(row, DB_HEADER.IsFolder)->data(HACKED_QT_EDITROLE).toBool();

        row_to_insert.filename = filename;
        row_to_insert.path = path;
        row_to_insert.fullpath = fullpath;
        row_to_insert.isfolder = isfolder;

        rst << row_to_insert;
    }
    return rst;

}

#ifdef USE_GIO_LIB_FOR_OPENWITH_MENU

QIcon get_app_icon_qicon(GAppInfo *default_app_info)
{
    // https://stackoverflow.com/questions/29360763/convert-gicon-to-qicon
    // GAppInfo *appInfo = (GAppInfo *)g_desktop_app_info_new("vlc.desktop");

    // TODO: check memory leak

    GtkIconInfo *pGtkIconInfo;
    if (default_app_info== NULL)
        return QIcon();
    GIcon *  gicon = g_app_info_get_icon(default_app_info);
    if (gicon== NULL)
        return QIcon();
    //    GtkIconTheme *pGtkIconTheme= gtk_icon_theme_get_default();
    //    pGtkIconInfo=gtk_icon_theme_lookup_by_gicon(pGtkIconTheme,pgIcon,
    //                                                256,GTK_ICON_LOOKUP_USE_BUILTIN);
    QList<int> sizes; sizes << 16 << 24 << 32 << 48 << 64<<96<<128<<256;
    QIcon qicon;
    foreach(int size, sizes)
    {
        GtkIconInfo *iconInfo = gtk_icon_theme_lookup_by_gicon(
                    gtk_icon_theme_get_default(),
                    gicon, size, (GtkIconLookupFlags)0);
        GdkPixbuf *pixbuf = gtk_icon_info_load_icon(iconInfo, NULL);
        if (pixbuf == NULL)
            continue;

        QImage image = QImage(
                    gdk_pixbuf_get_pixels(pixbuf),
                    gdk_pixbuf_get_width(pixbuf),
                    gdk_pixbuf_get_height(pixbuf),
                    gdk_pixbuf_get_rowstride(pixbuf),
                    QImage::Format_ARGB32);
        g_object_unref(pixbuf);
        qicon.addPixmap(QPixmap::fromImage( image));
        break;
    }
    g_object_unref(gicon);
    return qicon;
    //    g_clear_object(&icon);
    //    g_clear_object(&pGtkIconTheme);

};

AppLauncher MainWindow::get_default_app(QString file_type){
    // https://developer.gnome.org/gio/stable/GAppInfo.html

    std::string s2 = file_type.toStdString();
    const char * c3_file_type = s2.c_str();

    GAppInfo *default_app_info = g_app_info_get_default_for_type (
                c3_file_type,
                FALSE);
    if (default_app_info== NULL)
    {
        return  AppLauncher({QIcon(), "","", NULL}); //return None, None, None, None, None
    }

    //GIcon *  icon = g_app_info_get_icon(default_app_info);
    const char * app_tooltip =  g_app_info_get_description(default_app_info);
    const char * app_name = g_app_info_get_name(default_app_info);
    const char * commandline  = g_app_info_get_commandline(default_app_info);
    const char * executable  =   g_app_info_get_executable (default_app_info);
    //  xx  GFile * icon_file = g_file_icon_get_file( icon);

    QIcon qicon = get_app_icon_qicon(default_app_info);

    // g_object_unref (icon);
    // g_free(app_info);
    //g_object_unref(app_info);

    // https://developer.gnome.org/programming-guidelines/unstable/memory-management.html.en
    //g_object_unref(default_app_info);
    g_object_ptr_trarsh << default_app_info;
    //g_object_unref(icon);

    return AppLauncher( {qicon, QString(app_name), QString(app_tooltip), default_app_info});

}

void MainWindow::_on_tableview_context_menu_requested(QPoint){

    QMenu menu(this);
    //TODO: opt, called get_tableview_selected twice
    QString file_type = _get_filetype_of_selected();
    QList<ResultTableRow > selected_rows = get_tableview_selected();
    AppLauncher applauncher = get_default_app(file_type);
    if (true || file_type =="" || file_type =="folder" || applauncher.appname=="")
    {
        menu.addAction(QApplication::translate("menu","Open" ),
                       this, SLOT(_on_tableview_context_menu_open()));
    }
    else
    {
        //        menu.addAction(QString::sprintf( QApplication::translate("menu",
        //                                              "Open with \"%s\"" ),
        //                                         applauncher.appname),
        //                       );
    }

    QPoint point = QCursor::pos();
    menu.exec(point);

};
void MainWindow::_on_tableview_context_menu_requested(QPoint){

    QMenu menu(this);
    //TODO: opt, called get_tableview_selected twice
    QString file_type = _get_filetype_of_selected();
    QList<ResultTableRow > selected_rows = get_tableview_selected();
    //    AppLauncher applauncher = get_default_app(file_type);
    //    if (true || file_type =="" || file_type =="folder" || applauncher.appname=="")
    //    {
    //        menu.addAction(QApplication::translate("menu","Open" ),
    //                       this, SLOT(_on_tableview_context_menu_open()));
    //    }
    //    else
    //    {
    ////        menu.addAction(QString::sprintf( QApplication::translate("menu",
    ////                                              "Open with \"%s\"" ),
    ////                                         applauncher.appname),
    ////                       );
    //    }

    QPoint point = QCursor::pos();
    menu.exec(point);

};
#endif


#ifdef USE_KDELIBS_LIB_FOR_OPENWITH_MENU

void MainWindow::get_default_app(){
    QString file_type;

    // addOpenWithActionsTo
    // preferredOpenWithAction


}
#endif

#ifdef USE_KF5_LIB_FOR_OPENWITH_MENU

void MainWindow::get_default_app(QString )//file_type
{


    // addOpenWithActionsTo
    // preferredOpenWithAction


}
void MainWindow::_on_tableview_context_menu_requested(QPoint){

    QMenu menu(this);
    //TODO: opt, called get_tableview_selected twice
    QString file_type = _get_filetype_of_selected();
    QList<ResultTableRow > selected_rows = get_tableview_selected();

    // https://api.kde.org/frameworks/kio/html/classKFileItemActions.html
    KFileItemActions kfileitem_actions(&menu);
    KFileItemListProperties kfileitem_list_prop;
    QList< KFileItem > qlist_kfielitem;
    QList<QUrl> qlist_file_to_copy;
    for(const ResultTableRow & row: selected_rows)
    {
        // TODO: guess from content
        QMimeType type = QMimeDatabase().mimeTypeForFile(row.fullpath,
                                                         QMimeDatabase::MatchDefault);
        KFileItem kfielitem(QUrl::fromLocalFile(row.fullpath), type.name());
        qlist_file_to_copy<<QUrl::fromLocalFile(row.fullpath);
        qlist_kfielitem << kfielitem;
    }
    KFileItemList kfileitem_list(qlist_kfielitem);
    kfileitem_list_prop.setItems(kfileitem_list);
    kfileitem_actions.setItemListProperties(kfileitem_list_prop);

    QAction * action = kfileitem_actions.preferredOpenWithAction("");

    if(action == nullptr)
    {
        menu.addAction(QApplication::translate("menu","Open"),
                       this, SLOT(_on_tableview_context_menu_open()));
    }
    else
    {
        menu.addAction(action);
        kfileitem_actions.addOpenWithActionsTo(&menu);
        for(QAction * action : menu.actions())
            if(action->isSeparator())
                menu.removeAction(action);
    }
    menu.addAction(QApplication::translate("menu","Open path"),
                   this, SLOT(_on_tableview_context_menu_open_path()));

    //==============================================================================
    menu.addSeparator();


    QMenu * copy_menu = menu.addMenu(QApplication::translate("menu","Copy ..."));

    copy_menu->addAction(QApplication::translate("menu","Copy fullpath"),
                   this, SLOT(_on_tableview_context_menu_copy_fullpath()));
    copy_menu->addAction(QApplication::translate("menu","Copy filename"),
                   this, SLOT(_on_tableview_context_menu_copy_filename()));
    copy_menu->addAction(QApplication::translate("menu","Copy path"),
                   this, SLOT(_on_tableview_context_menu_copy_path()));

    KFileCopyToMenu kfile_copytomenu (copy_menu);
    kfile_copytomenu.setUrls(qlist_file_to_copy);
    kfile_copytomenu.addActionsTo(copy_menu);

    menu.addMenu(copy_menu);

    //==============================================================================
    menu.addSeparator();

    QAction * trash_it = menu.addAction(QIcon(QPixmap(":/icon/ui/icon/user-trash.png")),
                   QApplication::translate("menu","Move to trash"),
                                      this, SLOT(_on_tableview_context_menu_move_to_trash()));
    // TODO: trash files
    trash_it->setDisabled(true);

    menu.addAction(QIcon(QPixmap(":/icon/ui/icon/application-exit.png")),
                   QApplication::translate("menu","Delete"),
                                      this, SLOT(_on_tableview_context_menu_delete()));

    QPoint point = QCursor::pos();
    menu.exec(point);

};

#endif



void MainWindow::_on_tableview_context_menu_open(){
    QList<ResultTableRow > selected_rows = get_tableview_selected();
    for(const ResultTableRow  & row : selected_rows)
    {
        QDesktopServices::openUrl(QUrl::fromLocalFile(row.fullpath));
    }
};
void MainWindow::_on_tableview_context_menu_open_path(){
    QList<ResultTableRow > selected_rows = get_tableview_selected();
    for(const ResultTableRow  & row : selected_rows)
    {
        QDesktopServices::openUrl(QUrl::fromLocalFile(row.path));
    }
};


void MainWindow::_on_tableview_context_menu_copy_fullpath(){
//    QClipboard* cb =  QApplication::clipboard();
//    QMimeData md;
    QList<QUrl> qlist_file_to_copy;
    QStringList pathlist;
    for(const ResultTableRow  & row : get_tableview_selected())
    {
//        qlist_file_to_copy << QUrl::fromLocalFile(row.fullpath);
        pathlist << row.fullpath;
    }
//    md.setUrls(qlist_file_to_copy);
//    md.setText(pathlist.join("\n"));
//    QApplication::clipboard()->setMimeData(&md);

    QApplication::clipboard()->setText(pathlist.join("\n"));
}

void MainWindow::_on_tableview_context_menu_copy_filename(){
//    QMimeData md;
    QStringList pathlist;
    for(const ResultTableRow  & row : get_tableview_selected())
    {
        pathlist << row.filename;
    }
//    md.setText(pathlist.join("\n"));
//    QApplication::clipboard()->setMimeData(&md, QClipboard::Clipboard);

    QApplication::clipboard()->setText(pathlist.join("\n"));
}

void MainWindow::_on_tableview_context_menu_copy_path(){
//    QMimeData md;
    QList<QUrl> qlist_file_to_copy;
    QStringList pathlist;
    for(const ResultTableRow  & row : get_tableview_selected())
    {
//        qlist_file_to_copy << QUrl::fromLocalFile(row.path);
        pathlist << row.path;
    }
//    md.setUrls(qlist_file_to_copy);
//    md.setText(pathlist.join("\n"));
//    QApplication::clipboard()->setMimeData(&md, QClipboard::Clipboard);
    QApplication::clipboard()->setText(pathlist.join("\n"));
}

void MainWindow::_on_tableview_context_menu_move_to(){};
void MainWindow::_on_tableview_context_menu_copy_to(){};
void MainWindow::_on_tableview_context_menu_move_to_trash(){
    // TODO:
    // https://api.kde.org/frameworks/kio/html/namespaceKIO.html#aac1528c9af76659d1e039453db0cba59

};
void MainWindow::_on_tableview_context_menu_delete(){
    QStringList pathlist;
    for(const ResultTableRow  & row : get_tableview_selected())
    {
        pathlist << row.path;
    }
    QMessageBox::StandardButton reply;
    reply = QMessageBox::question(this,  QApplication::translate("message","Message"),
                         QApplication::translate("message","Are you sure to DELETE?"),
                         QMessageBox::Yes| QMessageBox::No, QMessageBox::No
                         );
    if (reply != QMessageBox::Yes)
    {
        return;
    }
    for (QString filename: pathlist)
    {
        QFile::remove(filename);
    }
    ui->statusBar->showMessage( QApplication::translate("statusbar","Done."),3000);

};
