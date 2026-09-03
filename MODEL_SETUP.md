# Qwen3-TTS 模型恢复说明

本项目使用两个官方 Hugging Face 模型，权重不进入 Git：

| 功能 | 模型 ID | 默认目录 | 本机约占用 |
| --- | --- | --- | ---: |
| 创建声线 / VoiceDesign | `Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign` | `models/voice_design_1.7b` | 4.21 GB |
| 语音克隆 / Base | `Qwen/Qwen3-TTS-12Hz-1.7B-Base` | `models/voice_clone_1.7b` | 4.23 GB |

在项目根目录执行：

```powershell
.venv\Scripts\python.exe scripts\download_models.py
```

脚本使用 `huggingface_hub.snapshot_download`，不会把 Token 写入项目。需要认证时请临时设置 `HF_TOKEN` 环境变量。也可以把模型放到其他目录，并在 `.env` 或启动进程环境中设置：

```text
QWEN_TTS_GENERATION_MODEL_PATH=D:\Models\voice_design_1.7b
QWEN_TTS_CLONE_MODEL_PATH=D:\Models\voice_clone_1.7b
```

模型目录必须包含 `model.safetensors` 以及同一快照中的配置和 tokenizer 文件。8GB 显存设备上，工作台通过进程内锁串行加载和释放两个模型，不能让两个独立 Demo 同时常驻。
