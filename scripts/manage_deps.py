#!/usr/bin/env python3
"""
依赖管理脚本

用于管理项目依赖，包括安装、更新、检查安全漏洞等功能。
"""
import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """运行命令并返回结果"""
    print(f"运行命令: {' '.join(cmd)}")
    return subprocess.run(cmd, check=check, capture_output=True, text=True)


def install_deps(dev: bool = False, tools: bool = False, monitoring: bool = False):
    """安装依赖"""
    print("📦 安装依赖...")
    
    # 基础安装
    cmd = [sys.executable, "-m", "pip", "install", "-e", "."]
    
    # 添加可选依赖
    extras = []
    if dev:
        extras.append("dev")
    if tools:
        extras.append("tools")
    if monitoring:
        extras.append("monitoring")
    
    if extras:
        cmd[-1] = f".[{','.join(extras)}]"
    
    try:
        result = run_command(cmd)
        print("✅ 依赖安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖安装失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False


def update_lock_file():
    """更新锁定文件"""
    print("🔒 更新依赖锁定文件...")
    
    try:
        # 生成新的锁定文件
        result = run_command([sys.executable, "-m", "pip", "freeze"])
        
        lock_file = Path("requirements-lock.txt")
        
        # 添加注释头
        header = """# 锁定版本的依赖文件
# 这个文件包含精确的版本号，用于确保环境一致性
# 生成时间: {timestamp}
# 生成方式: pip freeze > requirements-lock.txt
# 使用方式: pip install -r requirements-lock.txt

""".format(timestamp=subprocess.run(["date"], capture_output=True, text=True).stdout.strip())
        
        with open(lock_file, "w") as f:
            f.write(header)
            f.write(result.stdout)
        
        print(f"✅ 锁定文件已更新: {lock_file}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 更新锁定文件失败: {e}")
        return False


def check_security():
    """检查安全漏洞"""
    print("🔍 检查依赖安全漏洞...")
    
    try:
        # 尝试使用safety检查
        result = run_command([sys.executable, "-m", "safety", "check"], check=False)
        
        if result.returncode == 0:
            print("✅ 未发现安全漏洞")
        else:
            print("⚠️ 发现潜在安全漏洞:")
            print(result.stdout)
            print(result.stderr)
        
        return result.returncode == 0
    except FileNotFoundError:
        print("⚠️ safety工具未安装，跳过安全检查")
        print("安装方式: pip install safety")
        return True


def check_outdated():
    """检查过时的依赖"""
    print("📊 检查过时的依赖...")
    
    try:
        result = run_command([sys.executable, "-m", "pip", "list", "--outdated"])
        
        if result.stdout.strip():
            print("📋 过时的依赖:")
            print(result.stdout)
        else:
            print("✅ 所有依赖都是最新的")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 检查过时依赖失败: {e}")
        return False


def validate_deps():
    """验证依赖完整性"""
    print("✅ 验证依赖完整性...")
    
    try:
        # 检查依赖冲突
        result = run_command([sys.executable, "-m", "pip", "check"])
        print("✅ 依赖验证通过")
        return True
    except subprocess.CalledProcessError as e:
        print("❌ 发现依赖冲突:")
        print(e.stdout)
        print(e.stderr)
        return False


def clean_deps():
    """清理依赖缓存"""
    print("🧹 清理依赖缓存...")
    
    try:
        # 清理pip缓存
        run_command([sys.executable, "-m", "pip", "cache", "purge"])
        print("✅ 缓存清理完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 缓存清理失败: {e}")
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="依赖管理工具")
    parser.add_argument("action", choices=[
        "install", "update-lock", "check-security", 
        "check-outdated", "validate", "clean", "all"
    ], help="要执行的操作")
    
    parser.add_argument("--dev", action="store_true", help="包含开发依赖")
    parser.add_argument("--tools", action="store_true", help="包含工具依赖")
    parser.add_argument("--monitoring", action="store_true", help="包含监控依赖")
    
    args = parser.parse_args()
    
    success = True
    
    if args.action == "install":
        success = install_deps(args.dev, args.tools, args.monitoring)
    elif args.action == "update-lock":
        success = update_lock_file()
    elif args.action == "check-security":
        success = check_security()
    elif args.action == "check-outdated":
        success = check_outdated()
    elif args.action == "validate":
        success = validate_deps()
    elif args.action == "clean":
        success = clean_deps()
    elif args.action == "all":
        print("🚀 执行完整的依赖管理流程...")
        success = (
            install_deps(args.dev, args.tools, args.monitoring) and
            validate_deps() and
            check_security() and
            check_outdated() and
            update_lock_file()
        )
    
    if success:
        print("🎉 操作完成!")
        sys.exit(0)
    else:
        print("💥 操作失败!")
        sys.exit(1)


if __name__ == "__main__":
    main()
