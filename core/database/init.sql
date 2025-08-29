/*
    用于新建数据的脚本
*/

-- 存储介质（如硬盘、磁带、TF卡等）
CREATE TABLE storages (
    id TEXT PRIMARY KEY,            -- 全局唯一识别码，以storage_开头
    name TEXT UNIQUE NOT NULL,      -- 存储介质的名称
    kind TEXT,                      -- 存储介质的类型，如硬盘、磁带、TF卡等
    add_time TEXT,                  -- 将该介质加入数据库的时间
    last_check_time TEXT,           -- 上次进行检查的时间
    state TEXT DEFAULT 'healthy',   --健康状态，有online，danger，error，等
    capacity INTEGER,               -- 存储介质的容量
    info TEXT DEFAULT ''            -- 一些其他信息
);

-- 卷与存储介质的映射关系
CREATE TABLE volume_structures (
    super_id TEXT,                  -- 卷的唯一识别码
    sub_id TEXT UNIQUE,             -- 存储卷的物理存储器的唯一识别码
    add_time TEXT,                  -- 加入的时间
    info TEXT DEFAULT '',           -- 构建的其他信息
    PRIMARY KEY (super_id, sub_id)  -- 主键由卷的唯一识别码和存储卷的唯一识别码组成
);

-- 卷（可独立使用的存储单元）
CREATE TABLE volumes (
    id INTEGER PRIMARY KEY,             -- 卷的唯一识别码,由volume_开头
    name TEXT UNIQUE NOT NULL,          -- 卷名称
    kind TEXT,                          -- 卷的类型，如单独，raid5等
    add_time TEXT,                      -- 卷的添加时间
    last_check_time TEXT,               -- 上次检查时间
    state TEXT DEFAULT 'healthy',       -- 卷的状态，可能的值有healthy, danger, offline等
    capacity INTEGER,                   -- 卷的容量
    info TEXT DEFAULT '',               -- 卷的其他信息
    unique_mount_point TEXT DEFAULT '', -- 卷在统一文件系统中显示的挂载点
    file_system TEXT DEFAULT ''         -- 卷的文件系统类型
);

-- 超卷与卷的映射关系
CREATE TABLE super_volume_structures (
    super_id TEXT,                  -- 超卷的唯一识别码
    sub_id TEXT UNIQUE,             -- 构成卷的唯一识别码
    add_time TEXT,                  -- 构建超卷的时间
    info TEXT DEFAULT '',           -- 构建的其他信息
    PRIMARY KEY (super_id, sub_id)  -- 主键由超卷的唯一识别码和构成卷的唯一识别码组成
);

-- 超卷（多个卷的集合，可嵌套），是进行校验的单元
CREATE TABLE super_volumes (
    id INTEGER PRIMARY KEY,         -- 超卷的唯一识别码,由super_volume_开头
    name TEXT UNIQUE NOT NULL,      -- 超卷名称
    kind TEXT,                      -- 超卷的类型，如raid5，等
    add_time TEXT,                  -- 超卷的添加时间
    last_check_time TEXT,           -- 上次对超卷的检查时间
    state TEXT DEFAULT 'healthy',   -- 超卷的状态，可能的值有healthy, danger, offline等
    capacity INTEGER,               -- 超卷的容量
    info TEXT DEFAULT ''            -- 超卷的其他信息

);

-- 文件元数据
CREATE TABLE files (
    md5 TEXT,                       -- 文件的MD5值
    size INTEGER,                   -- 文件的大小(以字节计)
    add_time TEXT,                  -- 文件添加到数据库的时间
    from_path TEXT,                 -- 文件的原始路径
    now_path TEXT UNIQUE,           -- 文件当前的路径(以volume的根节点开始)
    now_volume TEXT,                -- 文件当前所在的卷
    now_name TEXT,                  -- 文件当前的名称(冗余信息)
    state TEXT DEFAULT 'online',    -- 文件的状态，主要是online，还有delete等
    info TEXT DEFAULT ''            -- 一些其他文件信息
);

-- 缓存文件元数据，用来存储缓存
CREATE TABLE cache (
    md5 TEXT,                       -- 文件的MD5值
    size INTEGER,                   -- 文件的大小(以字节计)
    now_path TEXT,                  -- 文件当前的路径(以cache的根节点开始)
    now_name TEXT,                  -- 文件当前的名称(冗余信息)
    last_visit_time TEXT,           -- 上次访问时间(用于LRU算法)
    last_modify_time TEXT,          -- 上次修改时间(用于LRU算法)
    add_time TEXT                   -- 文件添加到缓存的时间
);

-- 初始化一条默认存储介质、卷和超卷
INSERT INTO storages (id, name, kind, add_time, last_check_time, state, capacity, info)
VALUES ('00000000000000000000000000000000', 'default', 'disk', strftime('%s','now'), strftime('%s','now'), 'healthy', 0, '用于默认和缺省的类');

INSERT INTO volumes (id, name, kind, add_time, last_check_time, state, capacity, info)
VALUES (0, 'default', 'single', strftime('%s','now'), strftime('%s','now'), 'healthy', 0, '用于默认和缺省的类');

INSERT INTO super_volumes (id, name, kind, add_time, last_check_time, state, capacity, info)
VALUES (0, 'default', 'single', strftime('%s','now'), strftime('%s','now'), 'healthy', 0, '用于默认和缺省的类');
