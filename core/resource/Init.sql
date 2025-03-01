CREATE TABLE files(
    -- 文件的元信息
    /*
    文件的自身性质
    md5：文件的哈希值
    size：文件的大小（字节）
    state:文件的状态
        healthy:正常，健康的文件
    info：文件的一些注释
    */
    md5 TEXT,
    size TEXT,
    state TEXT DEFAULT 'healthy',
    info TEXT DEFAULT '',
    /*
    文件的来源信息
    addTime：文件被记录入数据库的时间
    fromPath：文件被记录入数据库中的路径
    */
    addTime TEXT, 
    fromPath TEXT,
    /*
    文件的存储信息
    Volume：文件现在位于的卷
    storagePath：文件在卷中的位置（省略最上层的datas）
    */
    volume TEXT DEFAULT 0,
    storagePath TEXT UNIQUE,
    /*
    文件的展示信息
    showPath：文件被认为存在的位置
    */
    showPath TEXT
);

CREATE TABLE cache(
    -- 文件的缓存信息，用于控制文件是否被缓存到长期在线的存储池
    /*
    md5：文件的哈希摘要
    cache：文件的缓存位置
    */
    md5 TEXT,
    cachePath TEXT
);

CREATE TABLE volume(
    -- 卷的元信息，卷指可以用来单独存储数据的存储单元
    id TEXT UNIQUE,     -- 卷的id
    addTime TEXT,       -- 卷的登记时间
    lastCheck TEXT,     -- 上次对卷进行检查的时间
    volumeName TEXT,    -- 卷的助记名

    /*
    healthy：卷的健康情况
        health：健康的卷
        degraded：存在冗余缺失的卷
        error：已经有错误的卷
        broken：已经不用的卷
    */
    healthy TEXT DEFAULT 'healthy', 

    info TEXT DEFAULT '',       -- 卷的额外标记信息
    needAll TEXT DEFAULT 1,     -- 是否需要全部子卷才能使用,0:否，1：是，2：只有一个
    used Text DEFAULT 0,        -- 已经使用的容量
    capacity Text DEFAULT 0,    -- 卷的总容量

    /*
    卷的类型
        singleDisk：建立在单独磁盘上的卷
        01：
        NULL：临时占位符
    */
    kind TEXT, 

    /*
    卷的格式化信息
        ltfs
        ntfs
        exfat
        zfs
            zfs-raid-z1
        NULL：临时占位符
    */
    format TEXT,

    /*
    卷是否可以独立使用
    -1：需要其他卷
    0：正好是最基础的使用单位
    1：它由若干个可以独立使用的子卷拼接而成
    */
    isBase TEXT DEFAULT 'false',

    globalPoint TEXT DEFAULT 'unknown'  -- 卷的/data目录被认为挂载在哪里
);

CREATE TABLE device(
    --  存储设备的元信息
    id TEXT PRIMARY KEY,    -- 存储设备自带的唯一id，对于磁盘来说，一般为SN码，对于磁带来说，在add时可以自动生成一个
    addTime TEXT,           -- 存储设备被记录的时间
    lastCheck TEXT,         -- 存储设备上次运行的情况
    deviceName TEXT,        -- 存储设备的助记
    /*
    存储设备的健康情况
        health：健康的存储设备
        degraded：存在问题的设备，勉强使用
        error：已经有错误的卷，一般用作缓存
        broken：彻底坏掉的设备，不要用
    */
    healthy TEXT DEFAULT 'health',

    capacity TEXT,-- 存储设备的容量
    /*
    存储设备的种类
    磁盘：
        HDD2.5：2.5寸机械硬盘
        HDD3.5：3.5寸机械硬盘
        SSD2.5：2.5寸固态硬盘
        SSDNVME：NVME固态硬盘
        SSDNGFF：SATANGFF固态硬盘
        SSDPCIE：PCIE固态硬盘
    磁带：
        lto5
        lto6
    u盘：
        usb3.0：usb3u盘
        usb2.0：usb2u盘
    占位：
        NULL
    */
    kind TEXT DEFAULT 'NULL',

    info TEXT DEFAULT ''    -- 一些不好分类的信息
);

CREATE TABLE storageStructure(
    superid TEXT,   -- 构成的卷，会被记录在volume表格内
    subid TEXT,     -- 由哪些卷构成，往往是volume或device内的
    subdir TEXT,    -- 在子卷中，位于哪个文件夹，NULL意味着会以裸盘的形式使用整个卷
    addTime TEXT,   -- 什么时候标记的这个卷
    /*
    这条记录的信息
        inuse：有效
        notuse：无效
    */
    state TEXT DEFAULT 'inuse',

    info TEXT DEFAULT '',   -- 一些其他的卷信息
    PRIMARY KEY (superid,subid)
);

INSERT INTO device (id,addTime,lastCheck,deviceName,capacity) VALUES ('0','0000:00:00 00:00:00','0000:00:00 00:00:00','referToAllDisk','0');
INSERT INTO volume (id,addTime,lastCheck,volumeName)  VALUES ('0','0000-00-00 00:00','0000-00-00 00:00','referToDownloadVolumn');
INSERT INTO storageStructure VALUES ('0','0','./','0000:00:00 00:00:00','inuse','addByInitProcess');