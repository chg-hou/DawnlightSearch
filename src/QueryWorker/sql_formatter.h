#ifndef SQL_FORMATTER_H
#define SQL_FORMATTER_H

#include <QString>
#include <QStack>
#include <QDateTime>
#include <QCache>

#include "globals.h"
struct Format_Sql_Result
{
    bool ok;
    QString sql_mask;  // " SELECT " + header_list.join(",") + QString(" FROM `%1` ").arg(uuid);
    QString sql_cmd; // WHERE condition
    // QString sql;
    /*
     * QString sql = sql_mask + " WHERE " + QString(" (ROWID BETWEEN %1 AND %2) AND").arg(rowid_low).arg(rowid_high)
                + " (" + sql_cmd + ") " + QString(" LIMIT %d").arg(QUERY_LIMIT);

                sql = sql_mask + where row between  + sql_cmd + Limit
*/
    bool case_sensitive_like_flag_ON;
    QSet<QPair<bool,QString >> highlight_words_Name;
    QSet<QPair<bool,QString >> highlight_words_Path;


};
Format_Sql_Result format_sql_cmd(QString path,
                       QString uuid,
                       QString sql_text,
                       unsigned long rowid_low,
                       unsigned long rowid_high);
#endif // SQL_FORMATTER_H
