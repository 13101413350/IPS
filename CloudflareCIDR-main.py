import os
import shutil
import zipfile
import requests
import re

# 下载zip文件
url = "https://github.com/ipverse/asn-ip/archive/refs/heads/master.zip"
try:
    r = requests.get(url, timeout=30)
    r.raise_for_status()  # 检查请求是否成功
    with open("master.zip", "wb") as code:
        code.write(r.content)
except requests.exceptions.RequestException as e:
    print(f"下载失败: {e}")
    exit(1)

# 解压zip文件
try:
    with zipfile.ZipFile("master.zip", 'r') as zip_ref:
        zip_ref.extractall(".")
except zipfile.BadZipFile:
    print("下载的文件损坏")
    exit(1)

# 将结果存储在这个列表中
ip_addresses = []
included_asns = ['209242', '13335', '149648', '132892', '139242', '202623', '203898', '394536']

# 遍历as文件夹
extract_dir = "asn-ip-master"
if not os.path.exists(extract_dir):
    print(f"找不到解压目录: {extract_dir}")
    exit(1)

for root, dirs, files in os.walk(os.path.join(extract_dir, "as")):
    if 'ipv4-aggregated.txt' in files:
        asn = os.path.basename(root)  # 使用basename代替split
        if asn in included_asns:
            file_path = os.path.join(root, 'ipv4-aggregated.txt')
            try:
                with open(file_path, 'r') as file:
                    ips = file.read().splitlines()
                    ip_addresses.extend(ips)
            except IOError as e:
                print(f"读取文件 {file_path} 失败: {e}")

# 正则表达式用于匹配IPv4地址和子网掩码
# 修复：允许1-3位数字，且子网掩码范围为0-32
ipv4_regex = re.compile(r'^(\d{1,3}\.){3}\d{1,3}/([0-9]|[1-2][0-9]|3[0-2])$')

# 创建输出目录（如果不存在）
output_dir = "Clash"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# 将结果写入两个文件
try:
    with open(os.path.join(output_dir, 'CloudflareCIDR.list'), 'w') as clash_file, \
         open('CloudflareCIDR.txt', 'w') as cidr_file:
        
        valid_count = 0
        invalid_count = 0
        
        for ip in ip_addresses:
            # 检查IP是否符合IPv4/子网掩码格式
            if ipv4_regex.match(ip):
                clash_file.write(f"IP-CIDR,{ip},no-resolve\n")
                cidr_file.write(f"{ip}\n")
                valid_count += 1
            else:
                # 对于无效格式，仍然写入但添加注释标记
                clash_file.write(f"# INVALID: {ip}\n")
                cidr_file.write(f"# {ip}\n")
                invalid_count += 1
                print(f"警告: 无效的IP格式 - {ip}")
        
        print(f"处理完成: 有效IP {valid_count} 条, 无效IP {invalid_count} 条")
        
except IOError as e:
    print(f"写入文件失败: {e}")
    exit(1)

# 清理下载的zip文件和解压的文件夹
try:
    if os.path.exists("master.zip"):
        os.remove("master.zip")
    if os.path.exists(extract_dir):
        shutil.rmtree(extract_dir)
    print("清理完成")
except Exception as e:
    print(f"清理文件时出错: {e}")
