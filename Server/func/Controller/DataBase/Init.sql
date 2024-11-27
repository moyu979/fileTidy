CREATE TABLE files(
    Md5 TEXT,
    size TEXT,
    addTime TEXT,
    fromPath TEXT,
    nowPath TEXT UNIQUE,
    nowName TEXT,
    storageVirtual INTEGER DEFAULT 0,
    state TEXT DEFAULT 'healthy',
    info TEXT DEFAULT ''
);

CREATE TABLE cache(
    Md5 TEXT,
    nowPath TEXT,
    nowName TEXT
);

CREATE TABLE Volume(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    addTime TEXT,
    lastCheck TEXT,
    volumeName TEXT UNIQUE NOT NULL,
    healthy TEXT DEFAULT 'healthy',
    info TEXT DEFAULT '',
    needAll INTEGER DEFAULT 1,
    used Text DEFAULT 0,
    capacity Text DEFAULT 0
);

CREATE TABLE Disk(
    id TEXT PRIMARY KEY,
    addTime TEXT,
    lastCheck TEXT,
    diskName TEXT,
    healthy TEXT DEFAULT 'health',
    capacity TEXT,
    kind TEXT,
    info TEXT DEFAULT ''
);

CREATE TABLE storageStructure(
    superid TEXT,
    subid TEXT UNIQUE,
    addTime TEXT,
    info TEXT DEFAULT '',
    PRIMARY KEY (superid,subid)
);

INSERT INTO Disk (id,addTime,lastCheck,diskName,capacity,kind) VALUES ('0','0000-00-00 00:00','0000-00-00 00:00','referToAllDisk','0','0');
INSERT INTO Volume (id,addTime,lastCheck,volumeName)  VALUES ('0','0000-00-00 00:00','0000-00-00 00:00','referToDownloadVolumn');
INSERT INTO storageStructure VALUES ('0','0','0000-00-00 00:00','addByInitProcess');