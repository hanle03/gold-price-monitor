# 黄金价格监控工具打包说明

## 打包指令
```bash
pyinstaller --onefile --windowed --name "监控" --add-data "xm3954.mp3;." gold_price_monitor.py
```

## 指令说明
- `--onefile`: 生成单个可执行文件
- `--windowed`: 不显示命令行窗口（Windows下为GUI应用）
- `--name "实时金价"`: 设置生成的可执行文件名称
- `--add-data "xm3954.mp3;."`: 将MP3文件添加到打包中，Windows下使用分号分隔路径

## 注意事项
1. 确保已安装所有依赖：`pip install -r requirements.txt`
2. 当前项目中没有Windows格式的icon.ico文件，所以移除了图标参数
3. 如果需要添加图标，需准备.ico格式的图标文件，并添加`--icon=your_icon.ico`参数
4. 打包后的可执行文件会在dist目录中生成