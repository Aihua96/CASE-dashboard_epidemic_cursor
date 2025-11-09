# -*- coding: utf-8 -*-
"""
Flask应用：香港各区疫情数据可视化大屏
"""
from flask import Flask, render_template, jsonify, send_file
from flask_cors import CORS
import pandas as pd
from datetime import datetime
import os
import json

app = Flask(__name__)
# 允许跨域请求
CORS(app)

# Excel文件路径
EXCEL_FILE = "香港各区疫情数据_20250322.xlsx"
HONGKONG_JSON = "hongkong.json"

# 区域名称映射（中文 -> 英文）
REGION_NAME_MAP = {
    '中西区': 'Central and Western',
    '湾仔区': 'Wan Chai',
    '东区': 'Eastern',
    '南区': 'Southern',
    '油尖旺区': 'Yau Tsim Mong',
    '深水埗区': 'Sham Shui Po',
    '九龙城区': 'Kowloon City',
    '黄大仙区': 'Wong Tai Sin',
    '观塘区': 'Kwun Tong',
    '葵青区': 'Kwai Tsing',
    '荃湾区': 'Tsuen Wan',
    '屯门区': 'Tuen Mun',
    '元朗区': 'Yuen Long',
    '北区': 'North',
    '大埔区': 'Tai Po',
    '沙田区': 'Sha Tin',
    '西贡区': 'Sai Kung',
    '离岛区': 'Islands'
}

def load_data():
    """加载Excel数据"""
    if not os.path.exists(EXCEL_FILE):
        raise FileNotFoundError(f"找不到文件: {EXCEL_FILE}")
    df = pd.read_excel(EXCEL_FILE)
    df['报告日期'] = pd.to_datetime(df['报告日期'])
    return df

@app.route('/')
def index():
    """首页"""
    return render_template('index.html')

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/daily_statistics')
def daily_statistics():
    """API: 每日新增确诊和累计确诊数据"""
    try:
        df = load_data()
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    # 按日期分组，计算每日所有地区的新增确诊总和
    daily_new_cases = df.groupby('报告日期')['新增确诊'].sum().reset_index()
    daily_total_cases = df.groupby('报告日期')['累计确诊'].sum().reset_index()
    
    # 计算增长率（每日新增相对于前一日累计的增长率）
    daily_statistics = pd.merge(daily_new_cases, daily_total_cases, on='报告日期')
    daily_statistics['增长率'] = (daily_statistics['新增确诊'] / daily_statistics['累计确诊'].shift(1) * 100).fillna(0)
    
    # 转换为JSON格式
    dates = daily_statistics['报告日期'].dt.strftime('%Y-%m-%d').tolist()
    new_cases = daily_statistics['新增确诊'].tolist()
    total_cases = daily_statistics['累计确诊'].tolist()
    growth_rates = daily_statistics['增长率'].round(2).tolist()
    
    return jsonify({
        'dates': dates,
        'new_cases': new_cases,
        'total_cases': total_cases,
        'growth_rates': growth_rates
    })

@app.route('/api/region_statistics')
def region_statistics():
    """API: 各区域累计确诊统计"""
    try:
        df = load_data()
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    # 获取最新日期的数据
    latest_date = df['报告日期'].max()
    latest_data = df[df['报告日期'] == latest_date]
    
    # 按区域汇总累计确诊
    region_stats = latest_data.groupby('地区名称')['累计确诊'].sum().reset_index()
    region_stats = region_stats.sort_values('累计确诊', ascending=False)
    
    # 转换为JSON格式
    regions = region_stats['地区名称'].tolist()
    cases = region_stats['累计确诊'].tolist()
    
    return jsonify({
        'regions': regions,
        'cases': cases
    })

@app.route('/api/region_daily')
def region_daily():
    """API: 各区域每日新增确诊数据（用于热力图）"""
    try:
        df = load_data()
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    # 按日期和区域分组
    region_daily = df.groupby(['报告日期', '地区名称'])['新增确诊'].sum().reset_index()
    
    # 转换为热力图需要的格式
    dates = sorted(df['报告日期'].unique())
    regions = sorted(df['地区名称'].unique())
    
    # 构建热力图数据 [区域, 日期, 数值]
    heatmap_data = []
    for date in dates:
        date_str = pd.to_datetime(date).strftime('%Y-%m-%d')
        date_data = region_daily[region_daily['报告日期'] == date]
        for region in regions:
            region_value = date_data[date_data['地区名称'] == region]['新增确诊'].sum()
            if pd.isna(region_value):
                region_value = 0
            heatmap_data.append([region, date_str, int(region_value)])
    
    return jsonify({
        'dates': [pd.to_datetime(d).strftime('%Y-%m-%d') for d in dates],
        'regions': regions,
        'data': heatmap_data
    })

@app.route('/api/hongkong_map')
def hongkong_map():
    """API: 提供香港地图JSON数据"""
    try:
        if not os.path.exists(HONGKONG_JSON):
            return jsonify({'error': '地图文件不存在'}), 404
        return send_file(HONGKONG_JSON, mimetype='application/json')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/map_data')
def map_data():
    """API: 地图数据（各区域累计确诊分布）"""
    try:
        df = load_data()
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    # 获取最新日期的数据
    latest_date = df['报告日期'].max()
    latest_data = df[df['报告日期'] == latest_date]
    
    # 按区域汇总累计确诊
    region_stats = latest_data.groupby('地区名称')['累计确诊'].sum().reset_index()
    
    # 转换为地图数据格式（包含中文和英文名称）
    map_data_list = []
    for _, row in region_stats.iterrows():
        chinese_name = row['地区名称']
        english_name = REGION_NAME_MAP.get(chinese_name, chinese_name)
        map_data_list.append({
            'name': english_name,  # 使用英文名称匹配地图JSON
            'chineseName': chinese_name,  # 保留中文名称用于显示
            'value': int(row['累计确诊'])
        })
    
    return jsonify({
        'data': map_data_list,
        'nameMap': REGION_NAME_MAP
    })

@app.route('/api/summary')
def summary():
    """API: 汇总统计信息"""
    try:
        df = load_data()
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    # 计算汇总数据
    total_new_cases = int(df['新增确诊'].sum())
    max_total_cases = int(df['累计确诊'].max())
    date_range_start = df['报告日期'].min().strftime('%Y-%m-%d')
    date_range_end = df['报告日期'].max().strftime('%Y-%m-%d')
    total_days = len(df['报告日期'].unique())
    
    # 最新日期的数据
    latest_date = df['报告日期'].max()
    latest_new_cases = int(df[df['报告日期'] == latest_date]['新增确诊'].sum())
    latest_total_cases = int(df[df['报告日期'] == latest_date]['累计确诊'].sum())
    
    return jsonify({
        'total_new_cases': total_new_cases,
        'max_total_cases': max_total_cases,
        'date_range_start': date_range_start,
        'date_range_end': date_range_end,
        'total_days': total_days,
        'latest_date': latest_date.strftime('%Y-%m-%d'),
        'latest_new_cases': latest_new_cases,
        'latest_total_cases': latest_total_cases
    })

if __name__ == '__main__':
    # 使用3000端口，避免与系统服务冲突
    app.run(debug=True, host='127.0.0.1', port=3000)

