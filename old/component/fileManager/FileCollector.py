"""
这是一个用于文件收集的类，提供两个函数，collect和clear，
接收这样几个参数:
    src_path: 源路径，一般是绝对路径
    dst_path: 目标路径，也是绝对路径
    size:需要收集的文件大小
    level：邻居情况
完成这样的功能：
collect:
    将src_path路径下的文件，依次*复制*到dst_path路径下，直到再拷贝一个文件，总大小就会超出为止，然后，收集最后一个文件的邻居文件，直到size仅可能逼近size为止，邻居这样定义：
    将文件系统视作一个树，如果两个文件的level个父目录之内有公共节点，就认为这两个文件是邻居
    在复制时，记录每个文件的原始路径和目标路径对
clear:
    根据记录的路径对，将文件从src中删除

"""
import os
import shutil
from pathlib import Path
from typing import List, Tuple


class FileCollector:
    def __init__(self):
        self.file_pairs: List[Tuple[str, str]] = []  # (src_path, dst_path)
    
    def _get_file_size(self, file_path: str) -> int:
        """获取文件大小"""
        return os.path.getsize(file_path)
    
    def _get_parent_paths(self, file_path: str, level: int) -> List[str]:
        """获取文件的level个父目录路径"""
        path = Path(file_path)
        parents = []
        current = path.parent
        for _ in range(level):
            parents.append(str(current))
            current = current.parent
            if current == current.parent:  # 到达根目录
                break
        return parents
    
    def _are_neighbors(self, file1: str, file2: str, level: int) -> bool:
        """判断两个文件是否是邻居（在level个父目录内有公共节点）"""
        parents1 = set(self._get_parent_paths(file1, level))
        parents2 = set(self._get_parent_paths(file2, level))
        return bool(parents1 & parents2)
    
    def _copy_file(self, src: str, dst: str) -> bool:
        """复制文件，如果目标目录不存在则创建"""
        try:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            return True
        except Exception:
            return False
    
    def collect(self, src_path: str, dst_path: str, size: int, level: int):
        """收集文件到目标路径"""
        self.file_pairs.clear()
        current_size = 0
        all_files = []
        last_file = None
        
        # 收集所有文件及其大小
        for root, dirs, files in os.walk(src_path):
            for file in files:
                file_path = os.path.join(root, file)
                file_size = self._get_file_size(file_path)
                all_files.append((file_path, file_size))
        
        # 按顺序复制文件，直到接近size限制
        for file_path, file_size in all_files:
            if current_size + file_size > size:
                last_file = file_path
                break
            
            # 计算目标路径（保持相对路径结构）
            rel_path = os.path.relpath(file_path, src_path)
            dst_file_path = os.path.join(dst_path, rel_path)
            
            if self._copy_file(file_path, dst_file_path):
                self.file_pairs.append((file_path, dst_file_path))
                current_size += file_size
        
        # 如果还有空间，收集最后一个文件的邻居文件
        if last_file and current_size < size:
            neighbors = []
            for file_path, file_size in all_files:
                if file_path == last_file:
                    continue
                # 检查是否已经复制过
                if any(fp[0] == file_path for fp in self.file_pairs):
                    continue
                # 检查是否是邻居
                if self._are_neighbors(last_file, file_path, level):
                    neighbors.append((file_path, file_size))
            
            # 按文件大小排序，优先添加小文件以更精确地接近目标大小
            neighbors.sort(key=lambda x: x[1])
            
            # 添加邻居文件直到接近size
            for file_path, file_size in neighbors:
                if current_size + file_size > size:
                    break
                
                rel_path = os.path.relpath(file_path, src_path)
                dst_file_path = os.path.join(dst_path, rel_path)
                
                if self._copy_file(file_path, dst_file_path):
                    self.file_pairs.append((file_path, dst_file_path))
                    current_size += file_size
    
    def clear(self):
        """根据记录的路径对，删除源文件"""
        for src_path, _ in self.file_pairs:
            try:
                if os.path.exists(src_path):
                    os.remove(src_path)
                    # 如果父目录为空，尝试删除（可选）
                    parent_dir = os.path.dirname(src_path)
                    if parent_dir and os.path.exists(parent_dir):
                        try:
                            if not os.listdir(parent_dir):
                                os.rmdir(parent_dir)
                        except Exception:
                            pass
            except Exception:
                pass
        self.file_pairs.clear()
