# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import print_function
from __future__ import print_function
from __future__ import print_function
from __future__ import print_function
from __future__ import print_function
from __future__ import absolute_import
from PyQt5.QtCore import QDateTime
try:
    from .._Global_DawnlightSearch import *
except:
    DB_HEADER_LIST = ['Filename', 'Path', 'Size', 'IsFolder',
                  'atime', 'mtime', 'ctime']
    class temp:
        pass
    GlobalVar = temp()
    GlobalVar.QUERY_LIMIT = 10
    GlobalVar.DATETIME_FORMAT = 'd/M/yyyy h:m:s'
    GlobalVar.MATCH_OPTION = 1
    GlobalVar.CASE_SENSTITIVE = False
# def parser_word(word_stack):
#     exact_match = False
#     word_tmp = ''
#     if word_stack[0] == '"' and word_stack[-1] == '"':
#         exact_match = True
#         word_stack[:] = word_stack[1:-1]
#     i = 0
#     while i < len(word_stack):
#         c = word_stack[i]
#         if c == '\\' and i < len(word_stack) - 1:
#             if word_stack[i + 1] == '"':
#                 word_tmp += '""'
#             else:
#                 word_tmp += word_stack[i] + word_stack[i + 1]
#             i += 1
#         elif c == '"':
#             word_tmp += '""'
#         elif c == '%' or c == '_':
#             word_tmp += '\\' + c
#         elif c == '*':
#             word_tmp += '%'
#         elif c == '?':
#             word_tmp += '_'
#         else:
#             word_tmp += word_stack[i]
#         i+=1
#     return [exact_match, word_tmp]

def format_sql_cmd(sql_dict):
    highlight_words = {'Name':[],'Path':[]}         # List:[[ case, word], .....]
    def escape_str(text):
        return '''"%s"''' % text.replace("\"", "\"\"")

    # 'path': table['path'],
    # 'uuid': table['uuid'],
    # 'sql_text': sql_text,
    # 'rowid_low': rowid_low,
    # 'rowid_high': rowid_high,
    # ======================================
    path        = sql_dict['path']
    uuid        = sql_dict['uuid']
    sql_text    = sql_dict['sql_text']
    rowid_low   = sql_dict['rowid_low']
    rowid_high  = sql_dict['rowid_high']

    # match_section = GlobalVar.MATCH_OPTION

    sql_text = sql_text.strip()

    header_list = DB_HEADER_LIST[:]
    path_idx = header_list.index('Path')
    header_list[path_idx] = '''"%s"''' % path.replace("\"", "\"\"") +\
                            "||Path"
    sql_mask = " SELECT " + ",".join(header_list) + (' FROM `%s` ' % uuid)

    match_section = GlobalVar.MATCH_OPTION
    # print "GlobalVar.MATCH_OPTION:",GlobalVar.MATCH_OPTION
    # print "match_section:", match_section
    #============================ default field===========================
    if match_section == 1:      # match Filename only
        default_field = 'Filename'
    elif match_section == 2:    # match path (without dev location) only
        default_field = 'Path'
    elif match_section == 1|2:  # match path(without dev location) + filename
        default_field = '''Path||"/"||Filename'''
    elif match_section == 4:    # match path(WITH dev location) only
        default_field = header_list[path_idx]
    elif match_section == 1|4:  # match path(WITH dev location) + filename
        default_field = header_list[path_idx] + '''||"/"||Filename'''

    # ============================ default verb===========================
    default_verb = 'LIKE'

    # ============================ default case===========================
    # default_case = ''       # 'COLLATE  nocase'
    case_sensitive_like_flag_ON = True
    if GlobalVar.CASE_SENSTITIVE:
        default_case = ''
    else:
        default_case = ' COLLATE  nocase '
        if not (' case:' in sql_text or ':case:' in sql_text):
            case_sensitive_like_flag_ON = False




    # ====================================================================
    sql_cmd = ''
    sql_cmd_list = []
    word_list = []
    tmp_section = ''
    quot_flag = False
    i = 0
    last_verb = ''
    last_field = ''
    last_word = ''

    field_stack = []
    verb_stack = []
    word_stack = []
    case_stack = []

    field_stack.append(default_field)
    verb_stack.append(default_verb)
    case_stack.append(default_case)
    phase_count_stack = [0]

    def get_highlight_word():
        field = field_stack[-1]
        verb = verb_stack[-1]
        case = case_stack[-1]
        regexp_flag = verb == "REGEXP"

        if verb == "REGEXP":
            return

        word_stack_tmp = word_stack[:]
        if word_stack_tmp[0] == '"' and word_stack_tmp[-1] == '"':
            word_stack_tmp[:] = word_stack_tmp[1:-1]
        word_temp = ''.join(word_stack_tmp)

        if '*' in word_temp or '?' in word_temp:
            return

        if field.endswith('Filename'):
            if case == '':
                highlight_words['Name'].append([1, word_temp])
            else:
                highlight_words['Name'].append([0, word_temp])

        if field.endswith('Path||"/"||Filename') or field.endswith('Path'):
            if case == '':
                highlight_words['Path'].append([1, word_temp])
            else:
                highlight_words['Path'].append([0, word_temp])

    def parser_word():
        verb = verb_stack[-1]
        regexp_flag = verb == "REGEXP"
        exact_match = False
        wildcard  = False
        word_tmp = ''
        if word_stack[0] == '"' and word_stack[-1] == '"':
            exact_match = True
            word_stack[:] = word_stack[1:-1]

        if regexp_flag and exact_match:
            word_tmp = ''.join(word_stack).replace('\\"','""')
            return [exact_match, wildcard, word_tmp]

        i = 0
        while i < len(word_stack):
            c = word_stack[i]
            if c == '\\' and i < len(word_stack) - 1:
                if word_stack[i + 1] == '"':
                    word_tmp += '""'
                else:
                    word_tmp += word_stack[i] + word_stack[i + 1]
                i += 1
            elif c == '"':
                word_tmp += '""'
            elif c == '%' or c == '_':
                word_tmp += '\\' + c
            elif c == '*':
                wildcard = True
                word_tmp += '%'
            elif c == '?':
                wildcard = True
                word_tmp += '_'
            else:
                word_tmp += word_stack[i]

            i += 1
        word_stack[:] = []
        return [exact_match, wildcard, word_tmp]

    def build_query():
        field = field_stack[-1]
        verb  = verb_stack[-1]
        case  = case_stack[-1]
        regexp_flag = verb == "REGEXP"

        # highlight list
        get_highlight_word()

        # sql parser
        exact_match, wildcard,  word = parser_word()       # any wildcard will enable LIKE matach -- exact_match = False.

        if ( regexp_flag and exact_match):
            sql_cmd = '(' + field + ' REGEXP "' + word + ' ' + case + ')'
            return sql_cmd


        if exact_match and (not wildcard):
            verb = '='
        if wildcard:
            verb = 'LIKE'
        if verb == 'LIKE' and (not exact_match):
            word = "%" + word + "%"

        sql_cmd = '(' + field + ' ' + verb + ' "' + word + '" ESCAPE "\\" ' + case + ')'

        if verb == 'LIKE':
            if case_sensitive_like_flag_ON:
                if case == '':  # case sensitive
                    pass
                else:        #   ' COLLATE  nocase '
                    sql_cmd = '( UPPER(' + field + ') ' + verb + ' "' + word.upper() + '" ESCAPE "\\" ' + case + ')'
            else:
                # global no case
                pass


        return sql_cmd

    sql_cmd = ''
    sql = ''
    word = ''
    qutoe_flag = False
    logical_tmp = [False ,False]  #  is OR, is NOT

    try:
        while i < len(sql_text):
            c = sql_text[i]
            if c in ' |' and word != '' and (not qutoe_flag):
                phase_segment_flag = True
                # phase_count_stack[-1] += 1
            else:
                phase_segment_flag = False

            if c == '>' and sql_text[i-1] == ' ' and (not qutoe_flag):
                phase_count_stack[-2] += 1

            if c == '\"':
                # exact-match
                if qutoe_flag:
                    # qutoe end
                    word += c
                    qutoe_flag = False
                    phase_segment_flag = True
                else:
                    qutoe_flag = True
                    # word_stack = list(word.strip())
                    word += c
            elif c  == '\\' and i <len(sql_text)-1:
                word += sql_text[i] + sql_text[i + 1]
                i += 1
            elif qutoe_flag:
                word += c
                i += 1
                continue
            elif c == ':':
                if word == 'f':
                    field_stack[-1] = 'Filename'
                elif word == 'p':
                    field_stack[-1] = 'Path'
                elif word == 'pf':
                    field_stack[-1] = '''Path||"/"||Filename'''
                elif word == 'dp':
                    field_stack[-1] = header_list[path_idx]
                elif word == 'ff':
                    field_stack[-1] = header_list[path_idx] + '''||"/"||Filename'''
                elif word == 'reg':
                    verb_stack[-1] = 'REGEXP'
                elif word == 'noreg':
                    verb_stack[-1] = 'LIKE'
                elif word == 'case':
                    case_stack[-1] = ''
                elif word == 'nocase':
                    case_stack[-1] = ' COLLATE  nocase '
                elif word == 'size':
                    size_start = i + 1
                    while size_start < len(sql_text) and not (sql_text[size_start] in '0123456789'):
                        size_start += 1

                    verb = sql_text[i + 1: size_start]
                    assert verb in ['<', '=', '>', '!=', '<=', '>=']

                    size_end = size_start
                    while size_end < len(sql_text) and sql_text[size_end] in '0123456789' :
                        size_end += 1
                    size = int(sql_text[size_start:size_end])
                    if size_end < len(sql_text) and sql_text[size_end] in 'kKmMgGtT' :
                        if sql_text[size_end] in 'kK':
                            size *= 1024
                        elif sql_text[size_end] in 'mM':
                            size *= 1024 * 1024
                        elif sql_text[size_end] in 'Gg':
                            size *= 1024 * 1024 * 1024
                        elif sql_text[size_end] in 'tT':
                            size *= 1024 * 1024 * 1024 * 1024
                        i = size_end +1
                    else:
                        i = size_end

                    phase_count_stack[-1] += 1
                    if phase_count_stack[-1] > 1:
                        if logical_tmp[0]:  # is OR
                            sql_cmd += ' OR '
                        else:
                            sql_cmd += ' AND '
                    if logical_tmp[1]:
                        sql_cmd += ' NOT '
                    logical_tmp[:] = [False, False]

                    sql_cmd += '(' + 'Size' + verb + str(size) + ')'

                elif word == 'folder' or word == 'file':
                    phase_count_stack[-1] += 1
                    if phase_count_stack[-1] > 1:
                        if logical_tmp[0]:  # is OR
                            sql_cmd += ' OR '
                        else:
                            sql_cmd += ' AND '
                    if logical_tmp[1]:
                        sql_cmd += ' NOT '

                    if word == 'folder':
                        sql_cmd +=  '( IsFolder)'
                    elif word == 'file':
                        sql_cmd += '(NOT IsFolder)'
                    logical_tmp[:] = [False, False]
                    word = ''
                    i += 1
                    continue

                elif word == "mtime" or word == "atime" or word == "ctime":
                    date_string_start = sql_text.index('"', i + 1)
                    date_string_end = sql_text.index('"', date_string_start + 1)
                    verb = sql_text[i + 1 : date_string_start]


                    assert verb in ['<','=','>','!=','<=','>=']
                    date_string = sql_text[date_string_start+1 : date_string_end]

                    try:
                        unixtime = int(date_string)
                    except:
                        unixtime = None
                    if unixtime is None:
                        date = QDateTime.fromString(date_string, GlobalVar.DATETIME_FORMAT)
                        if date.toString() == '':
                            raise Exception('Fail to format date string:\n%s\n%s' % (GlobalVar.DATETIME_FORMAT,
                                                                                     date_string) )
                        unixtime = date.toTime_t()

                    phase_count_stack[-1] += 1
                    if phase_count_stack[-1] > 1:
                        if logical_tmp[0]:  # is OR
                            sql_cmd += ' OR '
                        else:
                            sql_cmd += ' AND '
                    if logical_tmp[1]:
                        sql_cmd += ' NOT '

                    sql_cmd += '(' + word + verb + str(unixtime) + ')'
                    logical_tmp[:] = [False, False]

                    i = date_string_end

                word = ''
                i += 1
                continue
            elif c == '|':
                logical_tmp[0] = True  # is OR
                # if word != '':
                    # word_stack = list(word.strip())
                    # word = ''
                    # sql_cmd += build_query()
                while sql_text[i + 1] == '|' or sql_text[i + 1] == ' ':
                    i += 1
            elif c == ' ':
                # if logical_tmp == '':           #   <SPACE>|<SPACE>
                #     logical_tmp = ' AND '
                # if word != '':
                #     word_stack = list(word.strip())
                #     word = ''
                #     sql_cmd += build_query()
                while sql_text[i+1] == ' ':
                    i += 1
            elif c == '!':
                logical_tmp[1] = not logical_tmp[1]
            elif c == '<':
                if word == '':
                    if phase_count_stack[-1] > 0:
                        if logical_tmp[0]:  # is OR
                            sql_cmd += ' OR '
                        else:
                            sql_cmd += ' AND '
                    if logical_tmp[1]:
                        sql_cmd += ' NOT '
                    logical_tmp[:] = [False, False]
                    sql_cmd += ' ( '
                    field_stack.append(field_stack[-1])
                    verb_stack.append(verb_stack[-1])
                    case_stack.append(case_stack[-1])
                    phase_count_stack.append(0)
                else:
                    pass    # larger, less than

            elif c == '>':      # insert ")" after sql_cmd inserted.
                pass

            else:
                word += c

            if i == len(sql_text)-1 and ( (not quot_flag) and c != '"' ):        # Text end
                phase_segment_flag = True
                # phase_count_stack[-1]+=1

            if (phase_segment_flag and word != ''):
                phase_count_stack[-1] += 1
                word_stack = list(word.strip())
                word = ''
                if phase_count_stack[-1]>1:
                    if logical_tmp[0]:      # is OR
                        sql_cmd += ' OR '
                    else:
                        sql_cmd += ' AND '
                if logical_tmp[1]:
                    sql_cmd += ' NOT '



                sql_cmd += build_query()
                logical_tmp[:] = [False,False]

            if c == '>' :
                field_stack.pop()
                verb_stack.pop()
                case_stack.pop()
                phase_count_stack.pop()
                sql_cmd += ' ) '

            i+=1

        # print sql_mask
        # print sql_text
        # print sql_cmd
        # print word_list
        sql = sql_mask + ' WHERE ' + ' (ROWID BETWEEN %s AND %s) AND' % (rowid_low, rowid_high)\
              + ' (' + sql_cmd + ') ' + " LIMIT %d" % GlobalVar.QUERY_LIMIT

        # if case_sensitive_like_flag_ON:
        #     sql = ' PRAGMA case_sensitive_like=ON; ' + sql
        # else:
        #     sql = ' PRAGMA case_sensitive_like=OFF; ' + sql

        # OK_flag
        return True, sql_mask, sql_cmd,sql , case_sensitive_like_flag_ON, highlight_words
    except Exception as e:
        return False, None, str(e), None, case_sensitive_like_flag_ON, highlight_words

    # sql_where = []
    # for i in sql_text.split(' '):
    #     if i:
    #         sql_where.append(''' (`Filename` LIKE "%%%%%s%%%%") ''' % i)  # FIXME: ugly sql cmd
    # sql_where = " WHERE " + " AND ".join(sql_where)
    # sql_mask = sql_mask + sql_where
    #
    #
    #
    # if "WHERE" in sql_comm.upper():
    #     sql_comm_2 = sql_comm + '  AND  (ROWID BETWEEN %s AND %s) ' % (rowid_low, rowid_high)
    # else:
    #     sql_comm_2 = sql_comm + ' WHERE (ROWID BETWEEN %s AND %s) ' % (rowid_low, rowid_high)
    # sql_comm_2 += " LIMIT %d" % GlobalVar.QUERY_LIMIT
    # tmp_q.append({'query_id': query_id, 'sql_comm': sql_comm_2})


if __name__ == '__main__':

    ## xxx:  (Filename Like "%CORE%" COLLATE  noCASE)
    ## Correct:  PRAGMA case_sensitive_like=Off;


    # print '''"b * ? _ % \"a"'''
    # print parser_word(list('''"b * ? _ % \"a"'''))
    # exit(0)
    # sql_text ='''<aa bb> | cc <dd | e\Fe>'''
    sql_text = '''a <b | c> d e'''
    sql_text = '''a  <  b  > e'''
    sql_text = '''a < <  b  > < e | d > > e'''

    sql_text = '''  a b nocase: c case: d  "cd*v" '''
    sql_text = '''a b'''
    sql_text = '''"a" "b"'''

    sql_text = ''' ctime:<"23/1/2016 13:32:33" '''
    sql_text = ''' a c atime:>="23123423" '''
    sql_text = '''   nocase: c   '''
    sql_text = '''  a sdf ctime:<"1/3/1980 1:13:22"  '''
    sql_text = '''"cd" ctime:>"3423d4"'''   # error
    sql_text = ''' a folder: a  size:>=34G '''
    sql_text = ''' a folder: d'''
    sql_text = ''' a folder: p:d'''
    a,b,c,d,e,f = format_sql_cmd(
        {
            'path': '/devpath/',
            'uuid': 'UUID',
            'sql_text': sql_text,
            'rowid_low': 1,
            'rowid_high': 2,
        }
    )
    print(a)
    print(b)
    print(c)
    print(d)
    print(e)
    print(f)
    # a      Like "%a%"
    # "a"     =  "a"
    # "a*b"  Like "a%b"

    # reg: "a*b"   REGEXP "a*b"