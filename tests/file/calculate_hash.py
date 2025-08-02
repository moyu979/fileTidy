import core.file.calculate_hash as calculate_hash
import json
import os
import core.conf.conf as conf


def tests():
    conf.init_conf()
    md5 = calculate_hash.calculate_md5("./readme.md")  # 替换为实际的测试文件路径
    print(f"readme.md 的MD5值是: {md5}")
