# -*- coding: utf-8 -*-
import os
import json
import datetime
import time

# 获取当前脚本所在的绝对路径作为基准路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def generate_svg(history):
    """使用纯 Python 标准库生成精美的 SVG 进度折线图"""
    # 限制折线图最多只展示最近 of 12 个数据点，防止图表过于拥挤
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
        # Y 轴文字
        svg_parts.append(
            f'  <text x="{margin_left - 10}" y="{y_val + 4}" font-family="system-ui, -apple-system, sans-serif" '
            f'font-size="10" fill="#6b7280" text-anchor="end">{tick}%</text>'
        )
        
    if not plot_data:
        svg_parts.append(
            f'  <text x="{width / 2}" y="{height / 2}" font-family="system-ui, -apple-system, sans-serif" '
            f'font-size="14" fill="#9ca3af" text-anchor="middle">暂无标注历史数据</text>'
        )
        svg_parts.append('</svg>')
        return "\n".join(svg_parts)

    points = []
    for idx, pt in enumerate(plot_data):
        completed = pt.get('completed', 0)
        total = pt.get('total', 1)
        percent = (completed / total * 100) if total > 0 else 0
        
        if len(plot_data) == 1:
            x_val = margin_left + chart_w / 2
        else:
            x_val = margin_left + idx * (chart_w / (len(plot_data) - 1))
            
        y_val = margin_top + chart_h - (percent / 100.0) * chart_h
        
        time_str = pt.get('time', '')
        try:
            dt = datetime.datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
            short_time = dt.strftime('%m-%d %H:%M')
        except:
            short_time = time_str[:11]
            
        points.append((x_val, y_val, completed, percent, short_time))

    if len(points) > 1:
        path_coords = [f"{points[0][0]},{margin_top + chart_h}"]
        for x, y, _, _, _ in points:
            path_coords.append(f"{x},{y}")
        path_coords.append(f"{points[-1][0]},{margin_top + chart_h}")
        path_str = " ".join(path_coords)
        svg_parts.append(f'  <polygon points="{path_str}" fill="url(#grid-grad)" />')

    poly_coords = " ".join([f"{x},{y}" for x, y, _, _, _ in points])
    svg_parts.append(
        f'  <polyline points="{poly_coords}" fill="none" stroke="#3b82f6" stroke-width="2.5" '
        f'stroke-linecap="round" stroke-linejoin="round" />'
    )

    for idx, (x, y, comp_num, pct, short_time) in enumerate(points):
        svg_parts.append(
            f'  <circle cx="{x}" cy="{y}" r="4" fill="#ffffff" stroke="#3b82f6" stroke-width="2" />'
        )
        
        show_text = True
        if len(points) > 6 and idx % 2 != 0 and idx != len(points) - 1:
            show_text = False
            
        if show_text:
            svg_parts.append(
                f'  <text x="{x}" y="{y - 10}" font-family="system-ui, -apple-system, sans-serif" '
                f'font-size="9" font-weight="bold" fill="#2563eb" text-anchor="middle">{pct:.1f}%</text>'
            )
            
        svg_parts.append(
            f'  <text x="{x}" y="{margin_top + chart_h + 15}" font-family="system-ui, -apple-system, sans-serif" '
            f'font-size="9" fill="#6b7280" text-anchor="end" '
            f'transform="rotate(-25, {x}, {margin_top + chart_h + 15})">{short_time}</text>'
        )

    svg_parts.append('</svg>')
    return "\n".join(svg_parts)


def main():
    # 1. 从 config.json 读取总数
    config_file = os.path.join(BASE_DIR, 'config.json')
    total_imgs = 0
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                total_imgs = config.get('total_images', 0)
        except Exception as e:
            print(f"[Error] Failed to read config.json: {e}")
            
    # 2. 扫描当前文件夹中的 JSON 标注文件数量作为完成数
    files = os.listdir(BASE_DIR)
    json_files = []
    
    for f in files:
        full_path = os.path.join(BASE_DIR, f)
        if os.path.isfile(full_path):
            name, ext = os.path.splitext(f)
            if ext.lower() == '.json' and name not in ('progress_history', 'config'):
                json_files.append(name)
                
    completed_labels = len(set(json_files))
    remaining_imgs = max(0, total_imgs - completed_labels)
    
    percent = (completed_labels / total_imgs * 100) if total_imgs > 0 else 0.0

    # 3. 读写 progress_history.json 并计算增量
    history_file = os.path.join(BASE_DIR, 'progress_history.json')
    history = []
    
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r', encoding='utf-8') as fh:
                history = json.load(fh)
        except Exception as e:
            print(f"[Warning] Failed to load history, resetting: {e}")
            history = []

    # 计算较上一次的增量
    last_completed = history[-1].get('completed', 0) if history else 0
    delta = completed_labels - last_completed
    
    # 追加新的历史记录节点
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

    # 4. 生成 SVG 趋势折线图并保存到本地（供 Actions 上传到幽灵分支）
    svg_content = generate_svg(history)
    svg_file = os.path.join(BASE_DIR, 'progress_chart.svg')
    try:
        with open(svg_file, 'w', encoding='utf-8') as fs:
            fs.write(svg_content)
    except Exception as e:
        print(f"[Error] Failed to write SVG chart: {e}")

    # 5. 生成 README.md 模板内容
    bar_length = 20
    filled_length = int(round(bar_length * (percent / 100.0))) if total_imgs > 0 else 0
    bar = '█' * filled_length + '░' * (bar_length - filled_length)
    
    if delta > 0:
        delta_str = f" (较上次 **+{delta}** 🟢)"
    elif delta < 0:
        delta_str = f" (较上次 **{delta}** 🔴)"
    else:
        delta_str = " (较上次 **+0** ⚪)"

    # 加入时间戳，确保 GitHub 图像防缓存
    timestamp = int(time.time())

    readme_content = f"""# 🗺️ 陕西省榆林市标注项目进度 (26.7.10.ShanXi)

> [!NOTE]
> 本仓库仅同步 Labelme 标注所生成的 JSON 数据。图片总数在 `config.json` 中配置，GitHub Actions 会在每次推送时自动统计当前的 JSON 文件数量并更新此看板。

### 📊 标注状态看板

| 统计项 | 数值 | 占比 / 进度条 / 变化量 |
| :--- | :---: | :--- |
| **总图片数 (Total)** | **{total_imgs}** | `[{'█' * bar_length}]` 100.0% |
| **已标记 (Completed)** | **{completed_labels}** | `[{bar}]` {percent:.1f}%{delta_str} |
| **未标记 (Remaining)** | **{remaining_imgs}** | `[{'░' * bar_length}]` {(100.0 - percent):.1f}% |

**当前总体进度：**
![Progress Badge](https://img.shields.io/badge/Progress-{completed_labels}%20%2F%20{total_imgs}%20({percent:.1f}%25)-blue?style=for-the-badge&logo=github)

### 📈 标注进度趋势折线图
![标注进度趋势](https://github.com/SleepyMUMU/26.7.10.ShanXi/blob/assets/progress_chart.svg?raw=true&v={timestamp})

---
*📅 统计更新时间：{now_str} (UTC)*

---
## 👥 多人协作说明
本项目已全面接入 **GitHub Actions**。作为协作者，您**无需**在本地运行任何脚本或配置任何 Git 钩子。
只要您正常将 `.json` 文件 `git push` 到仓库，云端就会自动计算并更新此 README 文件和趋势图！
（如果您向本地库新增了待标注图片，请顺手修改 `config.json` 中的 `total_images` 数值即可。）

---
<div align="center">
  <sub>🤖 Automated by <b>Antigravity AI</b></sub>
</div>
"""

    # 6. 写入 README.md
    readme_path = os.path.join(BASE_DIR, 'README.md')
    try:
        with open(readme_path, 'w', encoding='utf-8') as fr:
            fr.write(readme_content)
        print("[Success] README.md updated successfully via GitHub Actions (Ghost branch mode).")
    except Exception as e:
        print(f"[Error] Failed to write README.md: {e}")

if __name__ == '__main__':
    main()
