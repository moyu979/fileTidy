CREATE TABLE files(
    Md5 TEXT,
    size TEXT,
    addTime TEXT,
    fromPath TEXT,
    nowPath TEXT,
    nowName TEXT,
    storageVirtual INTEGER DEFAULT 0,
    state TEXT DEFAULT 'healthy',
    info TEXT DEFAULT NULL
);

CREATE TABLE cache(
    Md5 TEXT,
    nowPath TEXT,
    nowName TEXT,
)

CREATE TABLE Volume(
    id INTEGER PRIMARY KEY,
    addTime TEXT,
    lastCheck TEXT,
    volumeName TEXT UNIQUE NOT NULL,
    healthy TEXT DEFAULT 'healthy',
    info TEXT DEFAULT NULL,
    needAll INTEGER DEFAULT 1,
    used Text DEFAULT 0,
    capacity Text DEFAULT 0,
);

CREATE TABLE Disk(
    id INTEGER PRIMARY KEY,
    addTime TEXT,
    lastCheck TEXT,
    diskName TEXT,
    healthy TEXT DEFAULT 'health',
    capacity TEXT,
    kind TEXT,
    info TEXT DEFAULT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE storageStructure(
    superid INTEGER,
    subid INTEGER,
    addTime TEXT,
    info TEXT DEFAULT NULL,
    PRIMARY KEY (superid,subid)
);

INSERT INTO physicalStorage (id,addTime,lastCheck,diskName,diskID,capacity) VALUES (0,'0000-00-00 00:00','0000-00-00 00:00','referToAllDisk','0000000000000000',0);
INSERT INTO virtualStorage (id,addTime,lastCheck,volumeName)  VALUES (0,'0000-00-00 00:00','0000-00-00 00:00','referToDownloadVolumn');
INSERT INTO storageStructure VALUES (0,0,'0000-00-00 00:00','addByInitProcess');