#include "sql_formatter.h"

Format_Sql_Result format_sql_cmd(QString path,
                       QString uuid,
                       QString sql_text,
                       unsigned long , //rowid_low
                       unsigned long ) //rowid_high
{



    static QCache<QPair<QPair<QString,unsigned int>,
                   QPair<QString,QString>
                        >, Format_Sql_Result> cache_sql(CONST_SQL_TEXT_FORMAT_CACHE_SIZE);

    QPair<QPair<QString, unsigned int>,QPair<QString,QString>> hash_key ( {  QPair<QString,unsigned int>   ({path, MATCH_OPTION}),
                                                        QPair<QString,QString> ( {uuid,sql_text }) } );

    if(cache_sql.contains(hash_key)){

        return *cache_sql.object(hash_key);
    }

    Format_Sql_Result  * format_sql_result = new Format_Sql_Result();

    sql_text = sql_text.trimmed(); //simplified() to replace multiple consecutive whitespaces with a single space character

    QStringList header_list = QUERY_HEADER_LIST;
    int path_idx = QUERY_HEADER.Path;

    header_list[path_idx]  = QString("\"%1\"").arg( path.replace("\"", "\"\"") ) + "||Path";

    QString sql_mask = " SELECT " + header_list.join(",") + QString(" FROM `%1` ").arg(uuid);




    int match_section = MATCH_OPTION;
    QString default_field;

    // #============================ default field===========================
    switch (match_section) {
    case 1: //# match Filename only
        default_field = "Filename";
        break;
    case 2: // # match path (without dev location) only
        default_field = "Path";
        break;
    case (1|2): // # match path(without dev location) + filename
        default_field = "Path||\"/\"||Filename";
        break;
    case 4: //  # match path(WITH dev location) only
        default_field = header_list[path_idx];
        break;
    case (1|4): // # match path(WITH dev location) + filename
        default_field = header_list[path_idx] + "||\"/\"||Filename";
        break;
    default:
        qDebug()<< "Wrong match setion"<<match_section;
        break;
    }

    // # ============================ default verb===========================
    QString default_verb = "LIKE";

    //# ============================ default case===========================
    //# default_case = ''       # 'COLLATE  nocase'
    bool case_sensitive_like_flag_ON = True;
    QString default_case;
    if (CASE_SENSTITIVE)
    {
        default_case = "";
    }
    else
    {
        default_case = " COLLATE  nocase ";
        if(  !(sql_text.contains(" case:")  ||  sql_text.contains(":case:")  ) )
            case_sensitive_like_flag_ON = False;
    }

    //

    bool quote_flag = False;
    int i = 0;

    QStack<QString> field_stack;
    QStack<QString> verb_stack;
    QStack<QString> word_stack;
    QStack<QString> case_stack;
    QStack<int> phase_count_stack;

    QSet<QPair<bool,QString >> highlight_words_Name;  // [[ case, word], .....]
    QSet<QPair<bool,QString >> highlight_words_Path;

    field_stack.push(default_field);
    verb_stack.push(default_verb);
    case_stack.push(default_case);
    phase_count_stack.push(0);

    QString sql_cmd ="";
    QString word ="";

    QList<bool> logical_tmp ( {False, False} );  //  is OR, is NOT

    bool phase_segment_flag;

    try{
        while( i < sql_text.length() )
        {
//            QChar c = sql_text[i];
            QString c (sql_text[i]);
            if ( (c==" " || c=="|" ) && (word !="") && (!quote_flag)  )
                phase_segment_flag = true;
            else
                phase_segment_flag = false;

            if (i>0 && c == ">" && QString(sql_text[i-1]) == " " && (! quote_flag) )
            {
                phase_count_stack[phase_count_stack.length()-2]++;
            }

            if (c=="\"")
            {
                if (quote_flag)
                {
                    word.append(c);
                    quote_flag = false;
                    phase_segment_flag = true;
                }
                else
                {
                    quote_flag=true;
                    word.append(c);
                }
            }
            else if ( c  == "\\" && i <sql_text.length()-1 )
            {
                word.append(sql_text[i] );
                word.append(sql_text[i+1] );
                i++;
            }
            else if (quote_flag)
            {
                word += c;
                i++;
                continue;
            }
            else if (c ==":")
            {
                if (word == "f")
                    field_stack.last()="Filename";
                else if (word == "p")
                    field_stack.last() = "Path";
                else if  (word == "pf")
                    field_stack.last() = "Path||\"/\"||Filename";
                else if (word == "dp")
                    field_stack.last() = header_list[path_idx];
                else if  (word == "ff")
                    field_stack.last() = header_list[path_idx] + "||\"/\"||Filename";
                else if  (word == "reg")
                    verb_stack.last() = "REGEXP";
                else if  (word == "noreg")
                    verb_stack.last() = "LIKE";
                else if  (word == "case")
                    case_stack.last() = "";
                else if  (word == "nocase")
                    case_stack.last() = " COLLATE  nocase ";
                else if  (word == "size")
                {
                    int size_start = i + 1;
                    while (size_start<sql_text.length() && !sql_text[size_start].isDigit())
                        size_start++;

                    QString verb = sql_text.mid(i+1, size_start - i - 1 );
                    Q_ASSERT( QStringList({"<", "=", ">", "!=", "<=", ">="}).contains(verb) );

                    int size_end = size_start;
                    while ( size_end < sql_text.length() && sql_text[size_end].isDigit()   )
                        size_end++;

                    unsigned long size = sql_text.mid(size_start, size_end - size_start).toInt();
                    if (size_end < sql_text.length()  && QString("kKmMgGtT").contains(sql_text[size_end])  )
                    {
                        if (QString(sql_text[size_end])=="k" || QString(sql_text[size_end]) =="K"  )
                            size *= 1024;
                        else if (QString(sql_text[size_end])=="m" || QString(sql_text[size_end]) =="M"  )
                            size *= 1024 * 1024;
                        else if (QString(sql_text[size_end])=="g" || QString(sql_text[size_end]) =="G"  )
                            size *= 1024l * 1024l * 1024l;
                        else if (QString(sql_text[size_end])=="t" || QString(sql_text[size_end]) =="T"  )
                            size *= 1024l * 1024l * 1024l * 1024l;
                        i = size_end +1;
                    }
                    else
                        i = size_end;

                    phase_count_stack.last()++;
                    if (phase_count_stack.last()>1)
                    {
                        if (logical_tmp[0])  // is OR
                            sql_cmd+= " OR ";
                        else
                            sql_cmd+= " AND ";
                    }
                    if (logical_tmp[1])
                        sql_cmd+= " NOT ";
                    logical_tmp[0]=false;logical_tmp[1]=false;

                    sql_cmd += QString("(") + "Size" + verb + QString::number(size) + ")";
                }

                else if (word =="folder" || word == "file")
                {
                    phase_count_stack.last()++;
                    if (phase_count_stack.last()>1)
                    {
                        if (logical_tmp[0])
                            sql_cmd += " OR ";
                        else
                            sql_cmd += " AND ";
                    }
                    if (logical_tmp[1])
                        sql_cmd += " NOT ";

                    if (word == "folder")
                        sql_cmd += "( IsFolder)";
                    else if (word == "file")
                        sql_cmd += "(NOT IsFolder)";
                    logical_tmp[0]=false;logical_tmp[1]=false;
                    word ="";
                    i++;
                    continue;
                }
                else if (word =="mtime" || word =="atime" || word == "ctime")
                {
                    int date_string_start = sql_text.indexOf("\"", i+1);
                    int date_string_end = sql_text.indexOf("\"", date_string_start + 1);
                    QString verb = sql_text.mid(i+1, date_string_start - i - 1 );


                    Q_ASSERT( QStringList({"<", "=", ">", "!=", "<=", ">="}).contains(verb) );
                    QString date_string = sql_text.mid(date_string_start+1, date_string_end- date_string_start - 1 );

                    int unixtime = date_string.toInt(); // = 0 if it fails
                    if (unixtime == 0)
                    {
                        QDateTime date = QDateTime::fromString(date_string, DATETIME_FORMAT);
                        if (! date.isValid())
                            throw std::invalid_argument( "Wrong date string:" + date_string.toStdString() );
                        unixtime = date.toTime_t();
                    }

                    phase_count_stack.last()++;
                    if (phase_count_stack.last()>1)
                    {
                        if (logical_tmp[0])  // is OR
                            sql_cmd+= " OR ";
                        else
                            sql_cmd+= " AND ";
                    }
                    if (logical_tmp[1])
                        sql_cmd+= " NOT ";

                    sql_cmd += QString("(") + word + verb + QString::number(unixtime) + ")";
                    logical_tmp[0]=false;logical_tmp[1]=false;

                    i = date_string_end;

                }

                word = "";
                i++;
                continue;
            }
            else if (c == "|")
            {
                logical_tmp[0] = true;  //# is OR
                while(  QString(sql_text[i+1]) == "|" || QString(sql_text[i+1]) == " " )
                    i++;
            }
            else if (c == " ")
            {    while(QString(sql_text[i+1]) == " " )
                    i++;
            }
            else if (c == "!")
                logical_tmp[1] = (! logical_tmp[1]);
            else if (c == "<")
            {
                if (word =="")
                {
                    if (phase_count_stack.last()>0)
                    {
                        if (logical_tmp[0])  // is OR
                            sql_cmd+= " OR ";
                        else
                            sql_cmd+= " AND ";
                    }
                    if (logical_tmp[1])
                        sql_cmd+= " NOT ";
                    logical_tmp[0]=false;logical_tmp[1]=false;
                    sql_cmd += " ( ";
                    field_stack.push(QString(field_stack.last()));
                    verb_stack.push(QString(verb_stack.last()));
                    case_stack.push(QString(case_stack.last()));
                    phase_count_stack.push(0);
                }
                else
                {
                    // larger, less than
                }
            }
            else if (c == ">")   //# insert ")" after sql_cmd inserted.
            {}
            else
                word+=c;


            if (i==sql_text.length()-1 &&
                    ( !quote_flag && c!="\""  )
                    )                               // text end
                phase_segment_flag = true;

            if (phase_segment_flag && word != "")
            {
                phase_count_stack.last()++;
                word_stack.clear();
                for(QString tmpstring: word.trimmed())
                    word_stack.push(tmpstring);
                word = "";
                if (phase_count_stack.last()>1)
                {
                    if (logical_tmp[0])
                        sql_cmd += " OR ";
                    else
                        sql_cmd += " AND ";
                }
                if (logical_tmp[1])
                    sql_cmd+= " NOT ";


                //sql_cmd += build_query();
                QString build_query;
                // build query
                {
                    QString field = field_stack.last();
                    QString verb = verb_stack.last();
                    QString _case  = case_stack.last();
                    bool regexp_flag = (verb == "REGEXP");

                    // # highlight list
                    //get_highlight_word()
                    if (!regexp_flag)
                    {
                        QStack<QString> word_stack_tmp= word_stack;
                        if (word_stack_tmp.first()=="\"" && word_stack_tmp.last()=="\"")
                        {
                            word_stack_tmp.pop_back();word_stack_tmp.pop_front();
                        }

                        QStringList tmp3;
                        for(QString i: word_stack_tmp){
                            tmp3<<i;
                        }
                        QString word_temp = tmp3.join("");

                        if (!word_temp.contains("*") && !word_temp.contains("?") )
                        {
                            if (field.endsWith("Filename")    )
                            {
                                highlight_words_Name.insert(QPair<bool, QString>({ (_case =="") , word_temp}  ));
                            }

                            if (field.endsWith("Path||\"/\"||Filename") ||
                                 field.endsWith("Path")   )
                            {
                                 highlight_words_Path.insert(QPair<bool, QString>({ (_case =="") , word_temp}  ));

                            }
                        }
                    }//  END  get_highlight_word()

                    //# sql parser
                    QString word_tmp = "";
                    bool exact_match = False;
//                    bool wildcard  = False;

                    //exact_match, wildcard,  word = parser_word()       # any wildcard will enable LIKE matach -- exact_match = False.
                    {

                        bool return_flag = false;

                        if (word_stack.first()=="\"" && word_stack.last()=="\"")
                        {
                            exact_match = True;
                            word_stack.pop_back();word_stack.pop_front();
                        }
                        if (regexp_flag && exact_match)
                        {
                            QStringList tmp2;
                            for(QString i: word_stack){
                                tmp2<<i;
                            }
                            word_tmp = tmp2.join("").replace("\\\"","\"\""); // ''.join(word_stack).replace('\\"','""')
                            // return [exact_match, wildcard, word_tmp]
                            return_flag = true;
                        }

                        if (!return_flag)
                        {
                            int i =0;
                            while (i<word_stack.length())
                            {
                                QString c = word_stack[i];
                                if (c=="\\" && i < (word_stack.length()-1))
                                {
                                    if (word_stack[i+1]=="\"")
                                        word_tmp += "\"\"";
                                    else
                                        word_tmp += word_stack[i] + word_stack[i+1];
                                    i+=1;
                                }
                                else if (c=="\"")
                                    word_tmp += "\"\"";
                                else if (c =="%" || c =="_")
                                    word_tmp += "\\" + c;
                                else if (c =="*")
                                {
//                                    wildcard = true;
                                    word_tmp += "%";
                                }
                                else if (c =="?")
                                {
//                                    wildcard = true;
                                    word_tmp += "_";
                                }
                                else
                                    word_tmp += word_stack[i];
                                i++;
                            }
                            word_stack.clear();
                            // return [exact_match, wildcard, word_tmp]
                        }

                    }// END parser_word

                    bool build_query_done = false;
                    if ( regexp_flag && exact_match)
                    {
                        build_query = "(" + field + " REGEXP \"" + word_tmp + "\" " + _case + ")";
                        //return build_query
                        build_query_done = true;
                    }
//                    # http://stackoverflow.com/questions/543580/equals-vs-like
//                    # if exact_match and (not wildcard):
//                    #     verb = '='
//                    # if wildcard:
//                    #     verb = 'LIKE'
//                    ##  overwrite ALL '='. '=" does not support ESCAPE.
                    if (!build_query_done)
                    {
                        verb = "LIKE";
                        if (! exact_match)
                            word_tmp = "%" + word_tmp + "%";
                        build_query = "(" + field + " " + verb + " \"" + word_tmp + "\" ESCAPE \"\\\" " + _case + ")" ;

                        if (case_sensitive_like_flag_ON)
                            if (! (_case ==""))  //' COLLATE  nocase '
                                build_query = "( UPPER(" + field + ") " + verb + " \"" + word_tmp.toUpper() + "\" ESCAPE \"\\\" " + _case + ")";

                    }
                }// build_query END
                sql_cmd += build_query;
                logical_tmp[0]=false;logical_tmp[1]=false;
            }

            if (c ==">")
            {
                field_stack.pop();
                verb_stack.pop();
                case_stack.pop();
                phase_count_stack.pop();
                sql_cmd += " ) ";
            }
            i++;
        }

//        QString sql = sql_mask + " WHERE " + QString(" (ROWID BETWEEN %1 AND %2) AND").arg(rowid_low).arg(rowid_high)
//                + " (" + sql_cmd + ") " + QString(" LIMIT %d").arg(QUERY_LIMIT);
//        // return True, sql_mask, sql_cmd,sql , case_sensitive_like_flag_ON, highlight_words
        format_sql_result->ok=true;
        format_sql_result->sql_mask = sql_mask;
        format_sql_result->sql_cmd = sql_cmd;
        format_sql_result->case_sensitive_like_flag_ON = case_sensitive_like_flag_ON;
        format_sql_result->highlight_words_Name = highlight_words_Name;
        format_sql_result->highlight_words_Path = highlight_words_Path;

        //cache_sql.object(hash_key)
//        cache_sql.insert(hash_key, format_sql_result );

//        return  format_sql_result;

//        struct Format_Sql_Result
//        {
//            bool ok;
//            QString sql_mask;  // " SELECT " + header_list.join(",") + QString(" FROM `%1` ").arg(uuid);
//            QString sql_cmd; // WHERE condition
//            bool case_sensitive_like_flag_ON;
//            QList<QPair<bool,QString >> highlight_words_Name;
//            QList<QPair<bool,QString >> highlight_words_Path;
//        };

    }
    catch(...)
    {
        format_sql_result->ok=false;
        // return False, None, str(e), None, case_sensitive_like_flag_ON, highlight_words
//        return format_sql_result;
    }

    //cache_sql.object(hash_key)
    cache_sql.insert(hash_key, format_sql_result );
    // *cache_sql.object(hash_key)
    return  *format_sql_result;

}
