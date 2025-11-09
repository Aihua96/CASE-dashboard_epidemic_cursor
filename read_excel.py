# -*- coding: utf-8 -*-
"""
读取香港各区疫情数据Excel文件的前20行数据
并计算每日新增确诊和累计确诊数据
"""
import pandas as pd

# Excel文件路径
excel_file = "香港各区疫情数据_20250322.xlsx"

try:
    # 读取Excel文件
    df = pd.read_excel(excel_file)
    
    # 确保报告日期是日期类型
    df['报告日期'] = pd.to_datetime(df['报告日期'])
    
    # 获取前20行数据
    df_head = df.head(20)
    
    # 显示前20行数据
    print("前20行数据：")
    print("=" * 80)
    print(df_head.to_string(index=True))
    print("=" * 80)
    
    # 显示数据基本信息
    print(f"\n数据总行数: {len(df)}")
    print(f"数据总列数: {len(df.columns)}")
    print(f"\n列名: {list(df.columns)}")
    
    # 计算每日新增确诊和累计确诊数据
    print("\n" + "=" * 80)
    print("每日确诊病例统计（按日期汇总）：")
    print("=" * 80)
    
    # 按日期分组，计算每日所有地区的新增确诊总和
    daily_new_cases = df.groupby('报告日期')['新增确诊'].sum().reset_index()
    daily_new_cases.columns = ['报告日期', '每日新增确诊总数']
    
    # 按日期分组，计算每日所有地区的累计确诊总和
    # 注意：累计确诊应该是所有地区累计确诊的总和
    daily_total_cases = df.groupby('报告日期')['累计确诊'].sum().reset_index()
    daily_total_cases.columns = ['报告日期', '每日累计确诊总数']
    
    # 合并每日新增和累计确诊数据
    daily_statistics = pd.merge(daily_new_cases, daily_total_cases, on='报告日期')
    
    # 显示统计结果
    print(daily_statistics.to_string(index=False))
    
    # 显示汇总信息
    print("\n" + "=" * 80)
    print("汇总统计：")
    print("=" * 80)
    print(f"总新增确诊数: {df['新增确诊'].sum():,}")
    print(f"最大累计确诊数: {df['累计确诊'].max():,}")
    print(f"数据日期范围: {df['报告日期'].min().strftime('%Y-%m-%d')} 至 {df['报告日期'].max().strftime('%Y-%m-%d')}")
    print(f"统计天数: {daily_statistics.shape[0]} 天")
    
except FileNotFoundError:
    print(f"错误：找不到文件 '{excel_file}'")
except Exception as e:
    print(f"读取文件时发生错误: {str(e)}")

