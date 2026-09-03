# Qwen TTS Voiceover Studio

一个面向 Windows 的本地 Qwen3-TTS 配音工作台，提供 VoiceDesign 创建声线、Base Voice Clone 克隆声线、项目化声线管理、批量台词生成、单句返修、WAV/128kbps MP3 转换和成品导出。

## 环境要求

- Windows 10/11
- Python 3.12（当前开发机版本）
- NVIDIA GPU、CUDA 可用的 PyTorch（当前开发机为 PyTorch 2.11.0 + CUDA 13.0）
- 约 10GB 可用磁盘空间存放两个模型快照
- 项目音频转换使用 `imageio-ffmpeg`，无需把 FFmpeg 二进制提交到仓库

## 新电脑安装

```powershell
git clone https://github.com/Lunivia/Qwen-TTS-Voiceover-Studio.git
cd Qwen-TTS-Voiceover-Studio
Set-ExecutionPolicy -Scope Process Bypass
.\setup_windows.ps1
```

模型不会在安装脚本中静默下载。确认 Hugging Face 来源后执行：

```powershell
.venv\Scripts\python.exe scripts\download_models.py
```

详细模型目录、来源和环境变量见 [MODEL_SETUP.md](MODEL_SETUP.md)。如需覆盖默认路径，复制配置模板：

```powershell
copy .env.example .env
```

`.env` 仅供本机使用，不要提交到 Git。

## 启动

双击 `start_studio.cmd`，或运行：

```powershell
.venv\Scripts\python.exe -m studio --host 127.0.0.1 --port 7870
```

工作台地址：<http://127.0.0.1:7870>。另有官方独立 Demo 启动脚本：`start_voice_clone.cmd`（7861）和 `start_voice_design.cmd`（7862）。8GB 显存设备使用互斥锁，两个 1.7B 服务不会同时占用 GPU。

## 项目结构

```text
studio/                 Gradio UI、数据库、音频和模型调度
scripts/                模型下载、Windows 启动与烟测脚本
config/models.psd1      两个独立模型的默认目录与端口
setup_windows.ps1       新电脑初始化
MODEL_SETUP.md          模型恢复说明
requirements-deployment.txt
```

首次运行会创建以下本地数据目录：

- `models/`：两个模型快照，不进入 Git
- `data/`：SQLite、项目状态、声线 Prompt、参考音频和日志，不进入 Git
- `outputs/`：生成及导出音频，不进入 Git

用户上传的克隆参考音频和所有生成音频均属于本地数据，仓库只保存代码、配置模板、启动脚本和文档。

## 测试

不加载模型的基础检查：

```powershell
.venv\Scripts\python.exe -m py_compile studio\*.py scripts\*.py
```

模型已恢复后，可运行 `scripts\smoke_test.py` 和 `scripts\studio_e2e_smoke.py` 做顺序推理验收。
