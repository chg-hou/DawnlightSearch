__This page is under construction...__
__some parts are out of date__

# DawnlightSearch

A Linux version of [Everything Search Engine](https://www.voidtools.com/). Support **NTFS indexing**. Show instant results as you type.

__The app is still under development and not stable. Comments and pull requests are very appreciated.__

[![Build Status](https://travis-ci.org/chg-hou/DawnlightSearch.svg?branch=c%2B%2B-version)](https://travis-ci.org/chg-hou/DawnlightSearch)
         
<details>
  <summary>
   <a href="https://hosted.weblate.org/projects/dawnlightsearch/translations/">
      <img src="https://hosted.weblate.org/widgets/dawnlightsearch/-/translations/svg-badge.svg" alt="Translation status" >
   </a>
 </summary> 
 <img src="https://hosted.weblate.org/widgets/dawnlightsearch/-/translations/multi-auto.svg"  alt="Translation status"  >  
</details>

## Similar Everything-like Search Engine in Linux: 

(Ordered by first commit date)

| Name | Language | GUI | Database | 
|-|-|-|-|
|[ANGRYsearch](https://github.com/DoTheEvo/ANGRYsearch) | Python3 | PyQt5 | SQLite3 |
|[fsearch](https://github.com/cboxdoerfer/fsearch) | C | GTK+3 | (built-in) |
|[DawnlightSearch (old)](https://github.com/chg-hou/DawnlightSearch/tree/master) | Python3 | PyQt5 | SQLite3 |
|[DawnlightSearch (this)](https://github.com/chg-hou/DawnlightSearch) | C++ | Qt5 | SQLite3 |


## Test environment:

 - Ubuntu 16.04 / 18.04

## Highlights:

 - Instant search.
 - Support **wildcards** and **regular expressions**.
 - Support filter on multi fileds: file name, folder, full path, size, mtime, ctime, and atime. 
  - Quick file indexing for NTFS partition by parsing master file table (MFT).
  - Customizable **dock widget** design.
  - **Multi-threaded** search. 
  - **Drag&drop** search results. (v0.1.2.2)
  
## Video demo:

[https://youtu.be/949Jm9j4sP4](https://youtu.be/949Jm9j4sP4)

![](./_screenshot/Dawnlight%20Search_c++.png)

![](./_screenshot/Dawnlight%20Search_2.png)

--------------------------------

### Interface:

#### Database:

Partitions of differenct UUIDs will be stored seperatedly in the database. In circumstances where duplicate UUIDs exist, they will be treated as a single one and records will be overwritten. 

![](./_screenshot/Database_table_1.png)

1. Whether search this partition. **You need to check it to search the corresponding partition.** Icon indicates the mount state.

2. Can be changed into any name you want. Will display in front of the path when partition unmounted.

3. Whether update this partition when “*Update DB*” clicked. You can always update a partition using the context menu, regardless of the checked state.


#### Menubar:

![](./_screenshot/Main_menu.png)

1. Edit excluded paths when indexing. Only full path is supported right now. Note: MFT parser will disregard this option.

2. Check this option to use MFT parser to speed up building index on an NTFS partition (like other MFT based searcher). 

3. Check to use the C++ MFT parser instead of the Python one. The C++ one is supposed to be much faster.


#### Search Syntax:


  Logical Operators   |  Description 
-------- | ---
&#160;  *space* | AND
 &#124; *vertical bar*   | OR
!   *exclamation mark* | NOT


  Wildcards   |  Description 
-------- | ---
&#160;  *space* | AND
 &#124; *vertical bar*   | OR
!   *exclamation mark* | NOT



Note: global "nocase" settings DOES have effect on regular expression.  
Examples: 

<span style="color:red"> ***reg:"a"*** </span> will match "123abcd". Will also match "123Abcd" if case-insensitive. 



### Installation:

|||
|-|-|
|From Source| [https://github.com/chg-hou/DawnlightSearch/wiki/Build-from-source](https://github.com/chg-hou/DawnlightSearch/wiki/Build-from-source)|
|AppImage|([https://github.com/chg-hou/DawnlightSearch/releases](https://github.com/chg-hou/DawnlightSearch/releases))|
|Snaps|(under review)|
|Flatpak|(fail to work)|


 - Qt5

 - kio-dev
 
### TODO:
 - Auto indexing.
 - Monitor file system changes.
 - Index files in archives.
 - More language options.
 - Support Windows.

### FIXME:


