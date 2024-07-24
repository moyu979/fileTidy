CREATE TABLE files(
    Md5 TEXT,
    addTime TEXT,
    fromPath TEXT,
    nowPath TEXT,
    nowName TEXT,
    storageVirtual INTEGER DEFAULT 0,
    storagePhysical INTEGER DEFAULT 0
);

CREATE TABLE virtualStorage(
    id INTEGER PRIMARY KEY,
    addTime TEXT,
    lastCheck TEXT,
    volumeName TEXT UNIQUE NOT NULL,
    needAll INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE physicalStorage(
    id INTEGER PRIMARY KEY,
    addTime TEXT,
    lastCheck TEXT,
    diskName TEXT UNIQUE NOT NULL
);

CREATE TABLE storageStructure(
    superid INTEGER,
    subid INTEGER,
    addTime TEXT,
    explaination TEXT DEFAULT NULL,
    PRIMARY KEY (superid,subid)
);

INSERT INTO physicalStorage VALUES (0,'0000-00-00 00:00','0000-00-00 00:00','referToAllDisk');
INSERT INTO virtualStorage VALUES (0,'0000-00-00 00:00','0000-00-00 00:00','referToDownloadVolumn');
INSERT INTO storageStructure VALUES (0,0,'0000-00-00 00:00',1,'addByInitProcess');