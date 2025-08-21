#!/usr/bin/env python3
"""
命令行接口模块

提供项目的命令行工具功能。
"""
import asyncio
import sys
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from config import config
from src.deployment import deploy_flows
from src.flows import hello_flow, health_check_flow
from src.health import get_health_status, get_readiness_status, get_liveness_status
from src.logging_config import setup_global_loggers
from src.metrics import metrics

console = Console()


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='启用详细输出')
@click.option('--config-file', help='配置文件路径')
def cli(verbose: bool, config_file: Optional[str]):
    """Prefect CI/CD 命令行工具"""
    if verbose:
        config.log_level = "DEBUG"
    
    # 设置日志
    setup_global_loggers()
    
    if config_file:
        console.print(f"[yellow]注意: 配置文件参数 {config_file} 暂未实现[/yellow]")


@cli.command()
@click.option('--name', default='World', help='问候对象的名称')
def run(name: str):
    """运行示例流程"""
    console.print(f"[blue]运行问候流程，目标: {name}[/blue]")
    
    try:
        result = hello_flow(name)
        console.print(f"[green]✅ 流程执行成功: {result}[/green]")
    except Exception as e:
        console.print(f"[red]❌ 流程执行失败: {e}[/red]")
        sys.exit(1)


@cli.command()
def deploy():
    """部署所有流程到Prefect"""
    console.print("[blue]开始部署流程...[/blue]")
    
    # 验证配置
    missing_configs = config.validate_required_settings()
    if missing_configs:
        console.print(f"[red]❌ 缺少必要配置: {', '.join(missing_configs)}[/red]")
        sys.exit(1)
    
    try:
        results = deploy_flows()
        
        # 显示部署结果
        table = Table(title="部署结果")
        table.add_column("流程名称", style="cyan")
        table.add_column("状态", style="magenta")
        table.add_column("详情", style="green")
        
        for flow_name, result in results.items():
            status = result.get('status', 'unknown')
            details = result.get('id', result.get('error', 'N/A'))
            
            status_color = "green" if status == "success" else "red"
            table.add_row(flow_name, f"[{status_color}]{status}[/{status_color}]", str(details))
        
        console.print(table)
        
        # 检查是否有失败的部署
        failed_deployments = [name for name, result in results.items() 
                            if result.get('status') != 'success']
        
        if failed_deployments:
            console.print(f"[yellow]⚠️  部分部署失败: {', '.join(failed_deployments)}[/yellow]")
        else:
            console.print("[green]✅ 所有流程部署成功![/green]")
            
    except Exception as e:
        console.print(f"[red]❌ 部署失败: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--format', type=click.Choice(['table', 'json']), default='table', help='输出格式')
def health(format: str):
    """检查应用健康状态"""
    console.print("[blue]检查应用健康状态...[/blue]")
    
    try:
        health_status = asyncio.run(get_health_status())
        
        if format == 'json':
            import json
            console.print(json.dumps(health_status, indent=2, ensure_ascii=False))
        else:
            # 表格格式
            overall_status = health_status.get('status', 'unknown')
            status_color = "green" if overall_status == "healthy" else "red"
            
            console.print(f"[{status_color}]整体状态: {overall_status}[/{status_color}]")
            
            table = Table(title="健康检查详情")
            table.add_column("检查项", style="cyan")
            table.add_column("状态", style="magenta")
            table.add_column("耗时(ms)", style="yellow")
            table.add_column("详情", style="green")
            
            for check in health_status.get('checks', []):
                check_status = check.get('status', 'unknown')
                status_color = "green" if check_status == "healthy" else "red"
                
                duration = check.get('duration_ms', 'N/A')
                details = check.get('details', check.get('error', 'N/A'))
                
                table.add_row(
                    check.get('name', 'Unknown'),
                    f"[{status_color}]{check_status}[/{status_color}]",
                    str(duration),
                    str(details)[:50] + "..." if len(str(details)) > 50 else str(details)
                )
            
            console.print(table)
            
    except Exception as e:
        console.print(f"[red]❌ 健康检查失败: {e}[/red]")
        sys.exit(1)


@cli.command()
def readiness():
    """检查应用就绪状态"""
    console.print("[blue]检查应用就绪状态...[/blue]")
    
    try:
        readiness_status = asyncio.run(get_readiness_status())
        status = readiness_status.get('status', 'unknown')
        status_color = "green" if status == "ready" else "red"
        
        console.print(f"[{status_color}]就绪状态: {status}[/{status_color}]")
        
        for check in readiness_status.get('checks', []):
            check_name = check.get('name', 'Unknown')
            check_status = check.get('status', 'unknown')
            check_color = "green" if check_status == "healthy" else "red"
            console.print(f"  - {check_name}: [{check_color}]{check_status}[/{check_color}]")
            
    except Exception as e:
        console.print(f"[red]❌ 就绪检查失败: {e}[/red]")
        sys.exit(1)


@cli.command()
def liveness():
    """检查应用存活状态"""
    console.print("[blue]检查应用存活状态...[/blue]")
    
    try:
        liveness_status = asyncio.run(get_liveness_status())
        status = liveness_status.get('status', 'unknown')
        uptime = liveness_status.get('uptime_seconds', 0)
        
        status_color = "green" if status == "alive" else "red"
        console.print(f"[{status_color}]存活状态: {status}[/{status_color}]")
        console.print(f"运行时间: {uptime:.2f} 秒")
        
    except Exception as e:
        console.print(f"[red]❌ 存活检查失败: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--format', type=click.Choice(['table', 'json']), default='table', help='输出格式')
def metrics_cmd(format: str):
    """查看应用指标"""
    console.print("[blue]收集应用指标...[/blue]")
    
    try:
        metrics_data = metrics.get_all_metrics()
        
        if format == 'json':
            import json
            console.print(json.dumps(metrics_data, indent=2, ensure_ascii=False))
        else:
            # 表格格式显示摘要
            console.print(f"[cyan]指标收集时间: {metrics_data.get('timestamp', 'N/A')}[/cyan]")
            console.print(f"[cyan]运行时间: {metrics_data.get('uptime_seconds', 0):.2f} 秒[/cyan]")
            
            # 计数器
            counters = metrics_data.get('counters', {})
            if counters:
                console.print("\n[yellow]计数器指标:[/yellow]")
                for name, points in counters.items():
                    total = sum(point.get('value', 0) for point in points)
                    console.print(f"  - {name}: {total}")
            
            # 仪表盘
            gauges = metrics_data.get('gauges', {})
            if gauges:
                console.print("\n[yellow]仪表盘指标:[/yellow]")
                for name, points in gauges.items():
                    if points:
                        latest_value = points[-1].get('value', 0)
                        console.print(f"  - {name}: {latest_value}")
            
            # 直方图
            histograms = metrics_data.get('histograms', {})
            if histograms:
                console.print("\n[yellow]直方图指标:[/yellow]")
                for name, summary in histograms.items():
                    count = summary.get('count', 0)
                    avg = summary.get('avg', 0)
                    console.print(f"  - {name}: count={count}, avg={avg:.3f}")
                    
    except Exception as e:
        console.print(f"[red]❌ 指标收集失败: {e}[/red]")
        sys.exit(1)


@cli.command()
def config_info():
    """显示当前配置信息"""
    console.print("[blue]当前配置信息:[/blue]")
    
    config.print_config_info()
    
    # 验证配置
    missing_configs = config.validate_required_settings()
    if missing_configs:
        console.print(f"\n[red]❌ 缺少必要配置: {', '.join(missing_configs)}[/red]")
    else:
        console.print("\n[green]✅ 配置验证通过[/green]")


@cli.command()
def version():
    """显示版本信息"""
    console.print("[cyan]Prefect CI/CD Example v1.0.0[/cyan]")
    console.print(f"Python: {sys.version}")
    console.print(f"环境: {config.environment}")
    console.print(f"部署模式: {'是' if config.deploy_mode else '否'}")


def main():
    """主入口函数"""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]操作被用户中断[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"[red]❌ 未预期的错误: {e}[/red]")
        sys.exit(1)


if __name__ == '__main__':
    main()
