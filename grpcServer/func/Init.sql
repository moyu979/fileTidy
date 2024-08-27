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

CREATE TABLE virtualStorage(
    id INTEGER PRIMARY KEY,
    addTime TEXT,
    lastCheck TEXT,
    volumeName TEXT UNIQUE NOT NULL,
    healthy TEXT DEFAULT 'healthy',
    info TEXT DEFAULT NULL,
    needAll INTEGER DEFAULT 1
);

CREATE TABLE physicalStorage(
    id INTEGER PRIMARY KEY,
    addTime TEXT,
    lastCheck TEXT,
    mode TEXT DEFAULT 'others',
    diskName TEXT UNIQUE,
    healthy TEXT DEFAULT 'health',
    capacity TEXT,
    info TEXT DEFAULT NULL,
    diskID TEXT UNIQUE
    
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