/* 
硬件信息，主要指代一个磁盘/usb存储设备/磁带的基本信息，是物理设备的基本单位 
*/
CREATE TABLE Storage(
    id TEXT PRIMARY KEY,
    name TEXT,
    kind TEXT,
    capacity TEXT,

    addTime TEXT,
    lastCheck TEXT,
    
    healthy TEXT DEFAULT 'health',
    
    info TEXT DEFAULT ''
);
/* 
卷信息：一个虚拟存储的基本单位，可以说分区，raid，或者是手动维护的一个若干分区组成的集群
 */
CREATE TABLE Volume(
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    capacity Text DEFAULT 0,

    addTime TEXT,

    lastCheck TEXT,
    healthy TEXT DEFAULT 'healthy',

    info TEXT DEFAULT '',

    needAll INTEGER DEFAULT 1,
);
/*
存储结构信息：一个卷下面的一个文件夹/分区/raid等的基本信息
*/



CREATE TABLE storageStructure(
    superid TEXT,
    subid TEXT UNIQUE,
    addTime TEXT,
    info TEXT DEFAULT '',
    PRIMARY KEY (superid,subid)
);

CREATE TABLE fileSource(
    Md5 TEXT,
    size TEXT,
    add_time TEXT,
    fromPath TEXT
);
CREATE TABLE File(
    md5 TEXT,
    size TEXT,
    add_time TEXT,
    from_path TEXT,
    now_path TEXT UNIQUE,
    now_name TEXT,
    volume INTEGER DEFAULT 0,
    state TEXT DEFAULT 'healthy',
    info TEXT DEFAULT ''
);



CREATE TABLE cache(
    Md5 TEXT,
    nowPath TEXT,
    nowName TEXT
);

INSERT INTO Storage (id,addTime,lastCheck,name,capacity,kind) VALUES ('0','0000-00-00 00:00','0000-00-00 00:00','referToAllDisk','0','0');
INSERT INTO Volume (id,addTime,lastCheck,name)  VALUES ('0','0000-00-00 00:00','0000-00-00 00:00','referToDownloadVolumn');
INSERT INTO storageStructure VALUES ('0','0','0000-00-00 00:00','addByInitProcess');