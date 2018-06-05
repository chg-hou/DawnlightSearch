#include "mft_parser.h"

using namespace MFT_Parser_space;


union
{
    char*		cBuffer;
    MFT_RECORD_HEADER*	mftHeader;
} myUnion;
union
{
    char*		cBuffer;
    ATTR_HEADER_COMMON*	    attrHeader;
    ATTR_HEADER_RESIDENT*       attrRes;
    ATTR_HEADER_NON_RESIDENT*   attrNonRes;
} attrUnion;
union
{
    char*		cBuffer;
    ATTR_FILE_NAME*	    FN;
} attrUnion_FN;

std::wstring_convert<std::codecvt_utf8_utf16<char16_t>, char16_t> cvt_u16string_to_string;

string get_path(vector<MFT_RECORD> & mft,DWORD seqnum)
{
    if (!(mft[seqnum].path.empty()))
    {
        if (mft[seqnum].path == "/")
            return mft[seqnum].path + mft[seqnum].name;
        else
            return mft[seqnum].path + "/" + mft[seqnum].name;
    }
    if (mft[seqnum].par_ref == 5)
    {
        mft[seqnum].path = "/";
        return "/" + mft[seqnum].name ;
    }
    if (mft[seqnum].par_ref == seqnum)
    {
        mft[seqnum].path = "/ORPHAN";
        return mft[seqnum].path + "/" + mft[seqnum].name;
    }
    string parentpath = get_path(mft, mft[seqnum].par_ref);
    mft[seqnum].path = parentpath;
    if (mft[seqnum].path == "/")
        return mft[seqnum].path + mft[seqnum].name;
    else
        return mft[seqnum].path + "/" + mft[seqnum].name;

}

void build_path(vector<MFT_RECORD> & mft)
{
    for (DWORD seqnum =0; seqnum< mft.size();seqnum++){
        get_path(mft, seqnum); //mft[seqnum].path =
    }
}

void print_mft(vector<MFT_RECORD> & mft)
{
    for (DWORD i =0; i< mft.size();i++){
        if (i>7) break;
        cout<<i<<"\t"<< (mft[i].name.empty())<<"\t"
           <<mft[i].par_ref<<"\t"
          << (mft[i].path)
          <<"\t"<< (mft[i].path.empty())
         <<"\t"<< (mft[i].atime)
        <<"\t"<< (mft[i].isFolder)
        <<"\t"<<mft[i].name
        <<endl;
    }
}


MFTParser::MFTParser(QObject *parent) : QObject(parent)
{

}

void MFTParser::write_to_sqlite_db(vector<MFT_RECORD> &mft)
{

    string sql_creat_table;



    for (DWORD i =0; i< mft.size();i++){
        if (mft[i].par_ref == 0)
            continue;

         /*
        sql = sqlite3_mprintf("insert into `%s` (`Filename`,`Path`,`Size`,`IsFolder`,`atime`,`mtime`,`ctime`)" \
                              "          values ('%q',      '%q'  , %d   , %d       , %d    , %d    ,  %d   );",
                              table_name.c_str(), mft[i].name.c_str(), mft[i].path.c_str(),
                              mft[i].size, mft[i].isFolder, mft[i].atime, mft[i].mtime, mft[i].ctime );

                sql = sqlite3_mprintf("insert into `%s` (`Filename`,`Path`,`Size`,`IsFolder`,`atime`,`mtime`,`ctime`)" \
                                      "          values ('%q',      '%q'  , %s   , %s       , %s    , %s    ,  %s   );",
                                      table_name.c_str(), mft[i].name.c_str(), mft[i].path.c_str(),
                                       mft[i].size, mft[i].isFolder, mft[i].atime, mft[i].mtime, mft[i].ctime );
         cout<<sql<<endl;*/

        // Note: sql has already been prepared in "inser_db_thread":
        /*
            cur.prepare(QString("insert into `%1` (`Filename`,`Path`,`Size`,`IsFolder`, "
                          "   `atime`,`mtime`,`ctime`) "
                          "values (?,  ?,  ?, ?, ?, ?, ?)").arg(table_name));

         */
        cur->bindValue(0, QString(mft[i].name.c_str()));
        cur->bindValue(1, QString(mft[i].path.c_str()));
        cur->bindValue(2, QVariant(mft[i].size));
        cur->bindValue(3, QVariant(mft[i].isFolder));
        cur->bindValue(4, QVariant((unsigned long long) mft[i].atime));
        cur->bindValue(5, QVariant((unsigned long long) mft[i].mtime));
        cur->bindValue(6, QVariant((unsigned long long) mft[i].ctime));
        cur->exec();

    }

    // TODO: excluded folder in mft parser

    // TODO: ? commit here
}

unsigned long long MFTParser::mft_c_parser_func(QString mft_filename_in, QSqlQuery * cur_in )
{
    cur = cur_in;
    mft_filename = mft_filename_in.toStdString();

    long length;

    ifstream is;
    is.open(mft_filename, ios::binary|ios::in);

    is.seekg(0, ios::end);
    length = is.tellg();
    is.seekg(0, ios::beg);

    cout<<"Length: "<<length<<endl;

    DWORD mft_size = length / 1024;
    vector<MFT_RECORD> mft;
    mft.resize(mft_size);

    myUnion.cBuffer = new char[RECORD_BUFFER_SIZE];

    for(DWORD seqno=0; ; seqno++)
    {

        is.read(myUnion.cBuffer, RECORD_SIZE);
        if (is.eof())
            break;
        //        cout<<"\n-------"<<myUnion.mftHeader->RecordNo<<" "<<seqno<<endl;  //#debugaa
        if (myUnion.mftHeader->RecordNo==0 && seqno>0)  continue;
        if (!(myUnion.mftHeader->Flags & 0x0001))   //deleted
            continue;
        //        assert(myUnion.mftHeader->RecordNo == seqno);


        //        cout <<"RecordNo:\t"<< myUnion.mftHeader->RecordNo << endl;
        //        cout <<"Magic:\t\t"<< myUnion.mftHeader->Magic << endl;
        //        cout <<"SeqNo:\t\t"<< myUnion.mftHeader->SeqNo<< endl;
        //        cout <<"AttrOffset:\t"<< myUnion.mftHeader->AttrOffset<< endl;
        //        cout <<"Flags:\t\t"<< myUnion.mftHeader->Flags<< endl;
        //        cout <<"RealSize:\t"<< myUnion.mftHeader->RealSize<< endl;
        //        cout<<"SeqNo:\t\t" << myUnion.mftHeader->SeqNo << endl;
        //        cout<<"AllocSize:\t" << myUnion.mftHeader->AllocSize << endl;
        //        cout<<"RefToBase:\t"<< myUnion.mftHeader->RefToBase << endl;
        //        cout<<"BaseSeq:\t"<< myUnion.mftHeader->BaseSeq << endl;
        //        cout<<"NextAttrId:\t"<< myUnion.mftHeader->NextAttrId << endl;
        //        cout <<"Align:\t\t" << myUnion.mftHeader->Align << endl;
        //        cout <<"SeqNumber:\t"<< myUnion.mftHeader->SeqNumber << endl;

        uint32_t read_ptr = myUnion.mftHeader->AttrOffset;
        string atrrecord_name = "";



        //int fncnt = 0;
        vector<ATTR_FILE_NAME> FN_vector;
        vector<string> FN_NAME_vector;
        while(read_ptr<1024)
        {
            attrUnion.cBuffer = myUnion.cBuffer + read_ptr;

            //            cout<<"====Attr==="<<endl;
            //            cout <<"\tType:\t\t"<< attrUnion.attrHeader->Type << endl;
            //            cout <<"\tTotalSize:\t"<< attrUnion.attrHeader->TotalSize << endl;
            //            cout <<"\tNonResident:\t"<< int(attrUnion.attrHeader->NonResident ) << endl;
            //            cout <<"\tNameLength:\t"<< int(attrUnion.attrHeader->NameLength) << endl;
            //            cout <<"\tNameOffset:\t"<< attrUnion.attrHeader->NameOffset << endl;
            //            cout <<"\tFlags:\t\t"<< attrUnion.attrHeader->Flags << endl;
            //            cout <<"\tId:\t\t"<< attrUnion.attrHeader->Id << endl;

            if (attrUnion.attrHeader->Type == 0xffffffff) // End of attributes
                break;
            if (attrUnion.attrHeader->NameLength > 0)
            {
                //                uint32_t name_offset = attrUnion.attrHeader->NameOffset;
                //                uint32_t bufLen = attrUnion.attrHeader->NameLength;
                //                wchar_t *nameBuf;
                //                nameBuf = new wchar_t[bufLen * 2];
                //                wchar_t *namePtr = (wchar_t*)((BYTE*)attrUnion.attrHeader + name_offset);
                //                wcsncpy(nameBuf, namePtr, bufLen);
                //                nameBuf[bufLen] = '\0\0';
                //                cout<<endl<<nameBuf<<endl;
                //                delete [] nameBuf;
            }


            if (attrUnion.attrHeader->Type ==0x10 )     //Standard Information
            {
                // attrUnion_SI.cBuffer = myUnion.cBuffer + read_ptr + attrUnion.attrRes->AttrOffset;
                // cout <<"\tStandard Information: CreateTime:\t\t"<< attrUnion_SI.attrHeader->CreateTime << endl;
            }
            if (attrUnion.attrHeader->Type ==0x30 )     //File name
            {
                attrUnion_FN.cBuffer = myUnion.cBuffer + read_ptr + attrUnion.attrRes->AttrOffset;
                FN_vector.push_back(*(attrUnion_FN.FN));

                uint32_t name_length = attrUnion_FN.FN->NameLength;
                //uint32_t name_offset = attrUnion.attrHeader->NameOffset;
                //uint32_t bufLen = name_length + 1;

                //char16_t *nameBuf;
                //nameBuf = new char16_t[bufLen * 2];

                char16_t *namePtr = (char16_t*)((BYTE*)attrUnion_FN.FN->Name);
                //copy(namePtr, namePtr+name_length, nameBuf);
                //nameBuf[name_length] = '\0\0';
                // http://www.cs.ucr.edu/~cshelton/courses/cppsem/strex.cc
                //u16string u16_cvt_str =nameBuf;
                //                std::string u8_str = u8"ꚥ"; // utf-8
                //                std::u16string u16_str = u"ꚥ"; // utf-16
                //                std::u32string u32_str = U"ꚥ"; // ucs4

                u16string u16_cvt_str =basic_string<char16_t>(namePtr,name_length);
                //cout<<endl<<"Name: "<<nameBuf<<endl;
                //delete [] nameBuf;

                string u8_cvt_str = cvt_u16string_to_string.to_bytes(u16_cvt_str);
                //                cout<<endl<<"\t\t\t\tName: "<<u8_cvt_str<<endl;//#debugaa
                FN_NAME_vector.push_back(u8_cvt_str);
            }


            if (attrUnion.attrHeader->TotalSize > 0)
            {
                read_ptr += attrUnion.attrHeader->TotalSize;
            }
            else
            {
                break;
            }
        }
        //FILE mft_file = open
        //        myUnion.mftHeader->Magic;
        //        for(int i=0; i<RECORD_SIZE; i++)
        //            cout<<myUnion.cBuffer[i];
        //        cout<<"Total fn: "<<FN_vector.size()<<endl;//#debugaa

        DWORD _r_sn = myUnion.mftHeader->RecordNo;
        if (FN_vector.size()==1)
        {
            mft[_r_sn].name    = FN_NAME_vector[0];
            mft[_r_sn].par_ref = FN_vector[0].ParentRef;
        }
        if (FN_vector.size() > 1)
        {
            mft[_r_sn].par_ref = FN_vector[0].ParentRef;
            if (FN_vector[0].NameSpace == 0x1 || FN_vector[0].NameSpace == 0x3)
                mft[_r_sn].name    = FN_NAME_vector[0];
            if (FN_vector[FN_vector.size()-1].NameSpace == 0x1 || FN_vector[FN_vector.size()-1].NameSpace == 0x3)
                mft[_r_sn].name    = FN_NAME_vector[FN_vector.size()-1];
        }
        if (FN_vector.size() > 0)
        {

            mft[_r_sn].size =  FN_vector[0].AllocSize;
            // Windows NT time is specified as the number of 100 nanosecond intervals since January 1, 1601.
            // UNIX time is specified as the number of seconds since January 1, 1970.
            // There are 134,774 days (or 11,644,473,600 seconds) between these dates.
            mft[_r_sn].mtime =  FN_vector[0].AlterTime/10000000 - 11644473600;
            mft[_r_sn].ctime =  FN_vector[0].MFTTime/10000000 - 11644473600;
            mft[_r_sn].atime =  FN_vector[0].ReadTime/10000000 - 11644473600;
            mft[_r_sn].isFolder =  myUnion.mftHeader->Flags & 0x0002;


        }
    }

    delete [] myUnion.cBuffer;

    is.close();

    build_path(mft);
    print_mft(mft);

    write_to_sqlite_db(mft);


    return mft_size;
}


