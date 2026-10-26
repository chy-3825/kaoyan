# 构建与题库更新

## 使用已有题库打包

需要 Python 3.10+、JDK 17，以及 Android SDK Build Tools 36 与 Android 平台包。
构建器不是 Gradle 工程，直接调用 `aapt2`、`d8`、`zipalign`、`apksigner`、`javac`、`keytool`。

现有脚本期望以下布局（版本目录名称可不同）：

```text
$YANXI_ANDROID_SDK/
├── tools/36.0.0/             # aapt2、d8、zipalign、apksigner 及对应 lib/
└── platform/android-36/      # android.jar 等平台文件
```

默认路径为 `~/.cache/yanxi-android`；这不是标准 SDK 目录布局。使用已有标准 SDK 时，可在单独目录中建立 `tools/<版本>` 指向 `build-tools/<版本>`、`platform/<版本>` 指向 `platforms/<版本>` 的符号链接，再设置 `YANXI_ANDROID_SDK`。需保持工具附带的 `lib/` 等文件完整。

例如构建线代：

```sh
export YANXI_ANDROID_SDK=/path/to/compatible-sdk-layout
cd apps/linear-algebra
python3 android/build.py
```

其他 App 替换目录即可；APK 和 SHA-256 校验文件输出到各 App 根目录。发布前将四个 APK 复制到仓库根目录的 `apk/`，更新其中的 `SHA256SUMS`，再运行根目录校验；校验会逐文件比较 APK 内嵌 Web 资源与源码。
首次构建会在其 `android/signing/` 创建本地签名私钥与密码。该目录被忽略，原始正式密钥不在仓库中。

## 题库检查

从仓库根目录运行：

```sh
python3 scripts/verify_repository.py
```

该检查验证 JSONL 和运行题库的一致性、题目与答案资源引用、Python 语法，以及当前待跟踪文件的敏感文件名和常见密钥格式。它不证明题目或答案内容正确。

## 更新题库（可选，会写入数据）

构建现有 APK 不需要此步骤。先保存当前数据再重新生成，以免覆盖已人工修改的题目。

数学总库联网更新依赖：

```sh
cd apps/math
python3 -m pip install -r requirements.txt
python3 scripts/build_bank.py
python3 scripts/build_2026_pdfs.py
python3 scripts/build_supplemental.py
```

PDF 脚本还需系统安装 Poppler 的 `pdftotext` 和 `pdftoppm`。网络源可变，重新生成结果不保证与快照相同；2026 裁图已修复。裁图还依赖 `PyMuPDF` 与 `Pillow`（已列入数学 requirements）。

概率、线代的 `scripts/build_bank.py` 根据各自本地题库整理生成运行数据。更新数学总库不会自动同步到两个专题 App。

## 政治 App

政治分区保留原有独立 Web 版本 `app/dist/` 和 Android 版本 `android/web/`，两者功能版本不同，使用 Android 当前题库时以 `android/web/` 为准。构建与环境见 [Android 说明](../apps/politics/android/README.md)；题库重建依赖见其 `requirements.txt` 和根 README。

## 恢复专用工具链

为避免清理本地缓存后丢失原安装步骤，仓库保留了 `scripts/setup_android_sdk.py` 和 `scripts/setup_android_emulator.py`，分别恢复原 Build Tools/平台目录和 Linux x86_64 测试模拟器。需要 Python `requests`，下载目标为 `~/.cache/yanxi-android`，会校验原下载文件的 SHA-1。这些是原有版本的恢复脚本，此次没有重新执行下载测试；下载源和系统兼容性可能发生变化。构建 APK 只需 SDK 脚本，模拟器脚本为可选。

## 重新生成已修复的离线题图

从仓库根目录运行；只重建图片，不覆盖数学已审核元数据：

```sh
python3 -m pip install -r apps/math/requirements.txt
python3 apps/math/scripts/build_2026_pdfs.py --images-only
python3 scripts/sync_math_images.py
python3 -m pip install -r apps/politics/requirements.txt
python3 apps/politics/scripts/build_question_images.py
python3 scripts/verify_repository.py
python3 scripts/test_question_images.py
```

政治配图从已保存 PDF 的内嵌图片无损提取，映射在 `apps/politics/sources/question_images.json`。政治题库重建会重新附加这些图片引用，并检查 Android/Web 两份资源存在。数学图片同步脚本检查题号和路径对应关系，再复制至概率、线代；不会自动修改专题库的题目元数据。

可选的浏览器检查需要 Playwright 与 Chromium 系浏览器：

```sh
python3 -m pip install playwright
python3 -m playwright install chromium
python3 scripts/check_image_ui.py
# 使用现有 Chrome/Edge 时：
BROWSER_EXECUTABLE=/path/to/chrome python3 scripts/check_image_ui.py
```

检查会启动本地临时 HTTP 服务，在 390×844 视口加载各题图及答案图，验证题目显示、放大/关闭，并输出截图目录。这不能代替 Android APK 的原生 WebView 实机检查。修复后的源码与资源需要重新打包，历史 Release APK 不会自动更新。
