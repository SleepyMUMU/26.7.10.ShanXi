# -*- coding: utf-8 -*-
import os
import json
import datetime
import subprocess
import sys

# 图像格式后缀
IMG_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif', '.PNG', '.JPG', '.JPEG', '.BMP')

def run_git_add(files):
    """在本地运行 git add 将文件加入暂存区"""
    try:
        # 检查是否在 git 仓库中
        res = subprocess.run(['git', 'rev-parse', '--is-inside-work-tree'], 
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode == 0:
            for f in files:
                if os.path.exists(f):
                    subprocess.run(['git', 'add', f])
    except Exception as e:
        print(f"[Warning] Failed to run git add: {e}")

def generate_svg(history):
    """使用纯 Python 标准库生成精美的 SVG 进度折线图"""
    # 限制折线图最多只展示最近的 12 个数据点，防止图表过于拥挤
    plot_data = history[-12:] if len(history) > 12 else history
    
    width = 600
    height = 220
    margin_left = 55
    margin_right = 30
    margin_top = 30
    margin_bottom = 45
    
    chart_w = width - margin_left - margin_right
    chart_h = height - margin_top - margin_bottom
    
    svg_parts = []
    # SVG 头部，添加样式以支持暗黑模式自适应
    svg_parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="{height}">'
        '<defs>'
        '  <linearGradient id="grid-grad" x1="0%" y1="0%" x2="0%" y2="100%">'
        '    <stop offset="0%" stop-color="#3b82f6" stop-opacity="0.25" />'
        '    <stop offset="100%" stop-color="#3b82f6" stop-opacity="0.0" />'
        '  </linearGradient>'
        '</defs>'
    )
    
    # 绘制水平网格线和 Y 轴标签 (0%, 20%, 40%, 60%, 80%, 100%)
    y_ticks = [0, 20, 40, 60, 80, 100]
    for tick in y_ticks:
        y_val = margin_top + chart_h - (tick / 100.0) * chart_h
        # 虚线
        svg_parts.append(
            f'  <line x1="{margin_left}" y1="{y_val}" x2="{width - margin_right}" y2="{y_val}" '
            f'stroke="#e5e7eb" stroke-dasharray="4,4" stroke-width="1" />'
        )
        # Y 轴文字 (自适应颜色，使用中性灰以兼容 GitHub 黑暗模式)
        svg_parts.append(
            f'  <text x="{margin_left - 10}" y="{y_val + 4}" font-family="system-ui, -apple-system, sans-serif" '
            f'font-size="10" fill="#6b7280" text-anchor="end">{tick}%</text>'
        )
        
    if not plot_data:
        # 无数据时的占位显示
        svg_parts.append(
            f'  <text x="{width / 2}" y="{height / 2}" font-family="system-ui, -apple-system, sans-serif" '
            f'font-size="14" fill="#9ca3af" text-anchor="middle">暂无标注历史数据</text>'
        )
        svg_parts.append('</svg>')
        return "\n".join(svg_parts)

    # 计算每个数据点的坐标
    points = []
    for idx, pt in enumerate(plot_data):
        completed = pt.get('completed', 0)
        total = pt.get('total', 1)
        percent = (completed / total * 100) if total > 0 else 0
        
        # 计算 X 坐标
        if len(plot_data) == 1:
            x_val = margin_left + chart_w / 2
        else:
            x_val = margin_left + idx * (chart_w / (len(plot_data) - 1))
            
        # 计算 Y 坐标
        y_val = margin_top + chart_h - (percent / 100.0) * chart_h
        
        # 解析时间，截取短格式 MM-DD HH:MM
        time_str = pt.get('time', '')
        try:
            dt = datetime.datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
            short_time = dt.strftime('%m-%d %H:%M')
        except:
            short_time = time_str[:11] # 兜底截取
            
        points.append((x_val, y_val, completed, percent, short_time))

    # 1. 绘制渐变填充区域 (仅在数据点多于1个时绘制)
    if len(points) > 1:
        path_coords = [f"{points[0][0]},{margin_top + chart_h}"]
        for x, y, _, _, _ in points:
            path_coords.append(f"{x},{y}")
        path_coords.append(f"{points[-1][0]},{margin_top + chart_h}")
        path_str = " ".join(path_coords)
        svg_parts.append(f'  <polygon points="{path_str}" fill="url(#grid-grad)" />')

    # 2. 绘制折线
    poly_coords = " ".join([f"{x},{y}" for x, y, _, _, _ in points])
    svg_parts.append(
        f'  <polyline points="{poly_coords}" fill="none" stroke="#3b82f6" stroke-width="2.5" '
        f'stroke-linecap="round" stroke-linejoin="round" />'
    )

    # 3. 绘制数据点小圆圈、数值标注和 X 轴时间标签
    for idx, (x, y, comp_num, pct, short_time) in enumerate(points):
        # 数据点小圆圈
        svg_parts.append(
            f'  <circle cx="{x}" cy="{y}" r="4" fill="#ffffff" stroke="#3b82f6" stroke-width="2" />'
        )
        
        # 数据点数值标注 (如 20.5%)，隔点显示或在最后一个点必定显示，防止过于拥挤
        show_text = True
        if len(points) > 6 and idx % 2 != 0 and idx != len(points) - 1:
            show_text = False # 点太多时，奇数点不标文字，只保留偶数点和最后一个点
            
        if show_text:
            svg_parts.append(
                f'  <text x="{x}" y="{y - 10}" font-family="system-ui, -apple-system, sans-serif" '
                f'font-size="9" font-weight="bold" fill="#2563eb" text-anchor="middle">{pct:.1f}%</text>'
            )
            
        # X 轴时间标签 (倾斜 30 度显示，显得更美观专业)
        svg_parts.append(
            f'  <text x="{x}" y="{margin_top + chart_h + 15}" font-family="system-ui, -apple-system, sans-serif" '
            f'font-size="9" fill="#6b7280" text-anchor="end" '
            f'transform="rotate(-25, {x}, {margin_top + chart_h + 15})">{short_time}</text>'
        )

    svg_parts.append('</svg>')
    return "\n".join(svg_parts)

def main():
    # 1. 扫描当前文件夹中的图片和 JSON 标注
    files = os.listdir('.')
    img_files = []
    json_files = []
    
    for f in files:
        if os.path.isfile(f):
            name, ext = os.path.splitext(f)
            ext_lower = ext.lower()
            if ext_lower in IMG_EXTENSIONS:
                img_files.append(name)
            elif ext_lower == '.json':
                # 排除历史记录文件本身，防止将其算作标注数据
                if name != 'progress_history':
                    json_files.append(name)
                    
    img_set = set(img_files)
    json_set = set(json_files)
    
    total_imgs = len(img_set)
    completed_labels = len(img_set.intersection(json_set))
    remaining_imgs = total_imgs - completed_labels
    
    percent = (completed_labels / total_imgs * 100) if total_imgs > 0 else 0.0

    # 2. 读写 progress_history.json 并计算增量
    history_file = 'progress_history.json'
    history = []
    
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r', encoding='utf-8') as fh:
                history = json.load(fh)
        except Exception as e:
            print(f"[Warning] Failed to load history, resetting: {e}")
            history = []

    # 计算较上一次的增量
    if history:
        last_completed = history[-1].get('completed', 0)
    else:
        last_completed = 0
        
    delta = completed_labels - last_completed
    
    # 仅在有进度变化（delta != 0）或者历史记录为空时，追加新的历史记录节点
    now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if delta != 0 or len(history) == 0:
        history.append({
            "time": now_str,
            "completed": completed_labels,
            "total": total_imgs
        })
        try:
            with open(history_file, 'w', encoding='utf-8') as fh:
                json.dump(history, fh, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Error] Failed to save history: {e}")

    # 3. 生成 SVG 趋势折线图
    svg_content = generate_svg(history)
    svg_file = 'progress_chart.svg'
    try:
        with open(svg_file, 'w', encoding='utf-8') as fs:
            fs.write(svg_content)
    except Exception as e:
        print(f"[Error] Failed to write SVG chart: {e}")

    # 4. 生成 README.md 模板内容
    # 渲染 Markdown 进度条字符 (20格)
    bar_length = 20
    filled_length = int(round(bar_length * (percent / 100.0))) if total_imgs > 0 else 0
    bar = '█' * filled_length + '░' * (bar_length - filled_length)
    
    # 格式化增量展示文字
    if delta > 0:
        delta_str = f" (较上次 **+{delta}** 🟢)"
    elif delta < 0:
        delta_str = f" (较上次 **{delta}** 🔴)"
    else:
        delta_str = " (较上次 **+0** ⚪)"

    readme_content = f"""# 🗺️ 陕西省榆林市标注项目进度 (26.7.10.ShanXi)

> [!NOTE]
> 本仓库仅同步 Labelme 标注所生成的 JSON 数据。图片文件保留在本地不进行上传。进度信息和趋势图表在每次本地提交时自动统计更新。

### 📊 标注状态看板

| 统计项 | 数值 | 占比 / 进度条 / 变化量 |
| :--- | :---: | :--- |
| **总图片数 (Total)** | **{total_imgs}** | `[{'█' * bar_length}]` 100.0% |
| **已标记 (Completed)** | **{completed_labels}** | `[{bar}]` {percent:.1f}%{delta_str} |
| **未标记 (Remaining)** | **{remaining_imgs}** | `[{'░' * bar_length}]` {(100.0 - percent):.1f}% |

**当前总体进度：**
![Progress Badge](https://img.shields.io/badge/Progress-{completed_labels}%20%2F%20{total_imgs}%20({percent:.1f}%25)-blue?style=for-the-badge&logo=github)

### 📈 标注进度趋势折线图
![标注进度趋势](progress_chart.svg)

---
*📅 统计更新时间：{now_str} (本地)*

---
## 👥 多人协作说明
如果您是本项目的新协作者，拉取代码后只需双击运行目录下的 **`setup_hooks.bat`** 即可在本地激活自动统计 Hook。
激活后，您每次进行 `git commit` 时，该脚本均会自动统计您的进度并更新 `README.md` 一并提交，无需手动操作。
"""

    # 5. 写入 README.md
    try:
        with open('README.md', 'w', encoding='utf-8') as fr:
            fr.write(readme_content)
        print("[Success] README.md and SVG chart updated successfully.")
    except Exception as e:
        print(f"[Error] Failed to write README.md: {e}")

    # 6. 如果在 Git 提交流程中，自动将生成的文件加入本次 commit
    run_git_add(['README.md', 'progress_history.json', 'progress_chart.svg'])

if __name__ == '__main__':
    main()
