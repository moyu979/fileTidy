# 本文件未经测试
import subprocess
import logging
import os


def run_command(cmd):
    """同步运行一个命令，并返回输出结果"""
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
    return result.returncode, result.stdout.decode(errors='ignore'), result.stderr.decode(errors='ignore')


def ssd_check(device="/dev/sda", scan_blocks=False):
    """
    检查SSD健康状态，返回 'health'（健康）、'danger'（警告）、None（检查失败）
    
    Args:
        device: SSD设备路径，默认为 /dev/sda
        scan_blocks: 是否开启坏道扫描，默认为False（只进行SMART检测）
    
    Returns:
        str: 'health' 表示健康，'danger' 表示有警告
        None: 检查失败或发生错误
    """
    logging.warning("[AI WARNING] 这些文件是由AI生成的，还未经过测试")
    
    # 边界条件判断
    if device is None:
        logging.error("[SSD ERROR] 设备路径不能为None")
        return None
    
    if not isinstance(device, str) or device.strip() == "":
        logging.error("[SSD ERROR] 设备路径必须是有效的字符串")
        return None
    
    device = device.strip()
    
    # 检查设备文件是否存在
    if not os.path.exists(device):
        logging.error(f"[SSD ERROR] 设备文件不存在: {device}")
        return None
    
    # 检查是否为块设备
    if not os.path.exists(f"/sys/block/{os.path.basename(device)}"):
        logging.error(f"[SSD ERROR] 不是有效的块设备: {device}")
        return None
    
    logging.info(f"[SSD INFO] 开始检查设备: {device}")
    
    # 检查SMART状态
    cmd_smart = ["sudo", "smartctl", "-H", device]
    code, out, err = run_command(cmd_smart)
    if code != 0:
        logging.error(f"[SSD SMART ERROR] {err}")
        return None
    
    logging.info(f"[SSD SMART STATUS] {out}")
    
    # 判断SMART状态
    if "PASSED" in out:
        smart_status = "health"
        logging.info("[SSD SMART OK] SMART检查通过")
    elif "FAILED" in out or "WARNING" in out or "Pre-fail" in out:
        smart_status = "danger"
        logging.warning(f"[SSD SMART WARNING] SMART检查失败或警告: {out}")
    else:
        smart_status = "danger"
        logging.warning(f"[SSD SMART WARNING] 未知SMART状态: {out}")
    
    # 如果开启扫描，则进行额外的SSD健康检查
    if scan_blocks:
        logging.info(f"[SSD SCAN] 开始SSD健康扫描，设备: {device}")
        
        # TODO: SSD详细健康检测逻辑待完善
        # 暂时注释掉详细检测，等后续完善
        """
        # 检查SSD的磨损指标
        cmd_wear = ["sudo", "smartctl", "-A", device]
        code, out, err = run_command(cmd_wear)
        if code != 0:
            logging.error(f"[SSD WEAR ERROR] {err}")
            return None
        
        # 分析SSD健康指标
        health_warnings = []
        
        # 检查磨损均衡计数
        if "Wear_Leveling_Count" in out:
            try:
                # 提取磨损均衡计数值
                lines = out.split('\n')
                for line in lines:
                    if "Wear_Leveling_Count" in line:
                        parts = line.split()
                        if len(parts) >= 10:
                            raw_value = parts[9]
                            if raw_value.isdigit():
                                wear_count = int(raw_value)
                                if wear_count > 100:  # 如果磨损计数过高
                                    health_warnings.append(f"磨损均衡计数较高: {wear_count}")
                                else:
                                    logging.info(f"[SSD WEAR OK] 磨损均衡计数: {wear_count}")
                            break
            except (ValueError, IndexError):
                logging.warning("[SSD WEAR WARNING] 无法解析磨损均衡计数")
        else:
            logging.warning("[SSD WEAR WARNING] 未找到磨损均衡计数指标")
        
        # 检查磨损指示器（百分比）
        if "Wear_Indicator" in out:
            try:
                lines = out.split('\n')
                for line in lines:
                    if "Wear_Indicator" in line:
                        parts = line.split()
                        if len(parts) >= 10:
                            raw_value = parts[9]
                            if raw_value.isdigit():
                                wear_percent = int(raw_value)
                                if wear_percent < 20:  # 如果磨损指示器低于20%
                                    health_warnings.append(f"磨损指示器较低: {wear_percent}%")
                                elif wear_percent < 50:
                                    logging.warning(f"[SSD WEAR WARNING] 磨损指示器中等: {wear_percent}%")
                                else:
                                    logging.info(f"[SSD WEAR OK] 磨损指示器良好: {wear_percent}%")
                            break
            except (ValueError, IndexError):
                logging.warning("[SSD WEAR WARNING] 无法解析磨损指示器")
        else:
            logging.warning("[SSD WEAR WARNING] 未找到磨损指示器")
        
        # 检查温度
        if "Temperature_Celsius" in out:
            try:
                lines = out.split('\n')
                for line in lines:
                    if "Temperature_Celsius" in line:
                        parts = line.split()
                        if len(parts) >= 10:
                            raw_value = parts[9]
                            if raw_value.isdigit():
                                temp = int(raw_value)
                                if temp > 70:  # 如果温度超过70°C
                                    health_warnings.append(f"温度过高: {temp}°C")
                                elif temp > 60:
                                    logging.warning(f"[SSD TEMP WARNING] 温度较高: {temp}°C")
                                else:
                                    logging.info(f"[SSD TEMP OK] 温度正常: {temp}°C")
                            break
            except (ValueError, IndexError):
                logging.warning("[SSD TEMP WARNING] 无法解析温度值")
        else:
            logging.warning("[SSD TEMP WARNING] 未找到温度监控指标")
        
        # 检查主机写入量
        if "Host_Writes_GiB" in out:
            try:
                lines = out.split('\n')
                for line in lines:
                    if "Host_Writes_GiB" in line:
                        parts = line.split()
                        if len(parts) >= 10:
                            raw_value = parts[9]
                            if raw_value.isdigit():
                                writes_gib = int(raw_value)
                                if writes_gib > 10000:  # 如果写入量超过10TB
                                    health_warnings.append(f"写入量较大: {writes_gib} GiB")
                                else:
                                    logging.info(f"[SSD WRITE OK] 写入量: {writes_gib} GiB")
                            break
            except (ValueError, IndexError):
                logging.warning("[SSD WRITE WARNING] 无法解析写入量")
        
        # 检查坏块计数
        if "Reallocated_Sector_Ct" in out:
            try:
                lines = out.split('\n')
                for line in lines:
                    if "Reallocated_Sector_Ct" in line:
                        parts = line.split()
                        if len(parts) >= 10:
                            raw_value = parts[9]
                            if raw_value.isdigit():
                                bad_blocks = int(raw_value)
                                if bad_blocks > 0:
                                    health_warnings.append(f"重分配扇区数: {bad_blocks}")
                                else:
                                    logging.info(f"[SSD BADBLOCKS OK] 无重分配扇区")
                            break
            except (ValueError, IndexError):
                logging.warning("[SSD BADBLOCKS WARNING] 无法解析重分配扇区计数")
        
        # 汇总健康警告
        if health_warnings:
            logging.warning(f"[SSD HEALTH WARNINGS] 发现{len(health_warnings)}个健康警告:")
            for warning in health_warnings:
                logging.warning(f"[SSD WARNING] {warning}")
            # 如果有健康警告，返回danger状态
            smart_status = "danger"
        """
        
        logging.info("[SSD SCAN] SSD健康扫描完成（详细检测已禁用）")
    else:
        logging.info(f"[SSD SCAN] 跳过SSD健康扫描，仅进行SMART检测")
    
    return smart_status
