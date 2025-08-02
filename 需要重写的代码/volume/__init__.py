"""
    volume_manager
    This module provides functionality for managing volumes in a file system.

    应该实现的功能：
        volume:对某个卷的管理，包括文件检查

        volumeFactory:卷工厂，负责创建和加载卷
        tools:一些工具函数，可能包括获取卷容量等

        应该实现的接口：
            获得一个已经存在的卷（可能从数据库或者硬盘读取，这块好像没必要用缓存），但是不用缓存的话，如何解析已经挂载的硬盘？维护一个volumeid：挂载点的列表是不是一个好的方法？
            
"""
