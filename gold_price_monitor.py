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
        
        # 获取用户输入的期待值
        zs_expect_value = zs_expect_entry.get()  # 期待（卖）
        zs_buy_expect_value = zs_buy_expect_entry.get()  # 期待（买）
        ms_expect_value = ms_expect_entry.get()  # 期待（买）
        ms_buy_expect_value = ms_buy_expect_entry.get()  # 期待（买）
        
        # 设置浙商银行价格显示样式
        try:
            zs_current = float(zs_price)
            zs_expect = float(zs_expect_value) if zs_expect_value else None
            zs_buy_expect = float(zs_buy_expect_value) if zs_buy_expect_value else None
            
            # 检查是否满足任何条件
            if zs_expect is not None and zs_current >= zs_expect:
                # 价格高于"期待（卖）"，使用红色加粗字体
                zs_price_label.config(
                    text=f"浙商 Price: {zs_price}\n时间: {zs_datetime}",
                    font=("Arial", 12, "bold"),
                    fg="red"
                )
            elif zs_buy_expect is not None and zs_buy_expect >= zs_current:
                # "期待（买）"大于当前价格，使用绿色加粗字体
                zs_price_label.config(
                    text=f"浙商 Price: {zs_price}\n时间: {zs_datetime}",
                    font=("Arial", 12, "bold"),
                    fg="green"
                )
            else:
                # 其他情况，使用默认字体
                zs_price_label.config(
                    text=f"浙商 Price: {zs_price}\n时间: {zs_datetime}",
                    font=("Arial", 12),
                    fg="black"
                )
        except ValueError:
            # 输入无效，使用默认字体
            zs_price_label.config(
                text=f"浙商 Price: {zs_price}\n时间: {zs_datetime}",
                font=("Arial", 12),
                fg="black"
            )
        
        # 设置民生银行价格显示样式
        try:
            ms_current = float(ms_price)
            ms_expect = float(ms_expect_value) if ms_expect_value else None
            ms_buy_expect = float(ms_buy_expect_value) if ms_buy_expect_value else None
            
            # 检查是否满足任何条件
            if ms_expect is not None and ms_current >= ms_expect:
                # 价格高于"期待（买）"，使用红色加粗字体
                ms_price_label.config(
                    text=f"民生 Price: {ms_price}\n时间: {ms_datetime}",
                    font=("Arial", 12, "bold"),
                    fg="red"
                )
            elif ms_buy_expect is not None and ms_buy_expect >= ms_current:
                # "期待（买）"大于当前价格，使用绿色加粗字体
                ms_price_label.config(
                    text=f"民生 Price: {ms_price}\n时间: {ms_datetime}",
                    font=("Arial", 12, "bold"),
                    fg="green"
                )
            else:
                # 其他情况，使用默认字体
                ms_price_label.config(
                    text=f"民生 Price: {ms_price}\n时间: {ms_datetime}",
                    font=("Arial", 12),
                    fg="black"
                )
        except ValueError:
            # 输入无效，使用默认字体
            ms_price_label.config(
                text=f"民生 Price: {ms_price}\n时间: {ms_datetime}",
                font=("Arial", 12),
                fg="black"
            )
        
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
root.title("监控")

# 设置窗口最小尺寸（宽度，高度）
root.minsize(width=400, height=200)
# 设置窗口置顶
# root.attributes('-topmost', True)

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

# 初始化时 - 创建标签以显示价格和涨跌幅（浙商）
zs_price_label = tk.Label(price_time_frame, text="浙商 Price: ", font=(
		"Arial", 12))
zs_price_label.pack(side=tk.LEFT, padx=5)

# 为浙商银行添加期待值输入框和标签
zs_expect_label = tk.Label(expect_frame, text="期待（卖）: ", font=(
		"Arial", 12))
zs_expect_label.pack(side=tk.LEFT, padx=5)
zs_expect_entry = tk.Entry(expect_frame, width=8, font=("Arial", 12))
zs_expect_entry.pack(side=tk.LEFT, padx=5)

# 为浙商银行添加"期待（买）"输入框和标签
zs_buy_expect_label = tk.Label(expect_buy_frame, text="期待（买）: ", font=(
		"Arial", 12))
zs_buy_expect_label.pack(side=tk.LEFT, padx=5)
zs_buy_expect_entry = tk.Entry(expect_buy_frame, width=8, font=("Arial", 12))
zs_buy_expect_entry.pack(side=tk.LEFT, padx=5)

# 初始化时 -创建标签以显示价格和涨跌幅（民生）
ms_price_label = tk.Label(price_time_frame, text="民生 Price: ", font=(
		"Arial", 12))
ms_price_label.pack(side=tk.LEFT, padx=5)

# 为民生银行添加期待值输入框和标签
ms_expect_label = tk.Label(expect_frame, text="期待（卖）: ", font=(
		"Arial", 12))
ms_expect_label.pack(side=tk.LEFT, padx=15)
ms_expect_entry = tk.Entry(expect_frame, width=8, font=("Arial", 12))
ms_expect_entry.pack(side=tk.LEFT, padx=5)

# 为民生银行添加"期待（买）"输入框和标签
ms_buy_expect_label = tk.Label(expect_buy_frame, text="期待（买）: ", font=(
		"Arial", 12))
ms_buy_expect_label.pack(side=tk.LEFT, padx=15)
ms_buy_expect_entry = tk.Entry(expect_buy_frame, width=8, font=("Arial", 12))
ms_buy_expect_entry.pack(side=tk.LEFT, padx=5)

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

# 创建图表更新函数
def update_charts():
    global canvas_zs, canvas_ms
    
    # 清除旧图表
    for widget in zs_chart_area.winfo_children():
        widget.destroy()
    
    for widget in ms_chart_area.winfo_children():
        widget.destroy()
    
    # 将matplotlib.dates导入移到函数外部
    from matplotlib import dates as mdates
    
    # 鼠标悬停显示详细信息的函数
    def hover(event, ax, data_history):
        # 清除之前的注释
        if hasattr(ax, 'hover_annotation'):
            ax.hover_annotation.remove()
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
            
            # 清除之前的十字轴线
            if hasattr(ax, 'hover_hline'):
                ax.hover_hline.remove()
                delattr(ax, 'hover_hline')
            if hasattr(ax, 'hover_vline'):
                ax.hover_vline.remove()
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
                ax.hover_hline.remove()
                delattr(ax, 'hover_hline')
            if hasattr(ax, 'hover_vline'):
                ax.hover_vline.remove()
                delattr(ax, 'hover_vline')
            
            ax.figure.canvas.draw_idle()
    
    # 创建浙商银行图表
    if len(zs_data_history["timestamp"]) > 1:
        fig_zs = Figure(figsize=(4, 3), dpi=100)
        ax_zs = fig_zs.add_subplot(111)
        ax_zs.plot(zs_data_history["timestamp"], zs_data_history["price"], color='orange', label='浙商金价')
        ax_zs.set_xlabel('时间')
        ax_zs.set_ylabel('价格 (元)')
        ax_zs.tick_params(axis='x', rotation=45)
        ax_zs.grid(True)
        ax_zs.legend()
        # 调整图表边距，增加右侧边距，实现左对齐效果
        fig_zs.subplots_adjust(left=0.15, right=0.85, top=0.9, bottom=0.4)
        
        canvas_zs = FigureCanvasTkAgg(fig_zs, master=zs_chart_area)
        canvas_zs.draw()
        
        # 添加鼠标悬停事件
        canvas_zs.mpl_connect('motion_notify_event', lambda event: hover(event, ax_zs, zs_data_history))
        
        canvas_zs.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    # 创建民生银行图表
    if len(ms_data_history["timestamp"]) > 1:
        fig_ms = Figure(figsize=(4, 3), dpi=100)
        ax_ms = fig_ms.add_subplot(111)
        ax_ms.plot(ms_data_history["timestamp"], ms_data_history["price"], color='orange', label='民生金价')
        ax_ms.set_xlabel('时间')
        ax_ms.set_ylabel('价格 (元)')
        ax_ms.tick_params(axis='x', rotation=45)
        ax_ms.grid(True)
        ax_ms.legend()
        # 调整图表边距，增加右侧边距，实现左对齐效果
        fig_ms.subplots_adjust(left=0.15, right=0.85, top=0.9, bottom=0.4)
        
        canvas_ms = FigureCanvasTkAgg(fig_ms, master=ms_chart_area)
        canvas_ms.draw()
        
        # 添加鼠标悬停事件
        canvas_ms.mpl_connect('motion_notify_event', lambda event: hover(event, ax_ms, ms_data_history))
        
        canvas_ms.get_tk_widget().pack(fill=tk.BOTH, expand=True)

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