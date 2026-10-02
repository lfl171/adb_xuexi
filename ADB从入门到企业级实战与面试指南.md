# ADB 从入门到企业级实战与面试全解

> 一篇写给「想真正搞懂 ADB」的 Android 工程师、测试开发、DevOps 与面试候选人的长文。
> 从 `adb devices` 到千台设备农场，从命令速查到面试官真正想听的答案。

---

## 目录

- [0. 写在前面：为什么 ADB 值得单独写一篇长文](#0-写在前面为什么-adb-值得单独写一篇长文)
- [1. 原理篇：ADB 到底是什么](#1-原理篇adb-到底是什么)
  - [1.1 三端架构](#11-三端架构)
  - [1.2 一次 `adb shell ls` 究竟走了哪些路](#12-一次-adb-shell-ls-究竟走了哪些路)
  - [1.3 端口、协议与传输层](#13-端口协议与传输层)
  - [1.4 鉴权：RSA 密钥与 unauthorized](#14-鉴权rsa-密钥与-unauthorized)
- [2. 入门篇：环境搭建与第一个命令](#2-入门篇环境搭建与第一个命令)
  - [2.1 安装 platform-tools](#21-安装-platform-tools)
  - [2.2 设备状态全解](#22-设备状态全解)
  - [2.3 目标设备的四种指定方式](#23-目标设备的四种指定方式)
- [3. 基础篇：日常 90% 场景的命令](#3-基础篇日常-90-场景的命令)
  - [3.1 设备与连接](#31-设备与连接)
  - [3.2 应用安装与卸载](#32-应用安装与卸载)
  - [3.3 文件传输](#33-文件传输)
  - [3.4 Shell 与进程](#34-shell-与进程)
  - [3.5 应用与组件操作](#35-应用与组件操作)
  - [3.6 日志 logcat](#36-日志-logcat)
  - [3.7 模拟输入](#37-模拟输入)
  - [3.8 屏幕与录制](#38-屏幕与录制)
- [4. 进阶篇：让它变快、变稳、变自动](#4-进阶篇让它变快变稳变自动)
  - [4.1 `adb shell` vs `adb exec-out`：二进制安全的关键](#41-adb-shell-vs-adb-exec-out二进制安全的关键)
  - [4.2 端口转发：`forward` 与 `reverse`](#42-端口转发forward-与-reverse)
  - [4.3 无线调试：从 TCP 到 Android 11 配对](#43-无线调试从-tcp-到-android-11-配对)
  - [4.4 性能与诊断工具箱](#44-性能与诊断工具箱)
  - [4.5 自动化测试接口](#45-自动化测试接口)
  - [4.6 UI 自动化底层：uiautomator dump 与 getevent](#46-ui-自动化底层uiautomator-dump-与-getevent)
- [5. 企业级篇：把 ADB 变成生产力基础设施](#5-企业级篇把-adb-变成生产力基础设施)
  - [5.1 企业里 ADB 的三类落地场景](#51-企业里-adb-的三类落地场景)
  - [5.2 CI/CD 集成：从 Docker 到设备农场](#52-cicd-集成从-docker-到设备农场)
  - [5.3 设备高可用：断线自愈守护进程](#53-设备高可用断线自愈守护进程)
  - [5.4 并发与隔离：一台机器带多少台设备](#54-并发与隔离一台机器带多少台设备)
  - [5.5 安全与合规：别让 ADB 成为后门](#55-安全与合规别让-adb-成为后门)
  - [5.6 可观测性：设备指标与日志采集](#56-可观测性设备指标与日志采集)
  - [5.7 企业级踩坑清单](#57-企业级踩坑清单)
- [6. 面试篇：分层题库 + 参考答案](#6-面试篇分层题库--参考答案)
  - [6.1 初级（1-3 年）](#61-初级1-3-年)
  - [6.2 中级（3-5 年）](#62-中级3-5-年)
  - [6.3 高级 / 架构设计](#63-高级--架构设计)
  - [6.4 场景设计题（重点）](#64-场景设计题重点)
  - [6.5 面试官视角：什么样的回答加分](#65-面试官视角什么样的回答加分)
- [7. 故障排查手册](#7-故障排查手册)
- [8. 附录：命令速查](#8-附录命令速查)

---

## 0. 写在前面：为什么 ADB 值得单独写一篇长文

很多人对 ADB 的认知停留在「背几个命令」：

```bash
adb install app.apk
adb logcat
adb shell
```

但现实中，ADB 是真机自动化测试、性能采集、CI/CD 流水线、设备农场、企业移动设备管理的**唯一物理入口**。它一头连着你的开发机，一头连着几百台跑着不同 Android 版本的真机。你在业务上遇到的那些"玄学问题"——安装失败、日志抓不到、自动化脚本偶发卡死、CI 上设备掉线——几乎都能追到 ADB 这一层。

这篇文章分三条线：

| 层次 | 关注点 | 读者 |
| --- | --- | --- |
| 教学线 | 原理 + 命令 + 为什么这么设计 | 入门者、转岗同学 |
| 实战线 | 自动化、CI、性能、稳定性治理 | 测试开发、DevOps |
| 面试线 | 高频题 + 场景题 + 加分点 | 求职者、面试官 |

**阅读建议**：原理篇（第 1 章）不要跳。面试拉开差距的地方，几乎全在第 1 章和第 5 章。

---

## 1. 原理篇：ADB 到底是什么

ADB = **A**ndroid **D**ebug **B**ridge（Android 调试桥）。名字里三个词都是重点：它是给**调试**用的、它是一个**桥**（不是直接连接）。

### 1.1 三端架构

ADB 由三个组件构成，理解这三者，90% 的"玄学问题"都能解释清楚：

```
┌──────────────────────────┐
│      开发机 / CI Runner   │
│                          │
│  ① adb client            │  你敲的每一条 adb 命令
│     ($ adb install xx)   │  都是一个独立进程，用完即退
│            │             │
│            │ TCP 5037    │  本地回环，走 loopback
│            ▼             │
│  ② adb server            │  一个后台常驻进程，
│     (常驻守护进程)         │  全机器唯一，管理所有设备连接
│            │             │
└────────────┼─────────────┘
             │
             │ ③ 传输层：USB 端点 bulk transfer
             │    或 TCP 5555+（无线调试）
             ▼
┌──────────────────────────┐
│         Android 设备      │
│   ④ adbd (adbd daemon)   │  以 shell 用户身份运行的 native 守护进程
│            │             │
│            ▼             │
│      shell / app_process │
└──────────────────────────┘
```

三个角色各自的职责：

| 组件 | 位置 | 生命周期 | 关键事实 |
| --- | --- | --- | --- |
| **adb client** | 开发机 | 每条命令一个进程 | 只负责把你的命令翻译成请求发给 server |
| **adb server** | 开发机 | 常驻后台，全局唯一 | 监听 **5037**，负责设备扫描、连接管理、请求路由 |
| **adbd** | 设备上 | 常驻，随设备启动 | 监听 USB 端点；`adb tcpip` 后额外监听 **5555** |

**这就是为什么 `adb kill-server` 能解决一大批问题**：因为它杀掉并重建的是那个"中间人"，而不是你的命令。

**这也是为什么"adb 版本不匹配"是高危问题**：client 和 server 之间是有协议的，版本不一致时 server 会被强制重启，正在跑的自动化脚本全部断链。你肯定见过这句：

```console
adb server version (41) doesn't match this client (39); killing...
```

### 1.2 一次 `adb shell ls` 究竟走了哪些路

面试里能把这条链路说清楚的人，通常对 ADB 是真懂的：

1. `adb` 可执行文件启动，作为 **client** 读取环境变量、参数，尝试连接 `127.0.0.1:5037`。
2. 如果 server 没起来，client 会 **fork 一个 server**（`adb -L tcp:5037 fork-server server`）再连。
3. server 维护一张"设备表"，每台设备一个**唯一 transport**（USB 上的 `serialno:devpath` 或 TCP 的 ip:port）。
4. server 根据 `-s/-d/-e/-t` 选出目标设备，打开一条 **stream（本地 socket）**。
5. server 向该设备的 adbd 发送 `shell:ls` 这样的服务请求，adbd 在设备上 fork 出 `sh -c ls`。
6. adbd 把 stdout/stderr 通过 transport 回传，server 再回传给 client，client 写到你的终端。
7. 命令结束，client 退出；**adb server 继续活着**，等下一次命令。

⚠️ 关键细节（面试高频）：`adb shell` 在设备端会分配 **PTY**，所以：

- 输出里的 `\n` 会被翻译成 `\r\n`；
- 二进制数据会被破坏；
- 退出码（exit code）在旧版本上会丢失。

这直接引出第 4.1 节的 `exec-out`。

### 1.3 端口、协议与传输层

| 端口 | 归属 | 说明 |
| --- | --- | --- |
| **5037** | 开发机 adb server | 固定端口，可通过 `ANDROID_ADB_SERVER_PORT` 或 `adb -P` 改 |
| **5555 ~ 5585** | 设备 adbd (TCP) | `adb tcpip 5555` 后设备监听；模拟器从 5554/5555 成对使用 |
| **5554** | 模拟器控制台 | `telnet localhost 5554`，需 `.emulator_console_auth_token` |

**USB 传输细节**（高级加分项）：USB 上并没有什么"ADB 协议"，ADB 复用了 USB 的 bulk 端点。adbd 在设备侧创建一个 gadget 接口（class `0xFF`，subclass `0x42`，protocol `0x01`——这串魔术数字就是 ADB 接口的标识），开发机侧 `usbhost` 通过 libusb/WinUSB 打开这个接口，两端在 bulk in/out 端点上跑自有的帧协议。所以：

- Windows 上需要厂商 USB 驱动或 WinUSB（Zadig 替换驱动就是这个原因）；
- Linux 上需要 udev 规则给 USB 设备读写权限，否则出现 `no permissions`；
- USB 自动挂起（autosuspend）会让设备在空闲后掉线，这是设备农场的经典敌人。

**传输层可替换**（这是 ADB 设计最优雅的地方）：transport 抽象出 `read/write/close` 语义，于是同一套上层逻辑既能跑 USB，也能跑 TCP、也能跑模拟器的 qemu pipe。你看到的"无线调试"，本质只是加了一种 transport。

### 1.4 鉴权：RSA 密钥与 unauthorized

从 Android 4.2.2 起，ADB 引入公钥鉴权，防的是"插上 USB 就能读你数据"：

1. 开发机首次连接时，若找不到 `~/.android/adbkey`，**自动生成一对 RSA 2048 密钥**（`adbkey` / `adbkey.pub`）。
2. adbd 收到连接后，若设备尚未信任该公钥，`adb devices` 显示 `unauthorized`。
3. 手机上弹出「允许 USB 调试吗？」，勾选"一律允许"后，公钥被写入设备的 `/data/misc/adb/adb_keys`。
4. 之后每次连接走签名挑战-应答，不再弹窗。

企业环境里的对应问题：

- **CI Runner 上必须固化 `adbkey`**，否则每次跑流水线都要人点手机授权，等于不可自动化；
- 密钥丢失/轮换后需要重新授权，要写进运维手册；
- `ADB_VENDOR_KEYS` 环境变量可为 OEM 场景附加厂商密钥；
- 生产设备可通过 Device Owner 策略直接**禁用 USB 调试**（见 5.5）。

---

## 2. 入门篇：环境搭建与第一个命令

### 2.1 安装 platform-tools

ADB 属于 `platform-tools`，**独立于 Android Studio**，随 SDK 单独发版：

- 官方地址：`https://developer.android.com/tools/releases/platform-tools`
- 解压后把目录加入 `PATH`。
- Windows 可用 `scoop install adb` / `choco install adb`；macOS 用 `brew install --cask android-platform-tools`；Linux 用发行版包管理器（注意版本可能偏老）。

**版本检查与统一（企业第一课）**：

```bash
adb version
# Android Debug Bridge version 1.0.41
# Version 35.0.2-android-tools
```

> **铁律：全团队 / 全流水线必须用同一个 adb 版本。**
> 设备农场里出现 `device offline` 潮、脚本随机失败，第一嫌疑永远是 CI 镜像里的 adb 被升级到了和测试机不兼容的版本。

Linux 上还需要 udev 规则（否则 `no permissions`）：

```bash
# /etc/udev/rules.d/51-android.rules
SUBSYSTEM=="usb", ATTR{idVendor}=="18d1", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="2717", MODE="0666", GROUP="plugdev"  # 小米
SUBSYSTEM=="usb", ATTR{idVendor}=="12d1", MODE="0666", GROUP="plugdev"  # 华为
# 用 lsusb 查你自己的厂商 ID
sudo udevadm control --reload-rules && sudo udevadm trigger
```

**关闭 USB 自动挂起（设备农场必做）**：

```bash
# 内核启动参数
usbcore.autosuspend=-1
# 或运行时对具体设备
echo -1 | sudo tee /sys/bus/usb/devices/1-1/power/autosuspend
```

### 2.2 设备状态全解

```bash
adb devices -l
```

输出的每一列/每种状态都要认识：

```console
List of devices attached
b4d9f0a1        device product:raven model:Pixel_6_pro device:raven transport_id:3
10.0.0.5:5555   device product:... transport_id:4
emulator-5554   offline
FA7A11A02345    unauthorized
1a2b3c4d        no permissions (user in plugdev group; are your udev rules wrong?)
```

| 状态 | 含义 | 典型原因 |
| --- | --- | --- |
| `device` | 正常可用 | — |
| `offline` | 端口在，链路断 | 设备休眠、USB 挂起、adb 版本不一致、server 卡死 |
| `unauthorized` | 未授权 | 手机没点"允许"，或 adbkey 变了 |
| `no permissions` | Linux 权限不足 | udev 规则缺失，或当前用户不在 plugdev 组 |
| `bootloader` / `recovery` / `sideload` | 特殊模式 | `adb reboot bootloader` 等进入 |
| `no permissions (verify udev rules)` | 同上 | — |

> `-l` 参数（list）会额外输出 `product/model/device/transport_id`，是区分"同型号多台设备"的关键。

### 2.3 目标设备的四种指定方式

```bash
adb -d shell ...        # 只选唯一的 USB 设备（USB device）
adb -e shell ...        # 只选唯一的模拟器（emulator）
adb -s b4d9f0a1 ...     # 按序列号选（最常用，自动化必用）
adb -t 3 ...            # 按 transport_id 选（同序列号多链路时救命）
```

**为什么自动化脚本必须显式指定 `-s`**：默认行为是"只有一台设备时才自动选中"，一旦有两台，所有命令都会报错：

```console
adb: more than one device/emulator
```

而设备农场里"两台"是常态。

---

## 3. 基础篇：日常 90% 场景的命令

### 3.1 设备与连接

```bash
adb start-server                 # 启动 server
adb kill-server                  # 杀掉 server（万能第一步）
adb devices -l                   # 列设备
adb get-state                    # 打印 device / offline / bootloader
adb get-serialno                 # 打印序列号
adb wait-for-device              # 阻塞直到有设备就绪（CI 必备）
adb wait-for-usb-device
adb wait-for-local-device
adb reconnect                    # 重连（先 offline 的）
adb reconnect offline            # 只重连 offline 的
adb reboot                       # 重启
adb reboot bootloader
adb reboot recovery
adb sideload ota.zip             # sideload 刷机包
adb root                         # 以 root 重启 adbd（仅 userdebug/eng）
adb unroot
adb remount                      # 把 /system 等挂成可写（需 verity 可关）
adb disable-verity / enable-verity
```

**`adb wait-for-device` 的真实语义**（面试易错点）：它只等"设备被 adbd 报告为 device 状态"，**不代表系统已经启动完成、不代表可以安装应用**。CI 里正确的等待姿势是组合拳：

```bash
adb wait-for-device
# 等到 boot 完成
until [ "$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" = "1" ]; do sleep 2; done
# 等到包管理器可用（这一步最容易被忽略）
until adb shell pm path android >/dev/null 2>&1; do sleep 2; done
# 解锁屏幕、常亮
adb shell input keyevent KEYCODE_WAKEUP
adb shell input keyevent 82
adb shell svc power stayon true
```

### 3.2 应用安装与卸载

```bash
adb install app.apk                       # 基础安装
adb install -r app.apk                    # -r replace 覆盖安装（保留数据）
adb install -t app.apk                    # -t 允许 test-only 包
adb install -d app.apk                    # -d 允许降级（downgrade）
adb install -g app.apk                    # -g 安装时授予全部运行时权限（自动化神器）
adb install --abi arm64-v8a app.apk       # 指定 ABI（split APK 场景）
adb install-multiple base.apk split_x.apk # 安装 split APK
adb install-multi-package a.apk b.apk     # 一次装多个不同包

adb uninstall com.example.app
adb uninstall -k com.example.app          # -k 保留数据与缓存
adb shell pm uninstall --user 0 com.oem.bloatware   # 免 root 卸载预装（当前用户）
adb shell pm clear com.example.app        # 清数据（等价于"恢复出厂"单应用）
```

**`-g` 为什么重要**：Android 6.0+ 运行时权限让每次装完都要弹窗授权，UI 自动化脚本会被权限弹窗打断。`-g` 在安装时直接授予，是"让脚本稳定下来"最便宜的一招。

**安装失败速查**：

| 报错 | 含义与处理 |
| --- | --- |
| `INSTALL_FAILED_ALREADY_EXISTS` | 已存在，用 `-r` |
| `INSTALL_FAILED_VERSION_DOWNGRADE` | 降级被拒，用 `-d` |
| `INSTALL_FAILED_UPDATE_INCOMPATIBLE` | 签名不一致（debug/release 混装），先 `uninstall` |
| `INSTALL_FAILED_INSUFFICIENT_STORAGE` | 空间不足，`adb shell df -h /data` |
| `INSTALL_FAILED_USER_RESTRICTED` | 厂商限制（MIUI 等），需在开发者选项里允许 USB 安装 |
| `INSTALL_PARSE_FAILED_NO_CERTIFICATES` | APK 未签名或被篡改 |
| `Failure [INSTALL_FAILED_TEST_ONLY]` | 用 `-t` |
| `adb: failed to finalize session` | USB 不稳/线材差/存储满，换线换口 |

### 3.3 文件传输

```bash
adb push local.txt /sdcard/Download/
adb push ./assets/ /sdcard/app_assets/       # 目录递归
adb pull /sdcard/log.txt ./logs/
adb pull /data/anr ./anr_dump/               # 需 root 或 debuggable
adb shell ls -l /sdcard/
adb shell df -h                              # 磁盘占用
adb shell du -sh /data/data/com.x            # 目录大小（需权限）
```

**拷不出应用私有数据怎么办**（高频实战难题，见 5.5 与 6.2）：

```bash
# 方式一：debuggable 应用用 run-as
adb exec-out run-as com.example.app cat databases/app.db > app.db

# 方式二：Android 10+ 用 backup/restore（需 allowBackup 或 debug 构建）
adb shell bmgr ...

# 方式三：userdebug 设备 adb root 后直接 pull
adb root && adb pull /data/data/com.example.app/ ./pkg/

# 方式四：应用内加"导出到 /sdcard"的调试入口（最工程化的做法）
```

### 3.4 Shell 与进程

```bash
adb shell                                   # 交互式（会分配 PTY）
adb shell "cmd1 && cmd2"
adb shell 'cmd; echo "exit=$?"'             # 稳妥获取远端退出码
adb shell ps -A                             # 全量进程
adb shell pidof com.example.app             # 取 pid（Android 7+）
adb shell top -n 1 -b | head -20            # 一次性 top
adb shell kill -9 <pid>
adb shell getprop                           # 全部属性
adb shell getprop ro.build.version.sdk      # API level
adb shell getprop ro.product.cpu.abi
adb shell setprop log.tag.MyTag VERBOSE     # 运行时调日志级别
adb shell dumpsys | head                    # 所有系统服务 dump
adb shell id                                # 当前身份（shell / root）
adb shell getenforce                        # SELinux 状态
```

**`adb shell` 引号陷阱**：外层引号由你的本地 shell 解释，容易和远端 shell 打架。

```bash
# ❌ 本地 shell 会先展开 $PID
adb shell echo $PID
# ✅ 单引号保护，交给远端
adb shell 'echo $PID'
# ✅ 或转义
adb shell "echo \$PID"
```

### 3.5 应用与组件操作

```bash
# ---- 包管理（pm 与 cmd package 等价，后者更"现代"）----
adb shell pm list packages                  # 全部
adb shell pm list packages -3               # 仅第三方
adb shell pm list packages -s               # 仅系统
adb shell pm list packages -d               # 仅被禁用的
adb shell pm list packages -u               # 含已卸载但保留数据的
adb shell pm list packages -f com.example.app   # 显示 apk 路径
adb shell pm path com.example.app
adb shell cmd package list packages
adb shell dumpsys package com.example.app | grep -E "versionName|versionCode|firstInstallTime"

adb shell pm grant com.example.app android.permission.CAMERA
adb shell pm revoke com.example.app android.permission.CAMERA
adb shell pm reset-permissions
adb shell pm disable-user --user 0 com.oem.app
adb shell pm enable com.oem.app

adb shell appops get com.example.app
adb shell appops set com.example.app SYSTEM_ALERT_WINDOW allow

# ---- Activity / Service / Broadcast ----
adb shell am start -n com.example.app/.MainActivity
adb shell am start -a android.intent.action.VIEW -d "https://example.com"
adb shell am start -W -n com.example.app/.MainActivity   # -W 打印耗时（冷启动测量）
adb shell am start -S -n com.example.app/.MainActivity   # -S 先 force-stop 再启（测冷启）
adb shell am force-stop com.example.app
adb shell am kill com.example.app                        # 温和杀（保留后台栈）
adb shell am broadcast -a com.example.ACTION --es key value --ei num 1
adb shell am set-debug-app -w com.example.app            # 启动即等调试器
adb shell am clear-debug-app
adb shell dumpsys activity activities | grep -E "mResumedActivity|mFocusedApp"
adb shell dumpsys window | grep -E "mCurrentFocus|mFocusedApp"
```

**冷启动耗时怎么读**（性能测试高频）：

```bash
adb shell am force-stop com.example.app
adb shell am start -W -n com.example.app/.MainActivity
# TotalTime: 412      应用自身启动耗时（最常被作为指标）
# WaitTime:  430      含系统调度（AMS 视角的总等待）
# ThisTime:  412      最后一个 Activity 的启动耗时
```

测量规范：连续测 **10 次以上取中位数/P90**，去掉首次（首次有 IO 缓存与 JIT/AOT 噪声），并固定 `wm size/density`、关闭动画、恒定电量与温度。

### 3.6 日志 logcat

```bash
adb logcat                                  # 实时
adb logcat -d                               # dump 后退出（不阻塞）
adb logcat -c                               # 清空缓冲
adb logcat -v threadtime                    # 带时间/线程/pid（推荐默认）
adb logcat -v time -v color
adb logcat -b main,system,crash             # 指定缓冲区
adb logcat -b all                           # 全部缓冲区
adb logcat -s MyTag                         # 只看某 TAG
adb logcat MyTag:D *:S                      # 只要 MyTag 的 D 以上
adb logcat --pid=$(adb shell pidof -s com.example.app)
adb logcat -G 16M                           # 扩大缓冲区（抓崩溃必备）
adb logcat -f /sdcard/log.txt               # 直接落盘到设备
adb logcat -t 500                           # 最近 500 行
adb logcat *:E                              # 只看 Error
```

**缓冲区（buffer）语义**（面试常问）：

| buffer | 内容 |
| --- | --- |
| `main` | 应用日志（`Log.d/i/w/e`） |
| `system` | 系统服务日志 |
| `crash` | 崩溃日志（Java 崩溃也常在这里） |
| `events` | 结构化事件（`EventLog`，二进制格式，需 `-b events` 并用 `logcat -b events -v ...`） |
| `radio` | 通信相关 |
| `kernel` | 内核（部分设备/权限下可见） |

**抓 Java 崩溃**：

```bash
adb logcat -b crash -d | grep -A 40 "FATAL EXCEPTION"
# 或
adb logcat -d AndroidRuntime:E *:S
```

**抓 Native 崩溃（tombstone）**：需要 root 或 userdebug 设备。

```bash
adb shell ls -l /data/tombstones/
adb shell cat /data/tombstones/tombstone_00
# 或者直接看 logcat 中的 DEBUG / libc 段
adb logcat -b crash -d | grep -A 60 "DEBUG"
```

**一次性收集完整现场**：`adb bugreport` 是真正的重武器。

```bash
adb bugreport ./bugreport-$(date +%s)
# Android 7+ 支持目录参数，产出 zip，内含：
#   bugreport-*.txt     全量 dumpsys + logcat + 属性
#   FS/data/anr/        ANR traces
#   FS/data/tombstones/ native 崩溃
#   proto/              二进制 proto 格式（更小更全）
```

> 面试加分：知道 **bugreport 里的 proto 格式**才能拿到 `dumpsys` 的完整字段（文本 `dumpsys` 常被截断）。平台化诊断系统通常解析 proto。

### 3.7 模拟输入

```bash
adb shell input text "hello%sworld"          # 空格用 %s 转义
adb shell input keyevent 3                   # HOME
adb shell input keyevent 4                   # BACK
adb shell input keyevent 26                  # POWER
adb shell input keyevent 82                  # MENU（常用于解锁）
adb shell input keyevent KEYCODE_WAKEUP      # 224
adb shell input tap 540 1200
adb shell input swipe 540 1600 540 400 300   # x1 y1 x2 y2 持续时间ms
adb shell input keyevent --longpress 3
adb shell input roll 0 100                   # 滚轮
```

**注意**：`input` 注入的是 InputDispatcher 层事件，很多安全页面（支付、指纹、部分银行 App）会通过 `FLAG_SECURE` 或安全键盘屏蔽，这是"自动化点不动"的常见根因之一。

### 3.8 屏幕与录制

```bash
# 截图
adb shell screencap -p /sdcard/s.png && adb pull /sdcard/s.png .
adb exec-out screencap -p > s.png           # 更优：不落盘、二进制安全

# 录屏
adb shell screenrecord /sdcard/demo.mp4 --time-limit 180 --size 720x1280 --bit-rate 4000000 --verbose
adb shell screenrecord --bugreport /sdcard/demo.mp4   # 叠帧时间戳，用于性能分析

# 分辨率与密度（兼容性测试神器）
adb shell wm size                           # 当前
adb shell wm size 1080x1920                 # 临时改分辨率
adb shell wm density 320
adb shell wm size reset
adb shell wm density reset

# 动画开关（性能测试必须先关）
adb shell settings put global window_animation_scale 0
adb shell settings put global transition_animation_scale 0
adb shell settings put global animator_duration_scale 0
```

> ⚠️ **Windows PowerShell 二进制陷阱（企业级高频坑）**
> PowerShell 5 的 `>` 重定向会把原生命令输出按文本解码再编码，`adb exec-out screencap -p > s.png` 产出的 PNG **是损坏的**（多平台自动化脚本挂在这一行上）。三种解法：

```powershell
cmd /c "adb exec-out screencap -p > s.png"                      # 交给 cmd 处理重定向
adb exec-out screencap -p | Set-Content -AsByteStream s.png     # PS 6+ 字节流写入
adb shell screencap -p /sdcard/s.png; adb pull /sdcard/s.png .  # 最稳：设备落盘再拉取
```

---

## 4. 进阶篇：让它变快、变稳、变自动

### 4.1 `adb shell` vs `adb exec-out`：二进制安全的关键

| 维度 | `adb shell` | `adb exec-out` |
| --- | --- | --- |
| 是否分配 PTY | 是 | 否 |
| 换行处理 | `\n` → `\r\n` | 原样 |
| 二进制安全 | ❌ 会被破坏 | ✅ |
| 交互式命令（`su`、`vi`） | ✅ 可用 | ❌ 不可用 |
| 适用场景 | 人工调试 | 脚本、取二进制、管道 |

**实战对照**：

```bash
# ❌ 取数据库，文件会因 CRLF 翻译而损坏
adb shell "cat /sdcard/a.db" > a.db
# ✅
adb exec-out "cat /sdcard/a.db" > a.db

# ✅ 免 root 取 debuggable 应用私有文件
adb exec-out run-as com.example.app cat databases/app.db > app.db
```

**行尾处理**（跨平台脚本必修课）：`adb shell getprop xxx` 的输出带 `\r`，在 Linux 脚本里比较会失败：

```bash
# ❌ 永远为 false
[ "$(adb shell getprop sys.boot_completed)" = "1" ]
# ✅
[ "$(adb shell getprop sys.boot_completed | tr -d '\r')" = "1" ]
```

### 4.2 端口转发：`forward` 与 `reverse`

这是从"会用 ADB"跨越到"懂 ADB"的分水岭。

```bash
# forward：开发机 → 设备（访问设备上的服务）
adb forward tcp:6100 tcp:7100
adb forward tcp:6100 localabstract:scrcpy      # unix domain socket
adb forward --list
adb forward --remove tcp:6100
adb forward --remove-all

# reverse：设备 → 开发机（让设备访问你电脑上的服务）
adb reverse tcp:8081 tcp:8081
adb reverse --list
adb reverse --remove-all
```

方向记忆法：

```
forward:   [你的浏览器] → localhost:6100 → adb → 设备:7100
reverse:   [设备上的 App] → localhost:8081 → adb → 你电脑:8081
```

**`reverse` 为什么是企业级必备**：

1. **React Native / Metro**：真机连开发机 `8081`，官方推荐就是 `adb reverse tcp:8081 tcp:8081`。
2. **Mock Server / 测试桩**：让真机访问开发机上跑的 Mock 服务，无需修改 App 的 baseUrl，也无需设备与开发机同网段。
3. **抓包**：`adb reverse tcp:8888 tcp:8888` 让设备流量打到你电脑的 Charles/mitmproxy，**不用配 WiFi 代理、不用装证书到系统区**（但 HTTPS 解密仍需证书）。
4. **免同网段**：设备在 USB 上、开发机在 VPN 里，`reverse` 照样通。

> 面试题：**"设备连不上你电脑上的测试服务，怎么办？"** 答 `adb reverse` 的候选人，和答"把电脑 IP 填到 App 里"的候选人，不在一个水平线上。

### 4.3 无线调试：从 TCP 到 Android 11 配对

**经典方式（Android 10 及以下，或已知端口）**：

```bash
# 1. 先用 USB 连上，让设备在 5555 监听
adb tcpip 5555
# 2. 拔掉 USB（可选），连接
adb connect 192.168.1.100:5555
adb devices
# 3. 断开
adb disconnect 192.168.1.100:5555
# 4. 需要 root 时可持久化
adb shell setprop persist.adb.tcp.port 5555
```

**Android 11+ 无线调试（带配对码，mDNS 发现）**：

```bash
# 手机：开发者选项 → 无线调试 → 使用配对码配对设备
# 拿到 IP:PORT（配对端口）与 6 位配对码
adb pair 192.168.1.100:37123
# 输入 6 位码 → 配对成功（密钥交换）

# 然后用「IP 和端口」页面显示的另一个端口连接
adb connect 192.168.1.100:5555

# mDNS 自动发现（需网络支持 mDNS）
adb mdns check
adb mdns services
```

**为什么 Android 11 要引入配对**：Android 10 及以前，任何人 `adb connect` 到你的 5555 端口都能尝试连接，安全性依赖"设备弹窗授权"，而部分设备在 TCP 模式下不会弹窗（等价于无鉴权）。Android 11 强制引入 TLS + 配对码，才能建立可信链路。

**无线调试的真实代价（企业级视角）**：

| 维度 | USB | 无线 |
| --- | --- | --- |
| 稳定性 | 高（有线） | 受 WiFi 干扰，易掉线 |
| 吞吐（安装大 APK / 传日志） | 高 | 明显低，安装慢 2-5 倍 |
| 规模 | 受 USB 口/供电限制 | 理论上不受限，但受 AP/信道限制 |
| 供电 | 直接供电 | 需另配充电，长期测试有电量风险 |
| 适用 | 设备农场主力 | 免线、演示、远程、跨地域真机云 |

**结论**：规模化农场仍以 **USB + 高品质有源 Hub + 独立供电** 为主，无线调试用于灵活接入和远程场景。

### 4.4 性能与诊断工具箱

```bash
# ---- 内存 ----
adb shell dumpsys meminfo com.example.app
adb shell dumpsys meminfo -d com.example.app       # 更细
adb shell dumpsys procstats --hours 3              # 一段时间内的内存行为
adb shell dumpsys meminfo                          # 全系统

# ---- CPU / 帧率 ----
adb shell dumpsys cpuinfo
adb shell dumpsys gfxinfo com.example.app
adb shell dumpsys gfxinfo com.example.app framestats   # 每帧明细（jank 分析）
adb shell dumpsys SurfaceFlinger --latency <layer>     # 帧延迟直方图

# ---- 电量 ----
adb shell dumpsys batterystats --reset
# ... 跑业务 ...
adb shell dumpsys batterystats com.example.app > battery.txt
adb shell dumpsys battery                          # 当前状态（可 set 造假）
adb shell dumpsys battery set level 50
adb shell dumpsys battery unplug                   # 模拟拔电
adb shell dumpsys battery reset
adb shell dumpsys deviceidle force-idle            # 强制 Doze，测后台限制
adb shell dumpsys deviceidle unforce

# ---- 网络 ----
adb shell dumpsys netstats detail
adb shell dumpsys connectivity
adb shell dumpsys wifi | head -50

# ---- 启动与 ANR ----
adb shell dumpsys activity exit-info com.example.app    # Android 11+ 历史退出原因
adb shell dumpsys dropbox --print | grep -A 30 "data_app_anr"
adb shell cat /data/anr/traces.txt                      # 需权限，新版路径为 /data/anr/
adb shell ls /data/anr/

# ---- 系统级追踪（现代方式）----
adb shell perfetto -o /data/misc/perfetto-traces/trace -t 10s \
  sched freq idle am wm gfx view binder_driver
adb pull /data/misc/perfetto-traces/trace ./trace.perfetto-trace
# 用 ui.perfetto.dev 打开分析

# ---- CPU 采样（native 热点）----
adb shell simpleperf record -p $(adb shell pidof com.example.app) --duration 10 -o /data/local/tmp/perf.data
adb pull /data/local/tmp/perf.data .

# ---- 编译状态（性能基线必做）----
adb shell cmd package compile -m speed -f com.example.app   # 强制 AOT 编译
adb shell cmd package compile -m verify -f com.example.app  # 重置
```

**性能测试的三条纪律**（面试常问"你怎么保证数据可信"）：

1. **固定编译状态**：`speed` / `speed-profile` / `verify` 三种模式的差距可达 30%+，不固定就等于随机数。
2. **固定环境**：分辨率、密度、动画、亮度、电量、温度、后台应用、网络。
3. **统计而非单次**：≥10 次，报中位数 + P90 + 抖动；去掉冷启动首帧的首次 IO 影响。

### 4.5 自动化测试接口

```bash
# ---- Instrumentation 测试（Espresso / AndroidJUnitRunner）----
adb shell am instrument -w \
  -e class com.example.test.LoginTest#testLoginSuccess \
  com.example.test/androidx.test.runner.AndroidJUnitRunner

# 常用参数
#   -w                等待测试结束（必备，否则立即返回）
#   -r                原始输出（便于解析）
#   -e debug true     等调试器
#   -e coverage true  覆盖率
#   -e package com.example.test.ui  只跑某个包

# ---- 输出解析（CI 里靠这个判断成败）----
# OK (2 tests)                       → 成功
# FAILURES!!!                       → 失败
# INSTRUMENTATION_FAILED            → 崩溃/超时，与断言失败区分开！
```

> **企业级陷阱**：CI 里必须区分 **"断言失败"** 和 **"设备/框架异常"**（`INSTRUMENTATION_FAILED`、`Process crashed`、超时）。混在一起，会导致"测试不稳定"的锅永远甩给开发。平台化方案是给退出码分层：用例失败 = 1，基础设施失败 = 2。

```bash
# ---- Monkey 稳定性压测 ----
adb shell monkey -p com.example.app \
  --pct-syskeys 0 --pct-appswitch 5 \
  --throttle 200 --ignore-crashes --ignore-timeouts \
  --monitor-native-crashes -v 50000 \
  > monkey.log 2>&1

# ---- UI 层自动化框架的底层 ----
# Appium      → adb + UiAutomator2/Espresso driver
# uiautomator2(openatx) → 推送 agent apk，走 adb 转发
# Airtest/Poco → adb + 图像识别/poco-sdk
# scrcpy      → 推送 server.jar，adb forward localabstract:scrcpy
```

### 4.6 UI 自动化底层：uiautomator dump 与 getevent

```bash
# dump 当前界面层级
adb shell uiautomator dump /sdcard/ui.xml
adb pull /sdcard/ui.xml .
# 只 dump 指定包
adb shell uiautomator dump --compressed /sdcard/ui.xml

# 查看当前焦点窗口（写脚本定位弹窗必用）
adb shell dumpsys window | grep -E "mCurrentFocus|mFocusedApp"

# 原始触摸事件（逆向坐标/手势调参用）
adb shell getevent -lt /dev/input/event3

# 屏幕物理信息
adb shell wm size
adb shell dumpsys display | grep -E "mBaseDisplayInfo|real"
```

> **坐标系陷阱（面试/实战高频）**：`uiautomator dump` 给的是 **屏幕逻辑坐标（px）**，而 `input tap` 用的也是 px，两者一致；但如果你改了 `wm size`，`screencap` 出来的图片尺寸和 `input` 的坐标系可能不一致——这是"脚本在本机跑通、在农场机器上点偏了"的经典原因。

---

## 5. 企业级篇：把 ADB 变成生产力基础设施

### 5.1 企业里 ADB 的三类落地场景

| 场景 | 关键诉求 | 典型技术栈 |
| --- | --- | --- |
| **研发自助** | 快、免配置、多人抢设备 | 设备占用锁、web adb、远程投屏（scrcpy） |
| **CI/CD 流水线** | 稳定、可复现、失败可归因 | Docker + Jenkins/GitLab CI + 设备池 |
| **真机云 / 设备农场** | 高密度、自愈、多租户隔离 | DeviceFarmer(stf) 或自研调度 + ADB 网关 |
| **企业设备管理（EMM/MDM）** | 合规、锁定、防调试 | Device Owner (`dpm`) + Android Enterprise |

**核心洞察**：单机 `adb` 是工具，规模化后 `adb` 变成了**一个需要被调度、被隔离、被监控的资源**。企业级工作的本质，就是给它加上 **分配、隔离、自愈、可观测** 四件套。

### 5.2 CI/CD 集成：从 Docker 到设备农场

**方案 A：容器直通 USB（简单，但脆弱）**

```bash
docker run --privileged \
  -v /dev/bus/usb:/dev/bus/usb \
  -v $PWD:/work \
  android-ci-image
```

问题：容器内 adb 版本必须与外层一致；`/dev/bus/usb` 热插拔需要 `--privileged`（安全隐患）；USB 掉线容器感知不到。

**方案 B：容器复用宿主 adb server（推荐，最省心）**

```bash
# 宿主先起 server（保持常驻），容器只跑 client 连过去
# 宿主：
adb start-server
# 容器：
adb -H host.docker.internal -P 5037 devices
```

优势：**完全绕开 USB 直通**，容器里连 `adb` 二进制都可以精简；设备管理与容器解耦；多个容器共享设备池（靠 `-s` 隔离）。
注意：需要 `--add-host=host.docker.internal:host-gateway`（Linux）或 Docker Desktop 默认支持。

**方案 C：设备农场 API（规模化终局）**

- 自建：DeviceFarmer/stf、ATX-server、OpenSTF 衍生方案。
- 云厂商：Firebase Test Lab、AWS Device Farm、BrowserStack App Automate、Sauce Labs、阿里云 EMAS/移动测试、腾讯 WeTest、华为云。
- 自研调度层：设备注册 → 健康检查 → 租约分配 → 端口池 → 任务下发 → 日志/产物回收 → 释放。

**一份可用的 CI 脚本骨架（Bash）**：

```bash
#!/usr/bin/env bash
set -Eeuo pipefail

SERIAL="${ANDROID_SERIAL:?must set ANDROID_SERIAL}"
APK="${1:?usage: run.sh app.apk}"
PKG="com.example.app"
RUNNER="com.example.app.test/androidx.test.runner.AndroidJUnitRunner"
ADB="adb -s ${SERIAL}"

cleanup() {
  # 无论成败都回收设备，避免农场"僵尸占用"
  ${ADB} shell am force-stop "${PKG}" || true
  ${ADB} shell wm size reset || true
  ${ADB} shell wm density reset || true
  ${ADB} reverse --remove-all || true
}
trap cleanup EXIT

echo "== 0. 确认设备 =="
"${ADB}" wait-for-device
for i in $(seq 1 60); do
  [ "$(${ADB} shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" = "1" ] && break
  sleep 2
done
until ${ADB} shell pm path android >/dev/null 2>&1; do sleep 2; done
${ADB} shell input keyevent KEYCODE_WAKEUP || true
${ADB} shell svc power stayon true

echo "== 1. 环境固化 =="
${ADB} shell settings put global window_animation_scale 0
${ADB} shell settings put global transition_animation_scale 0
${ADB} shell settings put global animator_duration_scale 0
${ADB} shell wm size 1080x1920
${ADB} shell wm density 420

echo "== 2. 安装 =="
${ADB} install -r -g -t "${APK}" || { echo "INFRA_FAIL install"; exit 2; }

echo "== 3. 跑测试 =="
OUT="$(mktemp)"
timeout 1800 ${ADB} shell am instrument -w -r "${RUNNER}" | tee "${OUT}" || true

if grep -q "OK (" "${OUT}"; then
  echo "PASS"; exit 0
elif grep -q "FAILURES!!!" "${OUT}"; then
  echo "TEST_FAIL"; exit 1
else
  echo "INFRA_FAIL instrumentation crashed/timeout"
  ${ADB} logcat -b crash -d | tail -200
  exit 2
fi
```

**关键设计点**（面试时讲这些，价值远超"我会写脚本"）：

1. `set -Eeuo pipefail` + `trap cleanup EXIT`：**保证设备一定被释放**。
2. **分层退出码**（0/1/2）：让流水线能区分"业务失败"与"环境失败"，这直接决定告警该发给谁。
3. **显式 `-s ${SERIAL}`**：并发场景下唯一正确的姿势。
4. **等待三连**（boot_completed / pm 可用 / 解锁常亮）：消除 80% 的"偶发失败"。
5. **环境固化**：动画、分辨率、密度，保证跨机器结果可比。

### 5.3 设备高可用：断线自愈守护进程

企业级农场最常见的故障不是"设备坏了"，而是**设备'看起来在'但实际不可用**。你需要一个守护进程持续做健康检查并自愈。

```bash
#!/usr/bin/env bash
# adb-watchdog.sh —— 轻量设备健康守护（生产环境建议用 Python/Go 重写并接入监控）
set -uo pipefail
INTERVAL=15
LOG=/var/log/adb-watchdog.log

log() { echo "[$(date '+%F %T')] $*" | tee -a "$LOG"; }

health_check() {           # $1 = serial
  local s="$1"
  adb -s "$s" get-state 2>/dev/null | grep -q '^device$' || return 1
  # 真正打一次命令，验证链路可用（关键！）
  adb -s "$s" shell 'echo ok' 2>/dev/null | tr -d '\r' | grep -q '^ok$' || return 1
  return 0
}

while true; do
  # 1. server 层面的整体健康
  if ! adb devices >/dev/null 2>&1; then
    log "adb server 无响应，重启 server"
    adb kill-server; sleep 2; adb start-server; sleep 3
    continue
  fi

  # 2. 逐个设备
  while read -r line; do
    serial="$(echo "$line" | awk '{print $1}')"
    state="$(echo "$line" | awk '{print $2}')"
    [ "$serial" = "List" ] && continue
    [ -z "${serial:-}" ] && continue

    case "$state" in
      device)
        if ! health_check "$serial"; then
          log "$serial 状态为 device 但命令不通 → reconnect"
          adb -s "$serial" reconnect || true
        fi
        ;;
      offline)
        log "$serial offline → reconnect offline"
        adb reconnect offline || true
        ;;
      unauthorized)
        log "$serial 未授权（需人工）"
        ;;
      *)
        log "$serial 异常状态: $state"
        ;;
    esac
  done < <(adb devices | tail -n +2)

  # 3. 周期性整理（防 server 长期运行状态泄漏）
  #    生产建议：每天低峰期重启一次 server，成本极低、收益明显
  sleep "$INTERVAL"
done
```

**企业级自愈的分层策略**（讲清这个层次，面试直接拉满）：

| 层级 | 动作 | 触发条件 | 成本 |
| --- | --- | --- | --- |
| L1 重连 | `adb reconnect <serial>` | 单设备 offline | 秒级 |
| L2 重启 server | `adb kill-server && adb start-server` | 多设备同时异常 / server 无响应 | 数秒，影响全机 |
| L3 复位 USB | `usbreset` / `uhubctl` 断电该口 | reconnect 无效 | 秒级，需硬件支持 |
| L4 重启设备 | `adb reboot` | 系统卡死 | 分钟级 |
| L5 人工介入 | 工单告警 | 硬件故障 | 小时级 |

加分项：**用带独立开关的 USB Hub（如支持 `uhubctl` 的 Hub）**，就能实现 L3 的"按口断电重启"，这是自建设备农场最值钱的硬件选型决策之一。

### 5.4 并发与隔离：一台机器带多少台设备

**现实数字**（经验值，随 USB 控制器与设备型号浮动）：

- 理论：USB 2.0 总线 127 地址；USB 3.0 控制器通常挂在独立 xHCI 上。
- 实践：**单台 Linux 机器 16-32 台真机**是舒适区；超过后安装失败率、掉线率显著上升。
- 瓶颈不在 CPU，而在 **USB 控制器带宽 + 供电 + 内核枚举稳定性**。

**隔离的关键手段**：

```bash
# 1. 每个任务用独立 adb server（端口池）——最强隔离，避免 kill-server 互相伤害
ANDROID_ADB_SERVER_PORT=5041 adb devices
ANDROID_ADB_SERVER_PORT=5042 adb devices
# 注意：不同 server 各自扫描设备，会重复占用 USB！仅在"故障隔离"必要时使用，
#      常规并发请用单 server + `-s` 隔离。

# 2. 端口转发池：每个任务分配独立本机端口，避免 6100 冲突
adb -s "$SERIAL" forward tcp:$((6100 + TASK_ID)) tcp:7912

# 3. reverse 端口同理
adb -s "$SERIAL" reverse tcp:$((8081 + TASK_ID)) tcp:8081

# 4. 任务级资源锁（文件锁是最简单可靠的实现）
exec 9>"/tmp/adb-lock-${SERIAL}"
flock -w 600 9 || { echo "设备被占用"; exit 3; }
```

**为什么"单 server + `-s`" 优于 "多 server"**：每个 adb server 都独立枚举 USB 设备，多个 server 会争抢同一物理设备句柄，导致 `device busy` / `offline` 潮。**隔离靠 `-s` + 端口池 + 锁，不靠多 server。**

### 5.5 安全与合规：别让 ADB 成为后门

ADB 的权限极高——`shell` 用户的权限在不少 ROM 上等同半个 root（可 `am`/`pm`/`dumpsys`/读写 `/sdcard`）。企业里必须管起来。

**风险清单**：

| 风险 | 说明 |
| --- | --- |
| 未授权设备接入 | 员工把手机插上就跑 `adb pull /sdcard`，可拷走照片/文档 |
| 调试桥被劫持 | 恶意软件拉起 adb server 或占用 5037 端口 |
| 生产设备可调试 | 忘记关 USB 调试就出厂 → 物理接触即数据泄露 |
| 无线调试暴露 | `tcpip 5555` 后同网段可扫描连接 |
| adbkey 泄露 | CI 密钥若泄漏，攻击者可伪装成可信主机 |

**加固手段（按场景）**：

```bash
# 1. 企业设备（EMM/MDM）：Device Owner 直接禁用调试
adb shell dpm set-device-owner com.example.mdm/.AdminReceiver
# 设备上会要求：无已登录账号、无多用户、未启用其他 Device Owner
# 之后通过 DevicePolicyManager 设置：
#   DISALLOW_DEBUGGING_FEATURES          → 禁用 USB 调试
#   DISALLOW_CONFIG_CREDENTIALS
#   DISALLOW_INSTALL_UNKNOWN_SOURCES
#   setStatusBarDisabled / lockTaskMode  → Kiosk 模式

# 2. 关闭无线调试遗留状态
adb usb                       # 切回 USB 模式，关闭 TCP 监听

# 3. 检查是否有非预期调试连接
adb shell getprop service.adb.tcp.port
adb shell netstat -anp 2>/dev/null | grep 5555

# 4. CI 侧最小化权限
#    - 专用测试机，不放业务/个人数据
#    - adbkey 放在受控 secrets 中，按 Runner 隔离
#    - 测试完成后 adb usb；不长期保留 tcpip 状态
```

**合规视角**：涉及用户数据的真机测试，需要有**数据最小化**意识——`adb pull /sdcard` 之前先确认这不是真实用户设备；测试日志里避免落明文 token/手机号。

### 5.6 可观测性：设备指标与日志采集

一个成熟的设备平台至少采集四类数据：

```bash
# ① 设备在线率（你的 SLO 核心指标）
adb devices | grep -c "device$"

# ② 设备健康（电量、温度、存储——低于阈值自动隔离出池）
adb shell dumpsys battery | grep -E "level|temperature"
adb shell df /data | tail -1
adb shell cat /sys/class/thermal/thermal_zone0/temp

# ③ 系统负载（判断是不是机器侧问题）
adb shell cat /proc/loadavg
adb shell dumpsys cpuinfo | head

# ④ 全量现场（失败任务必收）
adb logcat -b all -d -v threadtime > logcat_all.txt
adb bugreport ./bugreport
adb shell dumpsys activity exit-info com.example.app > exit_info.txt
```

**关键指标建议**：

| 指标 | 目标 | 说明 |
| --- | --- | --- |
| 设备可用率 | > 95% | 排除人工下线后，可调度设备 / 总设备 |
| 任务基础设施失败率 | < 2% | 与业务失败严格区分 |
| 平均恢复时间 | < 60s | 从 offline 到重新可用 |
| 安装成功率 | > 99% | 低于此值先查线材/Hub/存储 |
| 单任务耗时 P90 | 按业务定 | 突然劣化通常意味着设备老化或版本回归 |

### 5.7 企业级踩坑清单

按"踩到就半夜加班"的程度排序：

1. **5037 被占用**：各种手机助手（应用宝、360、Kies、Mobizen 等）会偷偷起自己的 adb 或占用端口。用 `netstat -ano | findstr :5037` 定位 PID，再 `taskkill /PID <pid> /F` 结束进程，最后排查是哪个软件常驻。
2. **adb 版本不一致**：CI 镜像、本地、IDE 插件各自带一份 adb。服务器上一定要 `which -a adb` 查清有几份，并锁版本。
3. **Windows 多用户会话**：adb server 是**机器级**的。如果 A 用户会话启动了 server，B 用户会连到"别人的" server，看到别人的设备表——共享 Runner 的经典事故。
4. **USB Hub 供电不足**：便宜 Hub 带 8 台设备，装上第三台就开始随机掉线。**必须用带独立电源的有源 Hub**。
5. **线材问题**：劣质线只能充电不能传数据，或大数据传输时 CRC 错误导致 `failed to finalize session`。农场要统一采购、统一标记、定期更换。
6. **设备自动休眠/锁屏**：`svc power stayon true` + 关闭自动锁屏 + 关闭省电模式，否则任务跑一半屏幕黑掉。
7. **Linux 自动挂起**：见 2.1，不改内核参数，设备几十分钟后必掉。
8. **权限弹窗打断自动化**：`install -g` + 预置权限 + 首次启动跳过引导（`--ez skip_intro true` 之类的启动参数）。
9. **`adb shell` 换行导致断言失败**：见 4.1，永远 `tr -d '\r'`。
10. **临时文件不清理**：`/sdcard` 被截图/录屏/日志塞满，然后开始大面积安装失败。任务结束时清理。
11. **server 长期运行的状态泄漏**：跑了几天后 `adb devices` 卡住。低峰期定时 `kill-server` 是廉价有效的运维手段。
12. **`--privileged` 容器的安全债**：USB 直通带来了容器逃逸面，安全团队一定会找上来。尽早切到"复用宿主 server"模型。

---

## 6. 面试篇：分层题库 + 参考答案

### 6.1 初级（1-3 年）

**Q1. ADB 是什么？由哪几部分组成？**

> Android Debug Bridge，包含 **adb client**（开发机上的命令行进程，每条命令一个）、**adb server**（开发机后台常驻，监听 5037，全局唯一）、**adbd**（设备上的守护进程）。client 与 server 走本地 socket 通信，server 与 adbd 走 USB 或 TCP。

**Q2. `adb devices` 显示 `unauthorized` 怎么办？**

> 设备未信任开发机公钥。检查手机是否弹出授权弹窗并勾选"一律允许"；确认开发者选项里的 USB 调试已开；可删除 `~/.android/adbkey` 与 `adbkey.pub` 让 ADB 重新生成密钥后重新授权；确认 `ADB_VENDOR_KEYS` 配置；企业 CI 需固化 adbkey。

**Q3. 怎么安装一个 APK？覆盖安装、允许降级、授予权限分别用什么参数？**

> `adb install app.apk`；`-r` 覆盖安装；`-d` 允许降级；`-g` 安装时授予全部运行时权限；`-t` 允许 test-only 包。

**Q4. 怎么只看某个 TAG 的日志？怎么清空日志？**

> `adb logcat -s MyTag` 或 `adb logcat MyTag:D *:S`；清空用 `adb logcat -c`；只看崩溃 `adb logcat -b crash -d`。

**Q5. 怎么杀掉一个应用的进程？**

> 优先 `adb shell am force-stop <pkg>`（走 AMS，最干净）。想温和一些用 `am kill <pkg>`。直接 `adb shell kill -9 <pid>` 也行，但绕过 AMS，可能触发异常重启逻辑。

**Q6. `adb shell` 和直接手机上的终端有什么区别？**

> `adb shell` 以 `shell` 用户身份运行，权限受 SELinux 与 UID 限制；不是 root。分配 PTY，所以有行尾转换等副作用。是否能 `su` 取决于设备 build 类型（user 版通常不行）。

**Q7. 怎么把文件从电脑推到手机？反过来呢？**

> `adb push local /sdcard/x`；`adb pull /sdcard/x .`。目录都支持递归。

**Q8. 什么是 `-s` 参数？为什么需要它？**

> 指定目标设备序列号。默认在只有一台设备时自动选中，多台时所有命令报 `more than one device/emulator`，所以自动化脚本必须显式指定。

---

### 6.2 中级（3-5 年）

**Q9. `adb forward` 和 `adb reverse` 的区别？各举一个真实用途。**

> `forward` 是主机端口映射到设备端口（主机 → 设备），用于通过主机访问设备上的服务；`reverse` 是设备端口映射到主机端口（设备 → 主机），用于让设备上的 App 访问主机上的服务。
> forward 用例：`adb forward tcp:6100 localabstract:scrcpy` 让 scrcpy 通过 ADB 拿到设备画面。
> reverse 用例：`adb reverse tcp:8081 tcp:8081` 让真机访问开发机的 Metro bundler；或 `adb reverse tcp:8888 tcp:8888` 让真机流量打到主机上的抓包代理。

**Q10. `adb shell` 和 `adb exec-out` 有什么区别？什么时候必须用后者？**

> `shell` 分配 PTY，会把 `\n` 翻译成 `\r\n` 并可能破坏二进制流；`exec-out` 不分配 PTY，输出二进制安全、无行尾改写。取截图/数据库/任何二进制文件时必须用 `exec-out`。

**Q11. 无线调试的原理？Android 11 的配对机制解决了什么问题？**

> 原理：让设备上的 adbd 额外监听 TCP 端口（默认 5555），transport 从 USB 换成 TCP，上层协议完全不变。
> Android 11 之前，`adb connect` 到 5555 只需设备侧弹窗授权，而 TCP 模式下部分设备不弹窗，等于链路无鉴权。Android 11 引入 **TLS + 8 位配对码的显式配对流程**（`adb pair`），先建立可信密钥再连接，避免同网段任意主机接入。

**Q12. `adb wait-for-device` 之后就能装应用了吗？**

> 不能。它只等设备被报告为 device 状态，不代表系统启动完成。要等 `sys.boot_completed=1`，还要等 PackageManager 可用（`pm path android` 能返回），否则会出现"设备已就绪但 install 失败"的偶发问题。

**Q13. 怎么在不 root 的情况下拿到 debuggable 应用的私有数据库？**

> `adb exec-out run-as <pkg> cat databases/app.db > app.db`。条件是该应用 `android:debuggable="true"`（debug 构建），且 `run-as` 在 user build 上对该应用可用。非 debuggable 应用则需要 root/userdebug 设备，或应用自身提供导出入口。

**Q14. 怎么测应用冷启动时间？怎么保证数据可信？**

> `adb shell am force-stop <pkg>` 然后 `adb shell am start -W -n <pkg>/<activity>`，读 `TotalTime`（应用自身启动）与 `WaitTime`（AMS 视角总耗时）。
> 可信性靠三点：固定编译状态（`cmd package compile -m speed -f`，避免 speed/speed-profile/verify 之间 30%+ 差异）、固定环境（分辨率/密度/动画/亮度/电量/温度、清后台）、多次采样取中位数与 P90。

**Q15. `offline` 状态的原因有哪些？怎么排查？**

> 常见原因：USB 自动挂起、线材/供电问题、设备休眠、adb server 状态卡死、client/server 版本不一致、多个 adb server 争抢同一设备。
> 排查顺序：`adb kill-server && adb start-server` → `adb reconnect offline` → 换线换口 → 检查 `which -a adb` 版本是否唯一 → Linux 检查 udev 与 autosuspend → 最后考虑 `adb reboot`。

**Q16. ANR 和 Native 崩溃的日志分别在哪里？**

> ANR：`/data/anr/` 下的 traces（需权限），或 `dumpsys dropbox` 的 `data_app_anr` 条目；最稳妥是 `adb bugreport` 里取 `FS/data/anr/`。Native 崩溃：`/data/tombstones/tombstone_*`（需 root/userdebug），logcat 的 `DEBUG`/`crash` 缓冲区也有摘要。Android 11+ 还可用 `dumpsys activity exit-info <pkg>` 查历史退出原因。

**Q17. 怎么抓全量现场交给开发排查？**

> `adb bugreport <dir>`，产出 zip，包含完整 dumpsys、全部 logcat、ANR、tombstone、属性、文件系统快照。注意 Android 7+ 才支持目录参数，且 proto 格式比文本更完整（文本 dumpsys 常被截断）。

**Q18. 一台机器上跑多台设备的自动化，有哪些隔离点？**

> ① 用 `-s <serial>` 指定设备；② 端口转发/reverse 用任务独立端口（端口池）；③ 设备级文件锁保证同一设备不被并发占用；④ 任务前后清理设备状态（force-stop、wm reset、reverse remove-all）；⑤ 不要为了隔离而给每个任务起独立 adb server——会争抢 USB 设备句柄。

---

### 6.3 高级 / 架构设计

**Q19. 什么叫"单 adb server + `-s` 隔离"？为什么不推荐每个任务一个 adb server？**

> 一个 adb server 可以管理所有设备，通过 `-s` 精确路由，资源开销最小、设备枚举唯一，不会重复打开 USB 句柄。
> 多个 adb server（不同 `ANDROID_ADB_SERVER_PORT`）会各自扫描 USB 并争抢同一物理设备，导致 `device busy`/`offline` 潮；而且 `kill-server` 会互相影响。多 server 只适合"故障域隔离"这种极少数场景。

**Q20. 设计一个千台规模的 Android 设备农场，你会怎么分层？**

> 参考答法（分五层，讲清职责与失败域）：
> 1. **接入层**：USB Hub（有源、可断电重启）+ 主机（每台 16-32 台设备），Linux + udev + 关闭 autosuspend。
> 2. **ADB 网关层**：单机单 server；封装 ADB 操作为 RPC（安装/启动/日志/截图），屏蔽 shell 细节；内置重试与超时。
> 3. **健康与自愈层**：watchdog 做 L1-L5 分层恢复（reconnect → 重启 server → USB 断电 → reboot → 人工）；健康指标（电量/温度/存储/在线率）驱动出池入池。
> 4. **调度层**：设备注册与标签（机型/版本/ABI）、租约 + 心跳 + 超时释放、任务队列、优先级与抢占；任务前后自动 reset。
> 5. **可观测与产物层**：设备在线率/基础设施失败率 SLO、失败任务自动收 bugreport/logcat/截图、产物归档与检索（按 task id 关联）。
> 附加：多租户隔离（配额 + 网络隔离）、成本核算（设备占用时长）、灰度（先小池验证再全量）。

**Q21. 设备"看起来在线但任务总是失败"，你怎么定位？**

> 分三路收敛：
> ① **链路真实性**：不要只信 `adb devices`，要实际执行一次命令（`adb -s X shell echo ok`）——`device` 状态不等于链路可用。
> ② **设备侧**：存储是否满（`df /data`）、电量/温度是否异常、是否被前一个任务污染（残留 reverse、改过的 wm size、未清的数据）。
> ③ **宿主机侧**：`/proc/loadavg`、USB 错误日志（`dmesg | grep -i usb`）、是否有别的软件在抢 5037、adb 版本是否被升级。
> 工程化解法：把"任务前自检"做成流水线第一步（自检不过直接标记设备不健康并换机），而不是让任务失败后再排查。

**Q22. CI 里 Android 测试失败的分类为什么重要？你会怎么设计？**

> 因为"业务断言失败"和"基础设施失败"的**责任人和处理动作完全不同**：前者给开发，后者给平台/运维。混在一起会导致"测试不稳定"的口碑崩塌，团队开始忽略红灯。
> 设计：定义分层退出码（0 通过 / 1 用例失败 / 2 基础设施失败 / 3 资源不足），CI 里对 2/3 自动重试一次并换设备，仍未通过则告警平台方；同时把设备信息、bugreport、logcat 作为产物归档，让失败可归因。

**Q23. 你怎么保证 ADB 操作在自动化里"幂等 + 可重试"？**

> - 安装：`install -r -g -t`，配 `pm uninstall` 兜底签名冲突。
> - 启动：`am start -S -W`，`-S` 保证"杀死再启"的确定起点。
> - 状态清理：`pm clear`、`wm size reset`、`settings put` 恢复默认、`reverse --remove-all`。
> - 等待：用"轮询条件"而不是 `sleep N`（`boot_completed`、`pm path`、目标窗口出现）。
> - 超时：所有 adb 调用都包 `timeout`，避免挂死占住设备。
> - 重试：只对**幂等且明确是基础设施错误**的操作重试（install、connect），不对断言重试。

**Q24. `pm`、`cmd package`、`dumpsys` 三者关系？**

> `pm`/`am`/`wm` 等是设备上的 shell 脚本，内部多数转发到 `cmd <service> <args>`（Android 7+ 引入 `cmd`）。`dumpsys` 走的是 `IDumpstate`/各系统服务的 `dump()` 接口，输出的是"服务内部状态"。做工具时优先用 `cmd`（参数更稳定、有 `help` 输出、便于解析），需要深层状态时才上 `dumpsys`。

**Q25. ADB 的安全边界在哪？企业里怎么加固？**

> 边界：`shell` 用户能做的事它都能做（am/pm/dumpsys/读写共享存储），在 userdebug 设备上 `adb root` 直接是 root。加固：生产设备用 Device Owner 设 `DISALLOW_DEBUGGING_FEATURES`；关闭 tcpip 长期监听（`adb usb`）；CI 用专用测试机 + 受控 adbkey；终端侧禁止未知 USB 设备（设备管控软件）；日志脱敏；《数据最小化》原则——不要把真实用户设备接到测试农场。

**Q26. 无线调试适合大规模农场吗？**

> 不适合作为主力。原因：WiFi 共享介质导致抖动与掉线；安装大 APK 吞吐远低于 USB（2-5 倍慢）；长期测试需独立供电；mDNS/子网隔离在数据中心里常被禁。它的价值在"免线灵活接入、远程/跨地域、演示"。规模化仍以有源 USB Hub + 独立供电为主。

**Q27. 为什么 `adb kill-server` 能解决很多问题？什么时候不该用？**

> 因为它重建了设备枚举与连接状态机，清掉了卡死的 transport 和过期的 socket。不该用的时候：有其他并发任务正在跑（会波及其他任务，这也是为什么生产环境应给"server 重启"加全机级别锁，并在低峰期执行）。

---

### 6.4 场景设计题（重点）

**场景一：App 偶发闪退，QA 说"复现不了"，你只有一台设备，怎么把证据拿回来？**

参考答法（体现工程化思维，而不是"我多试几次"）：

1. **先扩缓冲区**：`adb logcat -G 16M`，否则崩溃日志会被冲掉。
2. **持续落盘 + 分片**：后台跑 `adb logcat -b all -v threadtime -f /sdcard/lc_%Y%m%d_%H%M%S.log`（或主机侧 `-f` 到本地），避免只抓"事后"。
3. **开启 tombstone/ANR 收集**：`adb shell setprop persist.tombstoned.enabled 1`（视 ROM），并周期性 `adb shell ls /data/anr`。
4. **用 bugreport 兜底**：一旦观察到异常，立即 `adb bugreport`，拿到完整现场（含 proto 全字段）。
5. **让脚本 7×24 跑压力路径**：Monkey（`--pct-syskeys 0 --ignore-crashes --monitor-native-crashes`）+ 关键业务链路脚本，把"偶发"变成"必然"。
6. **归因分层**：拿到崩溃后区分 Java / Native / 系统杀进程（`exit-info`、`dumpsys dropbox` 的 `data_app_crash`、`system_app_anr`、LMK 日志 `lowmemorykiller`）。
7. **产出物关联**：日志 + 崩溃时间点 + 操作路径 + 设备/版本信息一起提 issue，而不是丢一段 logcat。

**场景二：给公司搭一个"研发自助借真机"平台，你会怎么做？**

参考答法：

1. **需求拆解**：借还（租约）、远程操作（投屏+触控）、环境还原（每次借用后 reset）、权限（谁能用哪些机型）、审计。
2. **最小可用版本**：DeviceFarmer/stf 或 scrcpy over adb 做远程投屏；用文件锁/DB 做租约；task 结束自动 `pm clear` + `wm reset` + `reverse --remove-all`。
3. **不要自研的部分**：投屏/编码（用 scrcpy 或 stf）、设备健康（用现成 watchdog 模式）。
4. **必须自研的部分**：与公司账号体系打通的权限模型、审计日志、与 CI 设备池的资源共享策略（研发白天用、CI 夜间用，或按配额划分）。
5. **风险**：研发用真机跑业务，容易把测试机当生产机，需要网络隔离 + 敏感数据管控。

**场景三：流水线里 Android 测试"红灯疲劳"，怎么救？**

参考答法：

1. **先量化**：把失败分为 用例失败 / 基础设施失败 / 超时 三类，算出各自比例（通常会发现基础设施类占 30-60%）。
2. **对症下药**：
   - 基础设施类：加等待三连、`-g` 安装、超时与重试、换线换 Hub、watchdog 自愈。
   - 超时类：拆分长用例、给每个 adb 调用加 timeout、设备换更高性能机型。
   - 真实失败类：交给开发，并把 bugreport 自动附上。
3. **机制建设**：分层退出码、基础设施失败自动换机重试一次、失败自动归档现场、稳定性看板（周维度趋势）。
4. **文化**：为"基础设施失败率"设 SLO（如 <2%），平台方对该指标负责，开发才不会觉得红灯是噪音。

---

### 6.5 面试官视角：什么样的回答加分

**会减分的回答**：

- 只会背命令，问"为什么"就答不上来。
- 把 `forward` 和 `reverse` 讲反，或只知道 `forward`。
- 认为 `adb devices` 显示 `device` 就等于链路可用。
- 说"多台设备就用多个 adb server"。
- 谈性能测试只说"跑 10 次取平均"，不提编译状态与环境固化。
- 遇到"设备掉线"只会说"重启一下"。

**明显加分的回答**：

- 能画出 client / server / adbd 三端架构，并解释 5037 与 5555 的角色。
- 主动区分 `shell` 与 `exec-out` 的二进制安全性，并提到 `\r` 的坑。
- 讲 `reverse` 时能说出 RN/Metro、Mock Server、抓包三个真实场景。
- 谈架构时主动引入"失败域/责任边界/退出码分层"，把技术问题上升为协作问题。
- 谈稳定性时给出"L1-L5 分层自愈"这种结构化答案。
- 主动提安全与合规（Device Owner、DISALLOW_DEBUGGING_FEATURES、数据最小化）。
- 承认边界：知道 ADB 在 user build 上的能力上限，不吹牛。

---

## 7. 故障排查手册

### 7.1 设备连接类

| 现象 | 排查步骤 |
| --- | --- |
| `adb devices` 空列表 | ① 换线换口 ② Windows 装/换 USB 驱动（Zadig→WinUSB）③ `adb kill-server` ④ Linux 查 udev + `lsusb` ⑤ 开发者选项里 USB 调试是否开 ⑥ 是否被手机助手软件占用 5037 |
| `unauthorized` | 手机弹窗点允许 → 删 `~/.android/adbkey*` 重新授权 → 检查 `ADB_VENDOR_KEYS` |
| `offline` | `adb reconnect offline` → `kill-server` → 检查 autosuspend → 换线 → `adb reboot` |
| `no permissions` | Linux udev 规则 + 用户组 + `adb kill-server` 后重插 |
| 有设备但命令都报 `more than one device` | 加 `-s <serial>`；或临时 `-d`/`-e` |
| emulator 连不上 | 查 `emulator-5554` 是否被占用；冷启动 emulator；查 Hyper-V/WHPX 冲突 |

### 7.2 Server 与服务类

| 现象 | 排查步骤 |
| --- | --- |
| `adb server version doesn't match` | `which -a adb` 找全部副本，统一到同一版本（IDE 插件常自带一份） |
| `cannot connect to daemon at tcp:5037` | `netstat -ano \| findstr :5037` 找占用进程；防火墙；多用户会话冲突 |
| 命令随机卡住不返回 | server 状态泄漏 → 低峰期 `kill-server`；给所有 adb 调用加 `timeout` |
| 多台设备同时掉线 | USB 控制器/供电问题；`dmesg \| grep -i usb`；降低单机设备密度 |

### 7.3 安装与运行类

| 现象 | 排查步骤 |
| --- | --- |
| `INSTALL_FAILED_UPDATE_INCOMPATIBLE` | 签名不一致 → `adb uninstall` 后重装 |
| `INSTALL_FAILED_INSUFFICIENT_STORAGE` | `adb shell df -h /data`，清理 `/sdcard` 与临时文件 |
| `failed to finalize session` | 线材/USB Hub/存储满；降低传输并发 |
| `INSTALL_FAILED_USER_RESTRICTED` | 厂商限制 → 开发者选项允许 USB 安装；MIUI 需登录账号等 |
| 装完就闪退 | `adb logcat -b crash -d`；检查 ABI 是否匹配（`--abi`） |
| 应用启动即黑屏/白屏 | `dumpsys window \| grep mCurrentFocus` 看焦点是否在自己应用；常见于引导页/权限弹窗 |

### 7.4 日志与证据类

| 现象 | 排查步骤 |
| --- | --- |
| 抓不到崩溃日志 | `logcat -G 16M` 扩 buffer；加 `-b crash`/`-b all`；改用 `bugreport` |
| ANR traces 读不到 | 需 root/userdebug；改用 `bugreport` 的 `FS/data/anr/`，或 `dumpsys dropbox --print` |
| 日志里时间对不上 | 设备时区/时钟偏移 → `adb shell date`，比对主机时间；用 `-v threadtime` 带完整时间戳 |
| 截图是坏的/打不开 | PowerShell 重定向陷阱（见 3.8），改用 `cmd /c`、`Set-Content -AsByteStream` 或先落盘再 pull |

---

## 8. 附录：命令速查

### 8.1 设备与连接

```bash
adb devices -l                       # 列设备（含型号/transport_id）
adb -s <serial> <cmd>                # 指定设备（自动化必用）
adb -d / -e / -t <id>                # USB / 模拟器 / transport_id
adb kill-server / start-server       # 重启 server
adb get-state / get-serialno
adb wait-for-device                  # 等设备出现
adb reconnect [offline|device]
adb reboot [bootloader|recovery|sideload]
adb root / unroot / remount
adb usb                              # 关掉 TCP 模式，回到 USB
adb tcpip 5555                       # 设备监听 5555
adb connect <ip>:5555 / disconnect
adb pair <ip>:<port>                 # Android 11+ 配对
adb mdns check / services
```

### 8.2 应用

```bash
adb install [-r|-d|-g|-t] app.apk
adb install-multiple base.apk split_*.apk
adb uninstall [-k] com.pkg
adb shell pm list packages [-3|-s|-d|-u] [-f]
adb shell pm path com.pkg
adb shell pm clear com.pkg
adb shell pm grant/revoke com.pkg <permission>
adb shell pm disable-user --user 0 com.pkg
adb shell appops get/set com.pkg <op> <mode>
adb shell cmd package compile -m speed -f com.pkg
adb shell dumpsys package com.pkg
```

### 8.3 组件与交互

```bash
adb shell am start [-W|-S] -n com.pkg/.Act
adb shell am force-stop com.pkg
adb shell am broadcast -a <action> [--es k v] [--ei k 1]
adb shell am instrument -w -r -e class <cls> <pkg/runner>
adb shell input text "hi%sworld"
adb shell input tap/swipe/keyevent ...
adb shell uiautomator dump /sdcard/ui.xml
adb shell dumpsys window | grep -E "mCurrentFocus|mFocusedApp"
```

### 8.4 文件与屏幕

```bash
adb push <local> <remote>            # 电脑 → 设备
adb pull <remote> <local>            # 设备 → 电脑
adb exec-out cat /sdcard/x > x       # 二进制安全
adb exec-out run-as com.pkg cat databases/app.db > app.db
adb shell screencap -p /sdcard/s.png
adb exec-out screencap -p > s.png    # 注意 PowerShell 陷阱
adb shell screenrecord /sdcard/a.mp4 --time-limit 180
adb shell wm size [WxH|reset]
adb shell wm density [N|reset]
adb shell df -h
```

### 8.5 日志与诊断

```bash
adb logcat -c                        # 清
adb logcat -d                        # dump 退出
adb logcat -v threadtime             # 推荐格式
adb logcat -b main,system,crash -d
adb logcat -s TAG / TAG:D *:S
adb logcat --pid=$(adb shell pidof -s com.pkg)
adb logcat -G 16M                    # 扩 buffer
adb shell dumpsys meminfo/cpuinfo/gfxinfo/batterystats <pkg>
adb shell dumpsys activity exit-info <pkg>
adb shell dumpsys dropbox --print
adb shell dumpsys deviceidle force-idle / unforce
adb shell perfetto -o /data/misc/perfetto-traces/t -t 10s sched freq am wm gfx view
adb bugreport ./out                  # 全量现场（重武器）
```

### 8.6 端口与转发

```bash
adb forward tcp:6100 localabstract:scrcpy
adb forward --list / --remove-all
adb reverse tcp:8081 tcp:8081        # 设备 → 主机
adb reverse --list / --remove-all
```

### 8.7 环境变量

| 变量 | 作用 |
| --- | --- |
| `ANDROID_SERIAL` | 等价于 `-s`，CI 里最常用 |
| `ANDROID_ADB_SERVER_PORT` | 改默认 5037（隔离/多实例） |
| `ADB_VENDOR_KEYS` | 附加厂商公钥 |
| `ADB_LOCAL_TRANSPORT_MAX_PORT` | 调整设备端 TCP 端口扫描范围 |
| `ADB_TRACE` | 打印 adb 自身调试日志（如 `all`、`sockets`），排查 adb 问题终极手段 |

---

## 结语

ADB 的知识曲线很有意思：

- **第一层**（会用）：记住命令，能装能看日志。
- **第二层**（懂原理）：知道 client/server/adbd、5037/5555、PTY 与 `exec-out`、`forward`/`reverse`。
- **第三层**（能治理）：把 ADB 当作需要被调度、隔离、自愈、可观测的资源，用分层退出码和 SLO 把它变成可信赖的基础设施。

绝大多数人停在第一层。面试和职场里真正拉开差距的，是从第二层往第三层走的那段路——而这段路，恰恰就是本文第 5 章和第 6.3、6.4 节的内容。
