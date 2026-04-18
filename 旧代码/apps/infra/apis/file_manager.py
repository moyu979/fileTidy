import os
from datetime import datetime
from typing import Optional

from apps.common.database.models import FileSourcesModel, FileLocationsModel
from apps.common.database.session import session_scope
from apps.common.utils.hash import compute_hash
from apps.common.utils.get_size import get_size
from apps.infra.volume.volume_manager import volume_manager
from apps.common.log.file_logger import FileLogger
from apps.common.exceptions import HashConflictError


def reg_file(
    path: str,
    state: Optional[str] = None,
    info: Optional[str] = None,
    add_time: Optional[datetime] = None,
    auto_add_to_locations: bool = True,
):
    """
    注册文件
    遍历path下的所有文件，计算文件的md5和sha512，获取文件大小，然后写入到FileSourcesModel表中
    
    Args:
        path: 文件或目录的路径
        state: 文件状态，默认为None，如果为None则使用模型默认值"online"
        info: 文件其他信息，默认为None，如果为None则使用模型默认值""
        add_time: 文件添加时间，默认为None，如果为None则使用模型默认值（当前UTC时间）
        auto_add_to_locations: 是否自动添加到FileLocationsModel，默认为True
    
    Returns:
        int: 成功注册的文件数量
    
    Raises:
        FileNotFoundError: 路径不存在
        PermissionError: 没有权限访问文件或目录
        OSError: 其他文件系统错误
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"路径不存在: {path}")
    
    # 确定要处理的文件列表
    files_to_process = []
    if os.path.isfile(path):
        files_to_process.append(path)
    elif os.path.isdir(path):
        for root, _, files in os.walk(path):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                files_to_process.append(file_path)
    else:
        raise ValueError(f"路径既不是文件也不是目录: {path}")
    
    # 处理默认值（用于所有文件的通用默认值）
    default_state = state if state is not None else "online"  # 使用模型默认值
    default_info = info if info is not None else ""  # 使用模型默认值
    default_add_time = add_time if add_time is not None else datetime.utcnow()  # 统一使用一个时间
    
    # 获取卷id和卷路径（统一获取一次，所有文件共用）
    volume_id = volume_manager.get_volume_id(path)
    volume_data_path = None
    abs_volume_path = None
    if volume_id:
        volume_data_path = volume_manager.get_data_path(volume_id)
        if volume_data_path:
            abs_volume_path = os.path.abspath(volume_data_path)
        else:
            volume_id = None
    
    success_count = 0
    
    with session_scope() as session:
        for file_path in files_to_process:
            try:
                # 计算文件的md5和sha512
                hash_result = compute_hash(file_path, enable_sha512=True, enable_md5=True)
                sha512 = hash_result.get("sha512")
                md5 = hash_result.get("md5")
                
                # 获取文件大小
                file_size = get_size(file_path)
                
                # 将文件路径转换为绝对路径
                abs_file_path = os.path.abspath(file_path)
                
                # 检查FileSourcesModel中是否已存在相同的md5、sha512和path
                existing_file_source = session.query(FileSourcesModel).filter(
                    FileSourcesModel.md5 == md5,
                    FileSourcesModel.sha512 == sha512,
                    FileSourcesModel.from_path == abs_file_path
                ).first()
                
                # 如果已存在，跳过并记录日志
                if existing_file_source:
                    print(f"跳过: 文件 {abs_file_path} 已存在于FileSourcesModel中（md5、sha512、path都重复）")
                    FileLogger.skip_duplicate(
                        path=abs_file_path,
                        md5=md5,
                        sha512=sha512
                    )
                    continue
                
                # 创建FileSourcesModel实例
                file_source = FileSourcesModel(
                    sha512=sha512,
                    md5=md5,
                    size=file_size,
                    from_path=abs_file_path,
                    state=default_state,
                    info=default_info,
                    add_time=default_add_time,
                )
                
                # 添加到session
                session.add(file_source)
                
                # 记录FileSourcesModel的reg操作（标记文件到源）
                FileLogger.reg(
                    path=abs_file_path,
                    md5=md5,
                    sha512=sha512
                )
                # 如果启用自动添加到FileLocationsModel且卷id有效，记录到FileLocationsModel
                if auto_add_to_locations and volume_id and abs_volume_path:
                    # 检查文件路径是否在卷路径下
                    if abs_file_path.startswith(abs_volume_path):
                        # 计算相对路径（去掉卷路径）
                        relative_path = os.path.relpath(abs_file_path, abs_volume_path)
                        # 统一使用正斜杠作为路径分隔符
                        now_path = relative_path.replace(os.sep, '/')
                        
                        # 创建FileLocationsModel实例
                        file_location = FileLocationsModel(
                            sha512=sha512,
                            md5=md5,
                            size=file_size,
                            now_path=now_path,
                            now_volume=volume_id,
                            state=default_state,
                            info=default_info,
                            add_time=default_add_time,
                        )
                        
                        # 添加到session
                        session.add(file_location)
                        
                        # 记录FileLocationsModel的intro操作：从源将文件导入数据库内卷
                        dst_path = f"{volume_id}/{now_path}"
                        FileLogger.intro(
                            path=abs_file_path,
                            md5=md5,
                            sha512=sha512,
                            dst=dst_path
                        )
                
                success_count += 1
                
            except (FileNotFoundError, PermissionError, OSError) as e:
                # 对于单个文件处理失败，记录错误但继续处理其他文件
                print(f"警告: 无法处理文件 {file_path}: {e}")
                continue
            except Exception as e:
                # 其他异常也记录但继续处理
                print(f"警告: 处理文件 {file_path} 时发生错误: {e}")
                continue
    
    return success_count

def intro_file(
    path: str,
    state: Optional[str] = None,
    info: Optional[str] = None,
    add_time: Optional[datetime] = None,
):
    """
    导入文件到数据集
    遍历path下的所有文件，计算文件的md5和sha512，获取文件大小
    如果文件存在于FileSourcesModel，则写入FileLocationsModel
    如果文件不存在于FileSourcesModel，则跳过该文件
    如果文件路径在FileLocationsModel中已存在但哈希值不匹配，则抛出HashConflictError异常
    
    Args:
        path: 文件或目录的路径
        state: 文件状态，默认为None，如果为None则使用模型默认值"online"
        info: 文件其他信息，默认为None，如果为None则使用模型默认值""
        add_time: 文件添加时间，默认为None，如果为None则使用模型默认值（当前UTC时间）
    
    Returns:
        int: 成功导入的文件数量
    
    Raises:
        FileNotFoundError: 路径不存在
        PermissionError: 没有权限访问文件或目录
        OSError: 其他文件系统错误
        HashConflictError: 文件路径在FileLocationsModel中已存在，但哈希值不匹配
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"路径不存在: {path}")
    
    # 确定要处理的文件列表
    files_to_process = []
    if os.path.isfile(path):
        files_to_process.append(path)
    elif os.path.isdir(path):
        for root, _, files in os.walk(path):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                files_to_process.append(file_path)
    else:
        raise ValueError(f"路径既不是文件也不是目录: {path}")
    
    # 处理默认值（用于所有文件的通用默认值）
    default_state = state if state is not None else "online"  # 使用模型默认值
    default_info = info if info is not None else ""  # 使用模型默认值
    default_add_time = add_time if add_time is not None else datetime.utcnow()  # 统一使用一个时间
    
    # 获取卷id和卷路径（统一获取一次，所有文件共用）
    volume_id = volume_manager.get_volume_id(path)
    volume_data_path = None
    abs_volume_path = None
    if volume_id:
        volume_data_path = volume_manager.get_data_path(volume_id)
        if volume_data_path:
            abs_volume_path = os.path.abspath(volume_data_path)
        else:
            volume_id = None
    
    if not volume_id or not abs_volume_path:
        raise ValueError("无法获取有效的卷id或卷路径，无法导入文件")
    
    success_count = 0
    
    with session_scope() as session:
        for file_path in files_to_process:
            try:
                # 计算文件的md5和sha512
                hash_result = compute_hash(file_path, enable_sha512=True, enable_md5=True)
                sha512 = hash_result.get("sha512")
                md5 = hash_result.get("md5")
                
                # 获取文件大小
                file_size = get_size(file_path)
                
                # 将文件路径转换为绝对路径
                abs_file_path = os.path.abspath(file_path)
                
                # 检查文件是否存在于FileSourcesModel（通过sha512查询）
                existing_file_source = session.query(FileSourcesModel).filter(
                    FileSourcesModel.sha512 == sha512
                ).first()
                
                # 如果文件不存在于FileSourcesModel，直接跳过
                if not existing_file_source:
                    print(f"跳过: 文件 {abs_file_path} 不存在于FileSourcesModel中")
                    continue
                
                # 检查文件路径是否在卷路径下
                if abs_file_path.startswith(abs_volume_path):
                    # 计算相对路径（去掉卷路径）
                    relative_path = os.path.relpath(abs_file_path, abs_volume_path)
                    # 统一使用正斜杠作为路径分隔符
                    now_path = relative_path.replace(os.sep, '/')
                    
                    # 检查FileLocationsModel中是否已存在该路径的记录
                    existing_location = session.query(FileLocationsModel).filter(
                        FileLocationsModel.now_volume == volume_id,
                        FileLocationsModel.now_path == now_path
                    ).first()
                    
                    if existing_location:
                        # 如果路径已存在，检查哈希值
                        if existing_location.md5 == md5 and existing_location.sha512 == sha512:
                            # 路径和两个哈希都相同，跳过
                            print(f"跳过: 文件 {abs_file_path} 在FileLocationsModel中已存在（路径和哈希都相同）")
                            continue
                        else:
                            # 路径已存在，但哈希值不同，抛出异常
                            error_msg = (
                                f"文件 {abs_file_path} 在FileLocationsModel中路径已存在，但哈希值不匹配\n"
                                f"  现有记录 - md5: {existing_location.md5}, sha512: {existing_location.sha512}\n"
                                f"  当前文件 - md5: {md5}, sha512: {sha512}"
                            )
                            raise HashConflictError(error_msg)
                    
                    # 路径不存在，创建新记录
                    # 创建FileLocationsModel实例
                    file_location = FileLocationsModel(
                        sha512=sha512,
                        md5=md5,
                        size=file_size,
                        now_path=now_path,
                        now_volume=volume_id,
                        state=default_state,
                        info=default_info,
                        add_time=default_add_time,
                    )
                    
                    # 添加到session
                    session.add(file_location)
                    
                    # 记录FileLocationsModel的intro操作：从源将文件导入数据库内卷
                    dst_path = f"{volume_id}/{now_path}"
                    FileLogger.intro(
                        path=abs_file_path,
                        md5=md5,
                        sha512=sha512,
                        dst=dst_path
                    )
                
                success_count += 1
                
            except (FileNotFoundError, PermissionError, OSError) as e:
                # 对于单个文件处理失败，记录错误但继续处理其他文件
                print(f"警告: 无法处理文件 {file_path}: {e}")
                continue
            except Exception as e:
                # 其他异常也记录但继续处理
                print(f"警告: 处理文件 {file_path} 时发生错误: {e}")
                continue
    return success_count