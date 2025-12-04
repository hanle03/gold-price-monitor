#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
黄金价格监控工具
功能：
1. 实时监控浙商银行和民生银行的黄金价格
2. 支持设置价格预警（期待买/卖价格）
3. 以图表形式展示价格走势（最近一小时数据）
4. 自动记录价格日志到CSV文件
5. 支持窗口大小调整和响应式布局

使用说明：
1. 运行程序后，自动开始监控黄金价格
2. 在"期待（卖）"输入框中设置期望卖出价格，当价格达到或超过时，价格标签变为红色加粗
3. 在"期待（买）"输入框中设置期望买入价格，当价格低于或等于时，价格标签变为绿色加粗
4. 图表显示最近一小时的价格走势，支持鼠标悬停查看具体价格和时间
5. 日志文件保存在log目录下，按日期分类存储
"""

import logging
# import logging.handlers
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

# CSV格式的日志格式
csv_formatter = logging.Formatter('"%(time)s","%(price)s"')

# 日志配置函数，用于创建和配置日志记录器
def configure_logger(bank_name, log_path):
    """
    配置日志记录器
    参数:
        bank_name: 银行名称，用于生成日志记录器名称和文件名
        log_path: 日志文件保存路径
    返回:
        tuple: (logger, file_handler)，配置好的日志记录器和文件处理器
    """
    # 创建日志记录器
    logger_name = f'{bank_name}_gold_price'
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    
    # 创建日志文件处理器
    log_file = os.path.join(log_path, f'{bank_name}_gold_price.log')
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    
    # 设置CSV格式的日志格式
    file_handler.setFormatter(csv_formatter)
    
    # 添加处理器到日志记录器
    logger.addHandler(file_handler)
    
    return logger, file_handler

# --------------------------
# 日志配置
# --------------------------
# 初始化日志配置
# 获取当前日期，格式为YYYY-MM-DD
current_date = datetime.datetime.now().strftime('%Y-%m-%d')
LOG_PATH = os.path.join(os.getcwd(), 'log', current_date)  # 默认日志保存路径：当前项目路径/log/日期/

# 创建日志目录（如果不存在）
if not os.path.exists(LOG_PATH):
    os.makedirs(LOG_PATH, exist_ok=True)

# 配置浙商银行和民生银行的日志记录器
zs_logger, zs_file_handler = configure_logger('zs', LOG_PATH)
ms_logger, ms_file_handler = configure_logger('ms', LOG_PATH)

# 为控制台输出保留原始格式（可选）
# console_handler = logging.StreamHandler()
# console_handler.setLevel(logging.INFO)
# console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# console_handler.setFormatter(console_formatter)
# zs_logger.addHandler(console_handler)
# ms_logger.addHandler(console_handler)

# --------------------------
# 配置参数
# --------------------------
# URL(实时金价api)
zsUrl = "https://api.jdjygold.com/gw2/generic/jrm/h5/m/stdLatestPrice?productSku=1961543816"  # 浙商银行API URL
msUrl = "https://api.jdjygold.com/gw/generic/hj/h5/m/latestPrice"  # 民生银行API URL

# 数据存储结构，用于保存一个小时内的数据
# 格式：{"timestamp": [], "price": []}
zs_data_history = {"timestamp": [], "price": []}  # 浙商银行价格历史
ms_data_history = {"timestamp": [], "price": []}  # 民生银行价格历史
# MAX_DATA_POINTS = 3600  # 一个小时的数据点（每秒一个）
MAX_DATA_POINTS = 240

# 从日志文件读取数据的函数
def read_data_from_log(file_path):
    """
    从日志文件中读取数据，确保返回的数据量不超过MAX_DATA_POINTS
    参数:
        file_path: 日志文件路径
    返回:
        dict: 包含timestamp和price的字典
    """
    data = {"timestamp": [], "price": []}
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        return data
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        # 解析每一行数据
        parsed_data = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 解析CSV格式数据
            parts = line.split('"')
            if len(parts) < 5:
                continue
            
            time_str = parts[1]
            price_str = parts[3]
            
            try:
                # 转换时间字符串为datetime对象
                timestamp = datetime.datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                # 转换价格字符串为float
                price = float(price_str)
                
                parsed_data.append((timestamp, price))
            except ValueError:
                # 跳过格式不正确的行
                continue
        
        # 按时间排序（确保最新的数据在最后）
        parsed_data.sort(key=lambda x: x[0])
        
        # 确保数据量不超过MAX_DATA_POINTS，只保留最新的
        if len(parsed_data) > MAX_DATA_POINTS:
            parsed_data = parsed_data[-MAX_DATA_POINTS:]
        
        # 分离timestamp和price
        for timestamp, price in parsed_data:
            data["timestamp"].append(timestamp)
            data["price"].append(price)
    except Exception as e:
        print(f"读取日志文件 {file_path} 出错: {e}")
    
    return data

# 检查和更新日志路径的函数
def check_and_update_log_path():
    """
    检查日期是否变更，如果变更则更新日志路径
    """
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

# 获取银行数据的函数
def fetch_bank_data(url, bank_name):
    """
    从API获取银行数据
    参数:
        url: API URL
        bank_name: 银行名称（用于日志）
    返回:
        tuple: (price, datetime_str) 价格和时间字符串
    """
    response = requests.get(url)
    response.raise_for_status()  # 检查请求是否成功
    data = response.json()
    
    # 提取价格和时间
    price = data['resultData']['datas']['price']
    time = data['resultData']['datas']['time']
    # 转换时间戳为可读格式
    datetime_str = datetime.datetime.fromtimestamp(int(time) / 1000).strftime('%Y-%m-%d %H:%M:%S')
    
    return price, datetime_str

# 保存数据到历史记录的函数
def save_data_to_history(data_history, price, timestamp=None):
    """
    保存数据到历史记录
    参数:
        data_history: 历史数据字典
        price: 价格
        timestamp: 时间戳（默认使用当前时间）
    """
    if timestamp is None:
        timestamp = datetime.datetime.now()
    
    data_history["timestamp"].append(timestamp)
    data_history["price"].append(float(price))
    
    # 保持数据量不超过一个小时（3600秒）
    if len(data_history["timestamp"]) > MAX_DATA_POINTS:
        data_history["timestamp"].pop(0)
        data_history["price"].pop(0)

# 添加全局变量用于跟踪通知状态
notification_sent = {
    'zs_sell': False,
    'zs_buy': False,
    'ms_sell': False,
    'ms_buy': False
}

# 显示置顶弹窗通知的函数
def show_notification(title, message):
    """
    显示置顶弹窗通知
    参数:
        title: 通知标题
        message: 通知内容
    """
    # 创建弹窗窗口
    popup = tk.Toplevel(root)
    popup.title(title)
    popup.geometry("300x150")
    
    # 设置窗口置顶
    popup.attributes('-topmost', True)
    
    # 添加通知内容
    label = tk.Label(popup, text=message, font=('Arial', 12), padx=20, pady=20)
    label.pack()
    
    # 添加关闭按钮
    close_button = tk.Button(popup, text="关闭", command=popup.destroy, font=('Arial', 10))
    close_button.pack(pady=10)
    
    # 设置弹窗在1小时后自动关闭
    popup.after(600000, popup.destroy)

# 更新价格标签样式的函数
def update_price_label(price_label, bank_name, current_price, datetime_str, expect_value, buy_expect_value):
    """
    更新价格标签的样式并显示弹窗通知
    参数:
        price_label: 价格标签组件
        bank_name: 银行名称（用于显示和通知）
        current_price: 当前价格
        datetime_str: 时间字符串
        expect_value: 期待（卖）值
        buy_expect_value: 期待（买）值
    """
    global notification_sent
    
    try:
        current = float(current_price)
        expect = float(expect_value) if expect_value else None
        buy_expect = float(buy_expect_value) if buy_expect_value else None
        
        # 获取银行缩写，用于通知状态跟踪
        bank_abbr = 'zs' if bank_name == '浙商' else 'ms'
        
        # 检查是否满足任何条件
        if expect is not None and current >= expect:
            # 价格高于"期待（卖）"，使用红色加粗字体
            price_label.config(
                text=f"{bank_name} Price: {current_price}\n时间: {datetime_str}",
                font=("Arial", 12, "bold"),
                fg="red"
            )
            
            # 显示弹窗通知（仅当第一次触发时）
            if not notification_sent[f'{bank_abbr}_sell']:
                message = f"当前价格: {current_price}元\n已达到或超过期待（卖）价格: {expect}元\n时间: {datetime_str}"
                show_notification(f"{bank_name}金价提醒", message)
                notification_sent[f'{bank_abbr}_sell'] = True
        elif buy_expect is not None and buy_expect >= current:
            # "期待（买）"大于当前价格，使用绿色加粗字体
            price_label.config(
                text=f"{bank_name} Price: {current_price}\n时间: {datetime_str}",
                font=("Arial", 12, "bold"),
                fg="green"
            )
            
            # 显示弹窗通知（仅当第一次触发时）
            if not notification_sent[f'{bank_abbr}_buy']:
                message = f"当前价格: {current_price}元\n已低于或等于期待（买）价格: {buy_expect}元\n时间: {datetime_str}"
                show_notification(f"{bank_name}金价提醒", message)
                notification_sent[f'{bank_abbr}_buy'] = True
        else:
            # 其他情况，使用默认字体
            price_label.config(
                text=f"{bank_name} Price: {current_price}\n时间: {datetime_str}",
                font=("Arial", 12),
                fg="black"
            )
            
            # 重置通知状态，以便下次触发时再次通知
            notification_sent[f'{bank_abbr}_sell'] = False
            notification_sent[f'{bank_abbr}_buy'] = False
    except ValueError:
        # 输入无效，使用默认字体
        price_label.config(
            text=f"{bank_name} Price: {current_price}\n时间: {datetime_str}",
            font=("Arial", 12),
            fg="black"
        )

# 主数据获取函数
def fetch_data():
    try:
        # 检查日期是否变更，如果变更则更新日志路径
        check_and_update_log_path()
        
        # 获取浙商银行数据
        zs_price, zs_datetime = fetch_bank_data(zsUrl, "浙商")
        
        # 获取民生银行数据
        ms_price, ms_datetime = fetch_bank_data(msUrl, "民生")

        # 更新 GUI - 动态更新
        
        # 获取用户输入的期待值
        zs_expect_value = zs_expect_entry.get()  # 期待（卖）
        zs_buy_expect_value = zs_buy_expect_entry.get()  # 期待（买）
        ms_expect_value = ms_expect_entry.get()  # 期待（买）
        ms_buy_expect_value = ms_buy_expect_entry.get()  # 期待（买）
        
        # 使用统一函数更新浙商银行价格标签
        update_price_label(zs_price_label, "浙商", zs_price, zs_datetime, zs_expect_value, zs_buy_expect_value)
        
        # 使用统一函数更新民生银行价格标签
        update_price_label(ms_price_label, "民生", ms_price, ms_datetime, ms_expect_value, ms_buy_expect_value)
        
        # 记录浙商银行金价日志（CSV格式）
        zs_logger.info(f"浙商金价: {zs_price}, 时间: {zs_datetime}", 
                     extra={'price': zs_price, 'time': zs_datetime})
        
        # 记录民生银行金价日志（CSV格式）
        ms_logger.info(f"民生金价: {ms_price}, 时间: {ms_datetime}", 
                     extra={'price': ms_price, 'time': ms_datetime})
        
        # 保存数据到历史记录（浙商）
        save_data_to_history(zs_data_history, zs_price)
        
        # 保存数据到历史记录（民生）
        save_data_to_history(ms_data_history, ms_price)
        
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

    # 每隔 15 秒钟调用一次 fetch_data 函数
    root.after(15000, fetch_data)

# --------------------------
# 图表变量初始化
# --------------------------
# 创建绘图函数
canvas_zs = None  # 浙商银行图表画布
canvas_ms = None  # 民生银行图表画布
fig_zs = None     # 浙商银行图表Figure
ax_zs = None      # 浙商银行图表Axis
fig_ms = None     # 民生银行图表Figure
ax_ms = None      # 民生银行图表Axis

# --------------------------
# 主窗口和UI组件初始化
# --------------------------
# 创建主窗口
root = tk.Tk()
root.title("监控")

# 设置窗口最小尺寸（宽度，高度）
root.minsize(width=400, height=200)
# 设置窗口置顶
# root.attributes('-topmost', True)

# UI组件创建函数
def create_bank_ui(bank_name, display_name, price_time_frame, expect_frame, expect_buy_frame, padx=5):
    """
    创建银行相关的UI组件
    参数:
        bank_name: 银行名称（用于变量命名）
        display_name: 银行显示名称（用于标签显示）
        price_time_frame: 价格和时间标签所在的框架
        expect_frame: 期待（卖）输入框所在的框架
        expect_buy_frame: 期待（买）输入框所在的框架
        padx: 组件之间的水平间距
    返回:
        dict: 包含创建的标签和输入框的字典
    """
    # 创建价格标签
    price_label = tk.Label(price_time_frame, text=f"{display_name} Price: ", font=(
            "Arial", 12))
    price_label.pack(side=tk.LEFT, padx=padx)
    
    # 创建期待（卖）输入框和标签
    expect_label = tk.Label(expect_frame, text="期待（卖）: ", font=(
            "Arial", 12))
    expect_label.pack(side=tk.LEFT, padx=padx)
    expect_entry = tk.Entry(expect_frame, width=8, font=(
            "Arial", 12))
    expect_entry.pack(side=tk.LEFT, padx=padx)
    
    # 创建期待（买）输入框和标签
    buy_expect_label = tk.Label(expect_buy_frame, text="期待（买）: ", font=(
            "Arial", 12))
    buy_expect_label.pack(side=tk.LEFT, padx=padx)
    buy_expect_entry = tk.Entry(expect_buy_frame, width=8, font=(
            "Arial", 12))
    buy_expect_entry.pack(side=tk.LEFT, padx=padx)
    
    return {
        'price_label': price_label,
        'expect_label': expect_label,
        'expect_entry': expect_entry,
        'buy_expect_label': buy_expect_label,
        'buy_expect_entry': buy_expect_entry
    }

# 创建顶部框架用于显示当前价格
price_frame = tk.Frame(root)
price_frame.pack(pady=10, fill=tk.X)

# 为价格时间行创建子框架
price_time_frame = tk.Frame(price_frame)
price_time_frame.pack(fill=tk.X, pady=2)

# 为期待值（卖）创建子框架
expect_frame = tk.Frame(price_frame)
expect_frame.pack(fill=tk.X, pady=2)

# 为期待值（买）创建子框架
expect_buy_frame = tk.Frame(price_frame)
expect_buy_frame.pack(fill=tk.X, pady=2)

# 创建浙商银行UI组件
zs_ui = create_bank_ui('zs', '浙商', price_time_frame, expect_frame, expect_buy_frame, padx=5)

# 创建民生银行UI组件（民生银行的padx需要调整以与浙商银行对齐）
ms_ui = create_bank_ui('ms', '民生', price_time_frame, expect_frame, expect_buy_frame, padx=15)

# 提取UI组件变量，以便在其他函数中使用
zs_price_label = zs_ui['price_label']
zs_expect_entry = zs_ui['expect_entry']
zs_buy_expect_entry = zs_ui['buy_expect_entry']

ms_price_label = ms_ui['price_label']
ms_expect_entry = ms_ui['expect_entry']
ms_buy_expect_entry = ms_ui['buy_expect_entry']

# 创建滚动条框架
scrollable_frame = tk.Frame(root)
scrollable_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# 添加垂直滚动条
v_scrollbar = tk.Scrollbar(scrollable_frame, orient=tk.VERTICAL)
v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# 添加水平滚动条
h_scrollbar = tk.Scrollbar(scrollable_frame, orient=tk.HORIZONTAL)
h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

# 创建画布用于放置图表内容
canvas = tk.Canvas(scrollable_frame, yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set, highlightthickness=0)
canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# 配置滚动条与画布的关联
v_scrollbar.config(command=canvas.yview)
h_scrollbar.config(command=canvas.xview)

# 创建图表框架，放置在画布上
chart_frame = tk.Frame(canvas)
canvas.create_window((0, 0), window=chart_frame, anchor=tk.NW)

# 监听图表框架大小变化，更新滚动区域
def update_scrollregion(event):
    canvas.configure(scrollregion=canvas.bbox("all"))

chart_frame.bind("<Configure>", update_scrollregion)

# 创建图表标题
zs_chart_title = tk.Label(chart_frame, text="浙商走势（最近一小时）", font=("Arial", 12))
zs_chart_title.pack(pady=5)

# 创建浙商银行图表区域
zs_chart_area = tk.Frame(chart_frame)
zs_chart_area.pack(fill=tk.BOTH, expand=True, pady=5)

# 创建民生银行图表标题
ms_chart_title = tk.Label(chart_frame, text="民生走势（最近一小时）", font=("Arial", 12))
ms_chart_title.pack(pady=5)

# 创建民生银行图表区域
ms_chart_area = tk.Frame(chart_frame)
ms_chart_area.pack(fill=tk.BOTH, expand=True, pady=5)

# 将matplotlib.dates导入移到函数外部
from matplotlib import dates as mdates

# 鼠标悬停显示详细信息的函数
def hover(event, ax, data_history):
    # 清除之前的注释
    if hasattr(ax, 'hover_annotation'):
        # 使用更可靠的方式移除注释
        try:
            # 尝试使用remove方法
            ax.hover_annotation.remove()
        except NotImplementedError:
            # 如果remove方法不可用，尝试其他方式
            pass
        # 无论如何都要删除属性
        delattr(ax, 'hover_annotation')
    
    # 检查鼠标是否在轴上且event.xdata有效
    if event.inaxes == ax and event.xdata is not None:
        # 获取x坐标（时间）的索引
        x_data = data_history["timestamp"]
        y_data = data_history["price"]
        
        if len(x_data) == 0:
            return
        
        # 将datetime对象转换为matplotlib内部的数值表示
        x_data_num = mdates.date2num(x_data)
        
        # 找到最接近鼠标位置的点
        idx = (np.abs(x_data_num - event.xdata)).argmin()
        
        # 获取该点的信息
        timestamp = x_data[idx]
        price = y_data[idx]
        
        # 创建显示文本
        text = f"时间: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n价格: {price:.2f}元"
        
        # 获取图表的x轴范围
        xlim = ax.get_xlim()
        # 计算图表中心位置
        x_center = (xlim[0] + xlim[1]) / 2
        
        # 根据鼠标位置在图表左侧或右侧来调整标签位置
        if event.xdata < x_center:
            # 鼠标在左侧，标签在右边
            ax.hover_annotation = ax.annotate(
                text, 
                xy=(event.xdata, event.ydata), 
                xytext=(10, 10),  # 标签位置相对于数据点的偏移（向右上）
                textcoords='offset points',
                verticalalignment='bottom',
                horizontalalignment='left',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.9),
                zorder=1000,  # 设置高zorder确保在最上层
                arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=.5')
            )
        else:
            # 鼠标在右侧，标签在左边
            ax.hover_annotation = ax.annotate(
                text, 
                xy=(event.xdata, event.ydata), 
                xytext=(-10, 10),  # 标签位置相对于数据点的偏移（向左上）
                textcoords='offset points',
                verticalalignment='bottom',
                horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.9),
                zorder=1000,  # 设置高zorder确保在最上层
                arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=-.5')
            )
        
        # 清除之前的十字线
        if hasattr(ax, 'hover_hline'):
            try:
                ax.hover_hline.remove()
            except NotImplementedError:
                pass
            delattr(ax, 'hover_hline')
        if hasattr(ax, 'hover_vline'):
            try:
                ax.hover_vline.remove()
            except NotImplementedError:
                pass
            delattr(ax, 'hover_vline')
        
        # 绘制十字轴线以突出当前坐标点
        # 水平轴线（y=price）
        ax.hover_hline = ax.axhline(y=price, color='gray', linestyle='--', linewidth=0.5, zorder=999)
        # 垂直轴线（x=timestamp）
        ax.hover_vline = ax.axvline(x=timestamp, color='gray', linestyle='--', linewidth=0.5, zorder=999)
        
        ax.figure.canvas.draw_idle()
    else:
        # 鼠标移出图表区域，移除十字线
        if hasattr(ax, 'hover_hline'):
            try:
                ax.hover_hline.remove()
            except NotImplementedError:
                pass
            delattr(ax, 'hover_hline')
        if hasattr(ax, 'hover_vline'):
            try:
                ax.hover_vline.remove()
            except NotImplementedError:
                pass
            delattr(ax, 'hover_vline')
        
        ax.figure.canvas.draw_idle()

# 创建和更新银行图表的通用函数
def update_bank_chart(bank_name, display_name, data_history, chart_area, canvas_var, fig_var, ax_var):
    """
    创建和更新银行图表
    参数:
        bank_name: 银行名称（用于变量命名）
        display_name: 银行显示名称（用于图表标签）
        data_history: 银行价格历史数据
        chart_area: 图表区域组件
        canvas_var: 图表画布变量（全局变量）
        fig_var: 图表Figure变量（全局变量）
        ax_var: 图表Axis变量（全局变量）
    返回:
        tuple: 更新后的(canvas, fig, ax)变量
    """
    if len(data_history["timestamp"]) <= 1:
        return canvas_var, fig_var, ax_var
    
    # 如果图表不存在，则创建新图表
    if fig_var is None or ax_var is None:
        fig_var = Figure(figsize=(4, 3), dpi=100)
        ax_var = fig_var.add_subplot(111)
        ax_var.set_xlabel('时间')
        ax_var.set_ylabel('价格 (元)')
        ax_var.tick_params(axis='x', rotation=45)
        ax_var.grid(True)
        # 调整图表边距，增加右侧边距，实现左对齐效果
        fig_var.subplots_adjust(left=0.15, right=0.85, top=0.9, bottom=0.4)
        
        canvas_var = FigureCanvasTkAgg(fig_var, master=chart_area)
        canvas_var.draw()
        
        # 添加鼠标悬停事件
        canvas_var.mpl_connect('motion_notify_event', lambda event: hover(event, ax_var, data_history))
        
        canvas_var.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    else:
        # 清除旧的图表内容
        ax_var.clear()
        ax_var.set_xlabel('时间')
        ax_var.set_ylabel('价格 (元)')
        ax_var.tick_params(axis='x', rotation=45)
        ax_var.grid(True)
    
    # 更新图表数据
    ax_var.plot(data_history["timestamp"], data_history["price"], color='orange', label=f'{display_name}金价')
    ax_var.legend()
    canvas_var.draw_idle()
    
    return canvas_var, fig_var, ax_var

# 创建图表更新函数
def update_charts():
    global canvas_zs, canvas_ms, fig_zs, ax_zs, fig_ms, ax_ms
    
    # 更新浙商银行图表
    canvas_zs, fig_zs, ax_zs = update_bank_chart(
        'zs', '浙商', zs_data_history, zs_chart_area, canvas_zs, fig_zs, ax_zs
    )
    
    # 更新民生银行图表
    canvas_ms, fig_ms, ax_ms = update_bank_chart(
        'ms', '民生', ms_data_history, ms_chart_area, canvas_ms, fig_ms, ax_ms
    )

# --------------------------
# 程序初始化和启动
# --------------------------
# 从日志文件初始化数据
# 读取浙商银行日志数据
zs_log_path = os.path.join(LOG_PATH, 'zs_gold_price.log')
zs_data = read_data_from_log(zs_log_path)
if zs_data["timestamp"]:
    zs_data_history = zs_data

# 读取民生银行日志数据
ms_log_path = os.path.join(LOG_PATH, 'ms_gold_price.log')
ms_data = read_data_from_log(ms_log_path)
if ms_data["timestamp"]:
    ms_data_history = ms_data

# 更新图表以显示初始化数据
update_charts()

# 启动数据获取
fetch_data()

# 启动 GUI 主循环
root.mainloop()