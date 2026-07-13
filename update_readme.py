# -*- coding: utf-8 -*-
import os
import json
import datetime

# 获取当前脚本所在的绝对路径作为基准路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def generate_sparkline(history):
    """使用纯文本字符生成迷你进度趋势图 (Sparkline)"""
    if not history:
        return "暂无趋势"
    bars = [' ', '▂', '▃', '▄', '▅', '▆', '▇', '█']
    # 限制最多显示最近 20 个数据点
    plot_data = history[-20:]
    sparkline = ""
    for pt in plot_data:
        total = pt.get('total', 1)
        completed = pt.get('completed', 0)
        percent = (completed / total) if total > 0 else 0
        idx = int(round(percent * (len(bars) - 1)))
        idx = max(0, min(len(bars) - 1, idx))
        sparkline += bars[idx]
    return sparkline

def generate_history_list(history):
    """生成最近 5 次的简略提交记录"""
    if not history:
        return "*暂无历史*"
    lines = []
    # 倒序展示最近 5 次
    for pt in reversed(history[-5:]):
        total = pt.get('total', 1)
        completed = pt.get('completed', 0)
        pct = (completed / total * 100) if total > 0 else 0
        time_str = pt.get('time', '')
        lines.append(f"- **{time_str}** : {completed}/{total} ({pct:.1f}%)")
    return "\n".join(lines)

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

    # 4. 生成 Markdown 文本元素
    sparkline_str = generate_sparkline(history)
    history_str = generate_history_list(history)
    
    bar_length = 20
    filled_length = int(round(bar_length * (percent / 100.0))) if total_imgs > 0 else 0
    bar = '█' * filled_length + '░' * (bar_length - filled_length)
    
    if delta > 0:
        delta_str = f" (较上次 **+{delta}** 🟢)"
    elif delta < 0:
        delta_str = f" (较上次 **{delta}** 🔴)"
    else:
        delta_str = " (较上次 **+0** ⚪)"

    # 5. 生成 README.md 模板内容
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

### 📈 标注进度趋势

**进度演进：** `{sparkline_str}`

<details>
<summary>查看最近 5 次变更记录 🔽</summary>

{history_str}
</details>

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
        print("[Success] README.md updated successfully via GitHub Actions (Text mode).")
    except Exception as e:
        print(f"[Error] Failed to write README.md: {e}")

if __name__ == '__main__':
    main()
