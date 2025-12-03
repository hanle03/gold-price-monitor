'''
Author: hbh
Date: 2025-06-13 10:49:29
LastEditors: hbh
LastEditTime: 2025-06-13 15:04:03
Description: 浙商/民生金价实时监控: 提供金价数值的实时价监控
             version: 1.0
'''

import logging
import logging.handlers
import requests
import datetime
import os
import matplotlib
# 设置matplotlib使用TkAgg后端
matplotlib.use('TkAgg')
# 设置matplotlib字体支持中文
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
# 用于创建图形用户界面
import tkinter as tk  # 基础模块

# 设置日志记录配置
# 获取当前日期，格式为YYYY-MM-DD
current_date = datetime.datetime.now().strftime('%Y-%m-%d')
LOG_PATH = os.path.join(os.getcwd(), 'log', current_date)  # 默认日志保存路径：当前项目路径/log/日期/

# 创建日志目录（如果不存在）
if not os.path.exists(LOG_PATH):
    os.makedirs(LOG_PATH, exist_ok=True)

# 配置浙商银行日志记录器
zs_logger = logging.getLogger('zs_gold_price')
zs_logger.setLevel(logging.INFO)

# 配置民生银行日志记录器
ms_logger = logging.getLogger('ms_gold_price')
ms_logger.setLevel(logging.INFO)

# 为浙商银行创建日志文件处理器
zs_log_file = os.path.join(LOG_PATH, 'zs_gold_price.log')
zs_file_handler = logging.FileHandler(zs_log_file, encoding='utf-8')

# 为民生银行创建日志文件处理器
ms_log_file = os.path.join(LOG_PATH, 'ms_gold_price.log')
ms_file_handler = logging.FileHandler(ms_log_file, encoding='utf-8')

# 设置CSV格式的日志格式
csv_formatter = logging.Formatter('"%(time)s","%(price)s"')
zs_file_handler.setFormatter(csv_formatter)
ms_file_handler.setFormatter(csv_formatter)

# 添加处理器到日志记录器
zs_logger.addHandler(zs_file_handler)
ms_logger.addHandler(ms_file_handler)

# 为控制台输出保留原始格式（可选）
# console_handler = logging.StreamHandler()
# console_handler.setLevel(logging.INFO)
# console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# console_handler.setFormatter(console_formatter)
# zs_logger.addHandler(console_handler)
# ms_logger.addHandler(console_handler)

# URL(实时金价api)
zsUrl = "https://api.jdjygold.com/gw2/generic/jrm/h5/m/stdLatestPrice?productSku=1961543816"
msUrl = "https://api.jdjygold.com/gw/generic/hj/h5/m/latestPrice"

# 数据存储结构，用于保存一个小时内的数据
# 格式：{"timestamp": [], "price": []}
zs_data_history = {"timestamp": [], "price": []}
ms_data_history = {"timestamp": [], "price": []}
MAX_DATA_POINTS = 3600  # 一个小时的数据点（每秒一个）

def fetch_data():
    try:
        # 检查日期是否变更，如果变更则更新日志路径
        global LOG_PATH, zs_file_handler, ms_file_handler
        
        new_date = datetime.datetime.now().strftime('%Y-%m-%d')
        new_log_path = os.path.join(os.getcwd(), 'log', new_date)
        
        if new_log_path != LOG_PATH:
            # 更新日志路径
            LOG_PATH = new_log_path
            
            # 创建新的日志目录
            if not os.path.exists(LOG_PATH):
                os.makedirs(LOG_PATH, exist_ok=True)
            
            # 移除旧的日志处理器
            zs_logger.removeHandler(zs_file_handler)
            ms_logger.removeHandler(ms_file_handler)
            
            # 创建新的日志文件处理器
            zs_log_file = os.path.join(LOG_PATH, 'zs_gold_price.log')
            zs_file_handler = logging.FileHandler(zs_log_file, encoding='utf-8')
            zs_file_handler.setFormatter(csv_formatter)
            zs_logger.addHandler(zs_file_handler)
            
            ms_log_file = os.path.join(LOG_PATH, 'ms_gold_price.log')
            ms_file_handler = logging.FileHandler(ms_log_file, encoding='utf-8')
            ms_file_handler.setFormatter(csv_formatter)
            ms_logger.addHandler(ms_file_handler)
        
        # 发送 GET 请求给浙商API
        zs_response = requests.get(zsUrl)
        zs_response.raise_for_status()  # 检查请求是否成功
        zs_data = zs_response.json()
        
        # 发送 GET 请求给民生API
        ms_response = requests.get(msUrl)
        ms_response.raise_for_status()  # 检查请求是否成功
        ms_data = ms_response.json()


        # 提取 price 和 time for ZS
        zs_price = zs_data['resultData']['datas']['price']
        zs_time = zs_data['resultData']['datas']['time']
        # 转换时间戳为可读格式
        zs_datetime = datetime.datetime.fromtimestamp(int(zs_time) / 1000).strftime('%Y-%m-%d %H:%M:%S')

        # 提取 price 和 time for MS
        ms_price = ms_data['resultData']['datas']['price']
        ms_time = ms_data['resultData']['datas']['time']
        # 转换时间戳为可读格式
        ms_datetime = datetime.datetime.fromtimestamp(int(ms_time) / 1000).strftime('%Y-%m-%d %H:%M:%S')

        # 更新 GUI - 动态更新
        zs_price_label.config(text=f"浙商 Price: {zs_price}\n时间: {zs_datetime}")
        ms_price_label.config(text=f"民生 Price: {ms_price}\n时间: {ms_datetime}")
        
        # 记录浙商银行金价日志（CSV格式）
        zs_logger.info(f"浙商金价: {zs_price}, 时间: {zs_datetime}", 
                     extra={'price': zs_price, 'time': zs_datetime})
        
        # 记录民生银行金价日志（CSV格式）
        ms_logger.info(f"民生金价: {ms_price}, 时间: {ms_datetime}", 
                     extra={'price': ms_price, 'time': ms_datetime})
        
        # 保存数据到历史记录（浙商）
        zs_data_history["timestamp"].append(datetime.datetime.now())
        zs_data_history["price"].append(float(zs_price))
        
        # 保存数据到历史记录（民生）
        ms_data_history["timestamp"].append(datetime.datetime.now())
        ms_data_history["price"].append(float(ms_price))
        
        # 保持数据量不超过一个小时（3600秒）
        if len(zs_data_history["timestamp"]) > MAX_DATA_POINTS:
            zs_data_history["timestamp"].pop(0)
            zs_data_history["price"].pop(0)
        
        if len(ms_data_history["timestamp"]) > MAX_DATA_POINTS:
            ms_data_history["timestamp"].pop(0)
            ms_data_history["price"].pop(0)
        
        # 更新图表
        update_charts()

    except requests.exceptions.RequestException as e:
        zs_price_label.config(text="ZS 请求出错")
        ms_price_label.config(text="MS 请求出错")
    except ValueError as e:
        zs_price_label.config(text="ZS 解析 JSON 失败")
        ms_price_label.config(text="MS 解析 JSON 失败")
    except KeyError as e:
        zs_price_label.config(text="ZS 数据缺失")
        ms_price_label.config(text="MS 数据缺失")

    # 每隔 1 秒钟调用一次 fetch_data 函数
    root.after(1000, fetch_data)

# 创建绘图函数
canvas_zs = None
canvas_ms = None

# 创建主窗口
root = tk.Tk()
root.title("金价监控")

# 设置窗口最小尺寸（宽度，高度）
root.minsize(width=800, height=600)
# 设置窗口置顶
# root.attributes('-topmost', True)

# 创建顶部框架用于显示当前价格
price_frame = tk.Frame(root)
price_frame.pack(pady=10)

# 初始化时 - 创建标签以显示价格和涨跌幅（浙商）
zs_price_label = tk.Label(price_frame, text="浙商 Price: ", font=(
		"Arial", 16))
zs_price_label.pack(side=tk.LEFT, padx=20)

# 初始化时 -创建标签以显示价格和涨跌幅（民生）
ms_price_label = tk.Label(price_frame, text="民生 Price: ", font=(
		"Arial", 16))
ms_price_label.pack(side=tk.LEFT, padx=20)

# 创建图表框架
chart_frame = tk.Frame(root)
chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# 创建图表标题
zs_chart_title = tk.Label(chart_frame, text="浙商银行金价走势（最近一小时）", font=("Arial", 14))
zs_chart_title.pack(pady=5)

# 创建浙商银行图表区域
zs_chart_area = tk.Frame(chart_frame)
zs_chart_area.pack(fill=tk.BOTH, expand=True, pady=5)

# 创建民生银行图表标题
ms_chart_title = tk.Label(chart_frame, text="民生银行金价走势（最近一小时）", font=("Arial", 14))
ms_chart_title.pack(pady=5)

# 创建民生银行图表区域
ms_chart_area = tk.Frame(chart_frame)
ms_chart_area.pack(fill=tk.BOTH, expand=True, pady=5)

# 创建图表更新函数
def update_charts():
    global canvas_zs, canvas_ms
    
    # 清除旧图表
    for widget in zs_chart_area.winfo_children():
        widget.destroy()
    
    for widget in ms_chart_area.winfo_children():
        widget.destroy()
    
    # 创建浙商银行图表
    if len(zs_data_history["timestamp"]) > 1:
        fig_zs = Figure(figsize=(8, 3), dpi=100)
        ax_zs = fig_zs.add_subplot(111)
        ax_zs.plot(zs_data_history["timestamp"], zs_data_history["price"], color='orange', label='浙商金价')
        ax_zs.set_xlabel('时间')
        ax_zs.set_ylabel('价格 (元)')
        ax_zs.tick_params(axis='x', rotation=45)
        ax_zs.grid(True)
        ax_zs.legend()
        fig_zs.tight_layout()
        
        canvas_zs = FigureCanvasTkAgg(fig_zs, master=zs_chart_area)
        canvas_zs.draw()
        canvas_zs.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    # 创建民生银行图表
    if len(ms_data_history["timestamp"]) > 1:
        fig_ms = Figure(figsize=(8, 3), dpi=100)
        ax_ms = fig_ms.add_subplot(111)
        ax_ms.plot(ms_data_history["timestamp"], ms_data_history["price"], color='orange', label='民生金价')
        ax_ms.set_xlabel('时间')
        ax_ms.set_ylabel('价格 (元)')
        ax_ms.tick_params(axis='x', rotation=45)
        ax_ms.grid(True)
        ax_ms.legend()
        fig_ms.tight_layout()
        
        canvas_ms = FigureCanvasTkAgg(fig_ms, master=ms_chart_area)
        canvas_ms.draw()
        canvas_ms.get_tk_widget().pack(fill=tk.BOTH, expand=True)

# 启动数据获取
fetch_data()

# 启动 GUI 主循环
root.mainloop()