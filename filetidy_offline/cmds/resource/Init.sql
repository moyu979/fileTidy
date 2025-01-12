CREATE TABLE files(
    md5 TEXT,
    size TEXT,
    addTime TEXT,
    fromPath TEXT,
    nowPath TEXT UNIQUE,
    nowName TEXT,
    storage TEXT DEFAULT 0,
    state TEXT DEFAULT 'healthy',
    info TEXT DEFAULT ''
);

CREATE TABLE cache(
    md5 TEXT,
    nowPath TEXT,
    nowName TEXT
);

CREATE TABLE Volume(
    id TEXT UNIQUE,
    addTime TEXT,
    lastCheck TEXT,
    volumeName TEXT UNIQUE NOT NULL,
    healthy TEXT DEFAULT 'healthy',
    info TEXT DEFAULT '',
    needAll TEXT DEFAULT 1,
    used Text DEFAULT 0,
    capacity Text DEFAULT 0,
    kind TEXT
);

CREATE TABLE PhysicalStorage(
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
    subid TEXT,
    addTime TEXT,
    info TEXT DEFAULT '',
    state TEXT DEFAULT 'inuse',
    PRIMARY KEY (superid,subid)
);

INSERT INTO PhysicalStorage (id,addTime,lastCheck,diskName,capacity,kind) VALUES ('0','0000:00:00 00:00:00','0000:00:00 00:00:00','referToAllDisk','0','0');
INSERT INTO Volume (id,addTime,lastCheck,volumeName)  VALUES ('0','0000-00-00 00:00','0000-00-00 00:00','referToDownloadVolumn');
INSERT INTO storageStructure VALUES ('0','0','0000:00:00 00:00:00','addByInitProcess','inuse');