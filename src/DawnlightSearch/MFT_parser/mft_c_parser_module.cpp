#include <Python.h>

#include <iostream>
#include <vector>
#include <fstream>
#include <sqlite3.h>
#include <stdlib.h>

#include <string>
#include <locale>
#include <codecvt>
#include <iomanip>
#include <assert.h>

#define RECORD_SIZE 1024
#define RECORD_BUFFER_SIZE 1024*2
//#include "mft_c_parser_module.h"

using namespace std;
std::wstring_convert<std::codecvt_utf8_utf16<char16_t>, char16_t> cvt_u16string_to_string;

string db_filename;
string mft_filename;
string table_name;

//======================================mft_c_parser_module=============
typedef uint32_t       DWORD;       //4
typedef int                 BOOL;
typedef unsigned char       BYTE;
typedef unsigned short      WORD;   //2
typedef uint64_t ULONGLONG;         //8

typedef struct tagFILE_RECORD_HEADER
{
    // 0:4
        DWORD		Magic;			// "FILE"
        // 4:6
        WORD		OffsetOfUS;		// Offset of Update Sequence
        // 6:8
        WORD		SizeOfUS;		// Size in words of Update Sequence Number & Array
        // 8:16
        ULONGLONG	LSN;			// $LogFile Sequence Number
        // 16:18
        WORD		SeqNo;			// Sequence number
        // 18:20
        WORD		Hardlinks;		// Hard link count
        // 20:22
        WORD		OffsetOfAttr;	// Offset of the first Attribute
        // 22:24
        WORD		Flags;			// Flags
        // 24:28
        DWORD		RealSize;		// Real size of the FILE record
        // 28:32
        DWORD		AllocSize;		// Allocated size of the FILE record
        // 32:38
        ULONGLONG	RefToBase;		// File reference to the base FILE record
        WORD		NextAttrId;		// Next Attribute Id
        WORD		Align;			// Align to 4 byte boundary
        // 44:48
        DWORD		RecordNo;		// Number of this MFT Record
} FILE_RECORD_HEADER;

typedef struct tagFILE_RECORD_HEADER_2
{
    // 0:4
        DWORD		Magic;			// "FILE"
        // 4:6
        WORD		OffsetOfUS;		// Offset of Update Sequence
        // 6:8
        WORD		SizeOfUS;		// Size in words of Update Sequence Number & Array
        // 8:16
        ULONGLONG	LSN;			// $LogFile Sequence Number
        // 16:18
        WORD		SeqNo;			// Sequence number
        // 18:20
        WORD		Hardlinks;		// Hard link count
        // 20:22
        WORD		AttrOffset;	// Offset of the first Attribute
        // 22:24
        WORD		Flags;			// Flags
        // 24:28
        DWORD		RealSize;		// Real size of the FILE record
        // 28:32
        DWORD		AllocSize;		// Allocated size of the FILE record

        // 32:38  32:36
        DWORD	RefToBase;		// File reference to the base FILE record
    // 32:38  36:38
        WORD __padding;
        // 38:40
        WORD        BaseSeq;

        //  40:42
        WORD		NextAttrId;		// Next Attribute Id
        // 42:44    f1 padding
        WORD		Align;			// Align to 4 byte boundary
        // 44:48
        DWORD		RecordNo;		// Number of this MFT Record
        // 48:50
        WORD        SeqNumber;
} MFT_RECORD_HEADER;

typedef	struct tagATTR_HEADER_COMMON
{
        DWORD		Type;			//0:4// Attribute Type
        DWORD		TotalSize;		//4:8// Length (including this header)
        BYTE		NonResident;	//8// 0 - resident, 1 - non resident
        BYTE		NameLength;		//9// name length in words
        WORD		NameOffset;		//10:12// offset to the name
        WORD		Flags;			//12:14// Flags
        WORD		Id;				//14:16// Attribute Id
} ATTR_HEADER_COMMON;
// tagATTR_HEADER_COMMON + 16 offset, NonResident==0;
typedef	struct tagATTR_HEADER_RESIDENT
{
        ATTR_HEADER_COMMON	Header;			// Common data structure
        DWORD				AttrSize;		// Length of the attribute body
        WORD				AttrOffset;		// Offset to the Attribute
        BYTE				IndexedFlag;	// Indexed flag
        BYTE				Padding;		// Padding
} ATTR_HEADER_RESIDENT;
// tagATTR_HEADER_COMMON + 16 offset, NonResident!=0;
typedef struct tagATTR_HEADER_NON_RESIDENT
{
        ATTR_HEADER_COMMON	Header;			// Common data structure
        ULONGLONG			StartVCN;		// Starting VCN
        ULONGLONG			LastVCN;		// Last VCN
        WORD				DataRunOffset;	// Offset to the Data Runs
        WORD				CompUnitSize;	// Compression unit size
        DWORD				Padding;		// Padding
        ULONGLONG			AllocSize;		// Allocated size of the attribute
        ULONGLONG			RealSize;		// Real size of the attribute
        ULONGLONG			IniSize;		// Initialized data size of the stream
} ATTR_HEADER_NON_RESIDENT;

typedef struct tagATTR_STANDARD_INFORMATION
{
        ULONGLONG	CreateTime;		// File creation time
        ULONGLONG	AlterTime;		// File altered time
        ULONGLONG	MFTTime;		// MFT changed time
        ULONGLONG	ReadTime;		// File read time
        DWORD		Permission;		// Dos file permission
        DWORD		MaxVersionNo;	// Maxim number of file versions
        DWORD		VersionNo;		// File version number
        DWORD		ClassId;		// Class Id
        DWORD		OwnerId;		// Owner Id
        DWORD		SecurityId;		// Security Id
        ULONGLONG	QuotaCharged;	// Quota charged
        ULONGLONG	USN;			// USN Journel
} ATTR_STANDARD_INFORMATION;

typedef struct tagATTR_FILE_NAME
{
        //ULONGLONG	ParentRef;		// File reference to the parent directory
        DWORD	    ParentRef;		// File reference to the parent directory
        WORD        __padding;
        WORD	    ParentSeq;		// File reference to the parent directory

        ULONGLONG	CreateTime;		// File creation time
        ULONGLONG	AlterTime;		// File altered time
        ULONGLONG	MFTTime;		// MFT changed time
        ULONGLONG	ReadTime;		// File read time
        ULONGLONG	AllocSize;		// Allocated size of the file
        ULONGLONG	RealSize;		// Real size of the file
        DWORD		Flags;			// Flags
        DWORD		ER;				// Used by EAs and Reparse
        BYTE		NameLength;		// Filename length in characters
        BYTE		NameSpace;		// Filename space
        WORD		Name[1];		// Filename
} ATTR_FILE_NAME;
//=======END=================mft_c_parser_module========END=====



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

struct MFT_RECORD{
    string name;
    DWORD par_ref;
    string path;
    DWORD size;
    ULONGLONG atime;
    ULONGLONG mtime;
    ULONGLONG ctime;
    bool isFolder;
} tmp_record;
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
static int callback(void *NotUsed, int argc, char **argv, char **azColName){
    int i;
    for(i=0; i<argc; i++){
        printf("%s = %s\n", azColName[i], argv[i] ? argv[i] : "NULL");
    }
    printf("\n");
    return 0;
}

void write_to_sqlite_db(vector<MFT_RECORD> & mft)
{
    sqlite3 *db;
    int  rc;
    string sql_creat_table;
    char *zErrMsg = 0;

    /* Open database */
    rc = sqlite3_open(db_filename.c_str(), &db);
    if( rc ){
        fprintf(stderr, "Can't open database: %s\n", sqlite3_errmsg(db));
        exit(0);
    }else{
        fprintf(stdout, "Opened database successfully\n");
    }

    /* Create SQL statement */

    sql_creat_table = "CREATE TABLE '" + table_name + "' ("\
                                                      "`file_id` INTEGER,"\
                                                      "`Filename`	TEXT,"\
                                                      "`Path`	TEXT,"\
                                                      "`Size`	INTEGER,"\
                                                      "`IsFolder`	BLOB,"\
                                                      "`atime`	INTEGER,"\
                                                      "`mtime`	INTEGER,"\
                                                      "`ctime`	INTEGER,"\
                                                      "PRIMARY KEY(`file_id`));";

    cout <<sql_creat_table<<endl;

    /* Execute SQL statement */
    rc = sqlite3_exec(db, sql_creat_table.c_str(), callback, 0, &zErrMsg);

    if( rc != SQLITE_OK ){
        fprintf(stderr, "SQL error: %s\n", zErrMsg);
        sqlite3_free(zErrMsg);
    }else{
        fprintf(stdout, "Table created successfully\n");
    }
    cout << "Begin insert..."<<endl;
    sqlite3_exec(db, "BEGIN;", 0, 0, 0);

    char *sql = NULL;
    for (DWORD i =0; i< mft.size();i++){
        if (mft[i].par_ref == 0)
            continue;
        sql = sqlite3_mprintf("insert into `%s` (`Filename`,`Path`,`Size`,`IsFolder`,`atime`,`mtime`,`ctime`)" \
                              "          values ('%q',      '%q'  , %d   , %d       , %d    , %d    ,  %d   );",
                              table_name.c_str(), mft[i].name.c_str(), mft[i].path.c_str(),
                              mft[i].size, mft[i].isFolder, mft[i].atime, mft[i].mtime, mft[i].ctime );
        /*
                sql = sqlite3_mprintf("insert into `%s` (`Filename`,`Path`,`Size`,`IsFolder`,`atime`,`mtime`,`ctime`)" \
                                      "          values ('%q',      '%q'  , %s   , %s       , %s    , %s    ,  %s   );",
                                      table_name.c_str(), mft[i].name.c_str(), mft[i].path.c_str(),
                                       mft[i].size, mft[i].isFolder, mft[i].atime, mft[i].mtime, mft[i].ctime );
         cout<<sql<<endl;*/
        sqlite3_exec(db, sql, 0, 0, 0);

        sqlite3_free(sql);

    }
    sqlite3_exec(db, "COMMIT;", 0, 0, 0);
    cout<<"COMMIT"<<endl;
    sqlite3_close(db);
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

/*  wrapped c_parser function */
static PyObject* mft_c_parser_func(PyObject* self, PyObject* args)
{

    char* arg1;
    char* arg2;
    char* arg3;
    string out_str("");
    /*  parse the input, from python float to c double */
    if (!PyArg_ParseTuple(args, "sss", &arg1, &arg2, &arg3))
    {
        out_str = "Fail to parser args.";
        cout<<string(arg1)<<endl;
        cout<<string(arg2)<<endl;
        cout<<string(arg3)<<endl;
        return Py_BuildValue("s", out_str.c_str());
    }

    mft_filename = string(arg1);
    db_filename  = string(arg2);
    table_name   = string(arg3);

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
    cout<<"end"<<endl;

    out_str = "Done.";
    return Py_BuildValue("s", out_str.c_str());
}

/*  define functions in module */
static PyMethodDef MFTParserMethods[] =
{
     {"mft_c_parser_func", mft_c_parser_func, METH_VARARGS, "parser $MFT file"},
     {NULL, NULL, 0, NULL}
};



/* module initialization */
#if PY_MAJOR_VERSION >= 3
//   https://docs.python.org/3.4/c-api/module.html
static struct PyModuleDef moduledef = {

        PyModuleDef_HEAD_INIT,
        "mft_c_parser_module",
        "parser $MFT file",             //char* m_doc Docstring for the module;
        -1,                             // -1 ? 0 ?
        MFTParserMethods,
        NULL,
        NULL,
        NULL,
        NULL
};

#define INITERROR return NULL

PyMODINIT_FUNC
PyInit_mft_c_parser_module(void)

#else
#define INITERROR return

void
initmft_c_parser_module(void)
#endif
{
#if PY_MAJOR_VERSION >= 3
    PyObject *module = PyModule_Create(&moduledef);
#else
    PyObject *module = Py_InitModule("mft_c_parser_module", MFTParserMethods);
#endif

//    if (module == NULL)
//        INITERROR;
//    struct module_state *st = GETSTATE(module);

//    st->error = PyErr_NewException("mft_c_parser_module.Error", NULL, NULL);
//    if (st->error == NULL) {
//        Py_DECREF(module);
//        INITERROR;
//    }

#if PY_MAJOR_VERSION >= 3
    return module;
#endif
}
