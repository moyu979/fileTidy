# fileTidyScripts

这是一个个人用来管理自己的文件库的python小脚本合集，主要功能有：
1. 文件级去重
2. 文件移动追踪
3. 文件索引
##
完成情况

|name|condition|
|---|---|
|AFile.py|finished|
|FileList.py|finished|
|generateHash.py|finished|

## 工作流程
### 下载文件后
相关文件：

|名称|类型|
|---|---|
|afterdownload.py|file|
|downloads|dir|

运行 afterdownload.py 文件,参数为存放下载完成文件的位置。

新下载的文件会和“downloads”文件夹中的最新记录中的文件一同被写入名为“new.txt”的文本文件中，旧的“new.txt”会被以“<废弃日期>_in.txt”命名。

此时文件的哈希值将被计算，同时进行文件夹内部的第一轮去重。

### 解压/压缩文件
相关文件：

|名称|类型|
|---|---|
|unzip.py|file|
|zip.py|file|
|zip|dir|
|unzip|dir|

将对应的文件以文件夹的形式和解压出的文件置于同一个文件夹下，例如，“z1.zip”，“z2.zip”对应“z1”和“z2”两个文件夹，并将四个文件/文件夹放在同一个“dir”下，以dir为参数运行“unzip.py”或“zip.py”，可在“unzip”或“zip”文件夹下生成对应的目录表，在运行“move”时会自动合并入新的目录中。

此时会计算新生成文件的哈希值，表项与标准格式一致，但需注意的是file的originPath会填写为“xx.zip/xxx”的形式，***不可以作为标准的文件路径***，因此在后期的处理中要进行单独处理。

### 手动整理文件后
相关文件：

|名称|类型|
|---|---|
|waitmoving.py|file|
|organized|dir|
运行“waitmoving.py”，参数为整理好的文件夹，

整理好的文件会被以路径的形式登记，并标记哈希值，记录在“organized”文件中，

### 文件归档后
相关文件：

|名称|类型|
|---|---|
|merge.py|file|
|unzip|dir|
|zip|dir|
|download|dir|
|organized|dir|
|final|dir|
运行“merge.py”，会自动读取unzip文件夹，zip文件夹，download文件夹和move下的对应内容，对应项目会在上述文件夹中删除，并入final文件夹
### 文件移动后
相关文件：

|名称|类型|
|---|---|
|move.py|file|
|final|dir|

根据现有目录查询，找到不存在的内容，标记为moved，找到不记录的内容，标记为“unfind”，在宽松模式下，文件名相同且不重复的会被直接引入，文件名多个相同，或不存在相同的会被计算哈希值并寻找，在严格模式下，所有的变化全部被计算哈希。

## 记录结构
相关文件：

|item       |结构   |作用               |其他解释|
|---        |---    |---                |---|
|hashMd5    |str    |文件的哈希值       |当出现哈希碰撞时，使用-n来记录重复序号|
|originPath |str[]  |文件下载后的路径   |鉴于有可能下载到重复文件，有可能存在多个|
|end        |str    |结束标记           |   |
|changePath |str[]  |文件的变化纪录     |在导入时就已经进行了去重，因此文件的变化记录仅记录存在的文件，是线性结构，而被删除的文件会被记录在相对文件夹中的“redirect.txt中”   |
|unzipFrom  |str[]  |从某个文件解压而来 |对已有的压缩包进行解压以消除密码和方便查阅，不同压缩包的内容可能相同|
|zipTo      |str[]  |压缩至             |对小文件可能采取压缩的方式以节约空间和加快索引速度，因此可能会产生一些压缩文件|
|nowPath    |str    |现在的存储路径     |自动生成|
|nowName    |str    |现在的文件名       |自动生成|

## 文件结构
相关文件：

|文件夹|解释|
|---|---|
|downloads  |下载后的文件的生成记录被记录在这里，在转移后会被删除，并产生更新后的文件|
|organize   |整理的记录表，每次使用后都会以日期保留|
|final      |最终的记录表|
|passwords  |压缩包的密码字典，暴力解压用，***警告：不是现在压缩包的密码，不会使用加密***   |
|disks      |存储硬盘的相关信息（总大小，剩余空间，特定smart信息等）|
