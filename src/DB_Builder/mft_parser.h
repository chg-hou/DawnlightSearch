#ifndef MFT_PARSER_H
#define MFT_PARSER_H

#include <QObject>
#include <QString>
#include <QSqlQuery>
#include <QVariant>

#include <iostream>
#include <vector>
#include <fstream>
#include <stdlib.h>

#include <string>
#include <locale>
//#include <codecvt> // codecvt not included in g++ 4.8
#include <iomanip>
#include <assert.h>

namespace MFT_Parser_space {


#define RECORD_SIZE 1024
#define RECORD_BUFFER_SIZE 1024*2
//#include "mft_c_parser_module.h"

using namespace std;

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


struct MFT_RECORD{
    string name;
    DWORD par_ref;
    string path;
    DWORD size;
    ULONGLONG atime;
    ULONGLONG mtime;
    ULONGLONG ctime;
    bool isFolder;
} ; //tmp_record;



class MFTParser : public QObject
{
    Q_OBJECT

private:
    QSqlQuery * cur;
    std::string mft_filename;
public:
    explicit MFTParser(QObject *parent = nullptr);
    void write_to_sqlite_db(vector<MFT_RECORD> & mft);
    unsigned long long mft_c_parser_func(QString mft_filename_in,
                              QSqlQuery * cur);
signals:

public slots:
};



}// END space MFT_Parser_space

#endif // MFT_PARSER_H
