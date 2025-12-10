import os
import asyncio
import json
import time
import argparse
from datetime import datetime
from llm_benchmark import run_benchmark
import numpy as np
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.style import Style

async def run_all_benchmarks(llm_url, api_key, model, use_long_context):
    configurations = [
        {"num_requests": 10, "concurrency": 1, "output_tokens": 100},
        {"num_requests": 100, "concurrency": 50, "output_tokens": 100},
        {"num_requests": 200, "concurrency": 100, "output_tokens": 100},
        {"num_requests": 400, "concurrency": 200, "output_tokens": 100},
        {"num_requests": 600, "concurrency": 300, "output_tokens": 100},
    ]

    all_results = []

    for config in configurations:
        print(f"Running benchmark with concurrency {config['concurrency']}...")
        results = await run_benchmark(config['num_requests'], config['concurrency'], 30, config['output_tokens'], llm_url, api_key, model, use_long_context)
        all_results.append(results)
        time.sleep(5)  # Wait a bit between runs to let the system cool down

    return all_results

def analyze_results(all_results):
    """分析所有测试结果并生成汇总报告"""
    summary = []
    total_tokens = 0
    total_time = 0
    
    for result in all_results:
        try:
            concurrency = result.get('concurrency', 0)
            rps = result.get('requests_per_second', 0)
            avg_latency = result.get('latency', {}).get('average', 0)
            p99_latency = result.get('latency', {}).get('p99', 0)
            avg_tps = result.get('tokens_per_second', {}).get('average', 0)
            avg_ttft = result.get('time_to_first_token', {}).get('average', 0)
            success_rate = (result.get('successful_requests', 0) / result.get('total_requests', 1)) * 100
            
            # 确保所有值都是有效的数字
            if any(x is None for x in [concurrency, rps, avg_latency, p99_latency, avg_tps, avg_ttft]):
                print(f"警告: 并发数 {concurrency} 的测试结果包含无效数据，已跳过")
                continue

            summary.append([
                concurrency,
                f"{rps:.2f}" if rps is not None else "N/A",
                f"{avg_latency:.3f}" if avg_latency is not None else "N/A",
                f"{p99_latency:.3f}" if p99_latency is not None else "N/A",
                f"{avg_tps:.2f}" if avg_tps is not None else "N/A",
                f"{avg_ttft:.3f}" if avg_ttft is not None else "N/A",
                f"{success_rate:.1f}%" if success_rate is not None else "N/A"
            ])
            
            total_tokens += result.get('total_output_tokens', 0)
            total_time += result.get('total_time', 0)
        except Exception as e:
            print(f"警告: 处理并发数 {result.get('concurrency', 'unknown')} 的结果时出错: {str(e)}")
            continue

    if not summary:
        print("错误: 没有有效的测试结果数据")
        return [], 0, 0

    return summary, total_tokens, total_time

def print_summary(all_results, model_name, use_long_context):
    """打印测试结果汇总"""
    summary, total_tokens, total_time = analyze_results(all_results)
    
    if not summary:
        print("没有可用的测试结果数据进行展示")
        return
    
    console = Console(width=100)  # 设置固定宽度
    
    # 创建标题面板
    title = Text("性能测试汇总报告", style="bold")
    console.print(Panel(title, width=60))
    
    # 打印基本信息
    basic_info = Table(show_header=False, width=60)
    basic_info.add_column("名称", style="cyan", width=20)
    basic_info.add_column("值", style="green", width=40)
    
    basic_info.add_row("模型", model_name)
    basic_info.add_row("长文本模式", "是" if use_long_context else "否")
    basic_info.add_row("总生成Token数", f"{total_tokens:,}")
    basic_info.add_row("总测试时间", f"{total_time:.2f} 秒")
    basic_info.add_row("平均Token生成速率", f"{total_tokens/total_time:.2f} tokens/sec")
    
    console.print("\n基本信息:")
    console.print(basic_info)
    
    # 创建详细性能指标表格
    table = Table(
        title="详细性能指标",
        show_header=True,
        header_style="bold cyan",
        border_style="blue",
        width=100,  # 设置表格总宽度
        pad_edge=False,  # 减少边缘填充
        min_width=80,    # 最小宽度
    )
    
    # 添加列（设置固定列宽）
    table.add_column("并发数", justify="right", style="cyan", width=8)
    table.add_column("RPS", justify="right", width=8)
    table.add_column("平均延迟(秒)", justify="right", width=12)
    table.add_column("P99延迟(秒)", justify="right", width=12)
    table.add_column("平均TPS", justify="right", width=10)
    table.add_column("首Token延迟", justify="right", width=12)
    table.add_column("成功率", justify="right", style="green", width=8)
    
    # 添加数据行
    for row in summary:
        try:
            # 根据成功率设置行样式
            success_rate = float(row[6].rstrip('%'))
            row_style = "green" if success_rate >= 95 else "yellow" if success_rate >= 80 else "red"
            
            table.add_row(
                str(row[0]),                    # 并发数
                f"{float(row[1]):.2f}",        # RPS
                f"{float(row[2]):.3f}",        # 平均延迟
                f"{float(row[3]):.3f}",        # P99延迟
                f"{float(row[4]):.2f}",        # 平均TPS (修复了这里的错误)
                f"{float(row[5]):.3f}",        # 首Token延迟
                row[6],                        # 成功率
                style=row_style
            )
        except ValueError as e:
            console.print(f"警告: 处理行数据时出错: {str(e)}", style="bold red")
            continue
    
    console.print("\n")
    console.print(table)
    
    # 计算和显示最佳性能配置
    try:
        best_rps_idx = np.argmax([float(row[1]) if row[1] != "N/A" else -1 for row in summary])
        best_latency_idx = np.argmin([float(row[2]) if row[2] != "N/A" else float('inf') for row in summary])
        
        perf_info = Table(title="性能最佳配置", show_header=False, box=None, width=60)
        perf_info.add_column("指标", style="cyan", width=15)
        perf_info.add_column("值", style="green", width=45)
        
        perf_info.add_row(
            "最高 RPS",
            f"并发数 {summary[best_rps_idx][0]} ({summary[best_rps_idx][1]} req/sec)"
        )
        perf_info.add_row(
            "最低延迟",
            f"并发数 {summary[best_latency_idx][0]} ({summary[best_latency_idx][2]} 秒)"
        )
        
        console.print("\n")
        console.print(perf_info)
        
        # 性能建议
        recommendations = []
        if best_rps_idx == len(summary) - 1:
            recommendations.append("系统似乎还未达到性能瓶颈，可以尝试更高的并发数")
        elif best_rps_idx == 0:
            recommendations.append("建议尝试降低并发数，当前负载可能过高")
        else:
            recommendations.append(f"最佳并发数范围在 {summary[best_rps_idx][0]} 附近")
        
        success_rate = float(summary[-1][6][:-1])
        if success_rate < 95:
            recommendations.append("在高并发时成功率偏低，建议检查系统资源或降低并发数")
        
        recommend_text = Text("\n性能建议:", style="bold cyan")
        console.print(recommend_text)
        for rec in recommendations:
            console.print(f"• {rec}", style="yellow")
            
    except Exception as e:
        console.print(f"警告: 生成性能分析时出错: {str(e)}", style="bold red")

def main():
    parser = argparse.ArgumentParser(description="Run LLM benchmarks with various configurations")
    parser.add_argument("--llm_url", type=str, required=True, help="URL of the LLM server")
    parser.add_argument("--api_key", type=str, required=False, default="default", help="API key for LLM server")
    parser.add_argument("--use_long_context", action="store_true", help="Use long context prompt pairs instead of short prompts")
    parser.add_argument("--model", type=str, default="deepseek-r1", 
                       help="Model name to use for inference (default: deepseek-r1)")
    args = parser.parse_args()

    all_results = asyncio.run(run_all_benchmarks(args.llm_url, args.api_key, args.model, args.use_long_context))

    # 保存详细结果到文件
    output_dir = f"{os.path.dirname(__file__)}{os.sep}output"
    os.makedirs(output_dir, exist_ok=True)
    
    # 生成带时间戳的文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"{output_dir}{os.sep}benchmark_results_{timestamp}.json"
    
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f"详细测试结果已保存至 {output_file}")
    
    # 打印汇总报告
    print_summary(all_results, args.model, args.use_long_context)

if __name__ == "__main__":
    main()