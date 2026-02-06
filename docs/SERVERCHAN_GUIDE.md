# Server酱推送配置指南

本文档介绍如何配置 Server酱（ServerChan）微信推送功能。

## 什么是 Server酱？

Server酱是一个将消息推送到微信的服务，非常适合用于监控系统的实时通知。

- 官网：https://sct.ftqq.com/
- 免费版：每天 5 条消息（宿舍监控完全够用）
- 付费版：无限制（￥9.9/年）

## 配置步骤

### 1. 获取 SendKey

1. 访问 [Server酱官网](https://sct.ftqq.com/)
2. 使用微信扫码登录
3. 在「发送消息」页面找到你的 SendKey（格式：`SCT123456abcdef`）
4. 关注「Server酱Turbo」公众号（用于接收推送）

### 2. 配置项目

编辑项目根目录的 `.env` 文件：

```bash
# 启用 Server酱推送
NOTIFICATION_METHODS=serverchan

# 填写 SendKey
NOTIFICATION_SERVERCHAN_SENDKEY=SCT123456abcdef
```

### 3. 同时使用邮件和微信推送

如果你想同时使用邮件和 Server酱：

```bash
# 启用多种推送方式
NOTIFICATION_METHODS=email,serverchan

# 邮件配置
NOTIFICATION_SMTP_HOST=smtp.gmail.com
NOTIFICATION_SMTP_PORT=587
NOTIFICATION_SMTP_USE_TLS=true
NOTIFICATION_SMTP_USER=your_email@gmail.com
NOTIFICATION_SMTP_PASSWORD=your_app_password
NOTIFICATION_RECIPIENTS=recipient@example.com

# Server酱配置
NOTIFICATION_SERVERCHAN_SENDKEY=SCT123456abcdef
```

## 使用

### 测试推送

```bash
# 检查电量并发送告警（如果低于阈值）
emon alert

# 查看详细信息
emon alert --verbose
```

### 启动定时监控

```bash
# 启动定时任务，自动检测并推送
emon schedule
```

## 推送效果

电量告警推送示例：

```
🔴 宿舍电量紧急告警

## ⚡ 当前电量：8.5 度

**告警阈值：** 10.0 度
**检测时间：** 2026-02-05 20:30:00

📉 **电量趋势：** 快速下降 (-2.5 度/天)
💡 **日均消耗：** 2.5 度/天
⏱️ **预计剩余：** 3 天

---
**⚠️ 请及时充值，避免断电！**
```

推送延迟：通常 1-2 秒内送达微信，非常及时。

## 常见问题

### Q: 推送失败怎么办？

1. 检查 SendKey 是否正确
2. 确认已关注「Server酱Turbo」公众号
3. 查看日志文件 `data/logs/` 中的错误信息
4. 使用 `--verbose` 参数查看详细错误

### Q: 能否只使用 Server酱，不用邮件？

可以。设置 `NOTIFICATION_METHODS=serverchan` 即可。

### Q: 支持其他推送方式吗？

当前支持：
- ✅ 邮件（SMTP）
- ✅ Server酱（微信）

如需其他推送方式，欢迎提交 Issue 或 Pull Request。

## 技术实现

- API endpoint: `https://sctapi.ftqq.com/{SendKey}.send`
- 支持 Markdown 格式内容
- 自动重试机制
- 错误处理和日志记录

源码：[src/ecust_electricity_monitor/notifiers/serverchan.py](../src/ecust_electricity_monitor/notifiers/serverchan.py)

## 相关链接

- [Server酱官网](https://sct.ftqq.com/)
- [Server酱文档](https://sct.ftqq.com/sendkey)
- [项目 GitHub](https://github.com/DOHEX/ecust-dorm-electricity-monitor)


## 配置步骤

### 1. 获取 SendKey

1. 访问 [Server酱官网](https://sct.ftqq.com/)
2. 使用微信扫码登录
3. 在「发送消息」页面找到你的 SendKey（格式如：`SCT123456abcdef`）
4. 关注「Server酱Turbo」公众号，用于接收推送消息

### 2. 配置项目

有两种配置方式：

#### 方式一：`.env` 文件（推荐）

编辑项目根目录的 `.env` 文件，添加以下内容：

```bash
# 推送方式配置
NOTIFICATION_METHODS=serverchan

# Server酱配置
NOTIFICATION_SERVERCHAN_SENDKEY=SCT123456abcdef
```

#### 方式二：`config.toml` 文件

编辑 `config.toml` 文件：

```toml
[notification]
methods = "serverchan"
serverchan_sendkey = "SCT123456abcdef"
```

### 3. 同时使用邮件和 Server酱

如果你想同时使用邮件和 Server酱推送，配置如下：

```bash
# .env 文件
NOTIFICATION_METHODS=email,serverchan

# 邮件配置
NOTIFICATION_SMTP_HOST=smtp.gmail.com
NOTIFICATION_SMTP_PORT=587
NOTIFICATION_SMTP_USE_TLS=true
NOTIFICATION_SMTP_USER=your_email@gmail.com
NOTIFICATION_SMTP_PASSWORD=your_app_password
NOTIFICATION_RECIPIENTS=recipient@example.com

# Server酱配置
NOTIFICATION_SERVERCHAN_SENDKEY=SCT123456abcdef
```

## 使用示例

### 测试推送

配置完成后，运行以下命令测试告警功能：

```bash
# 检查电量并发送告警（如果电量低于阈值）
emon alert

# 强制发送告警邮件
emon alert --send-email
```

### 启动定时监控

```bash
# 启动定时监控，自动推送告警
emon schedule
```

## Server酱推送效果

电量告警推送示例：

```
🔴 宿舍电量紧急告警

## ⚡ 当前电量：8.5 度

**告警阈值：** 10.0 度
**检测时间：** 2026-02-05 20:30:00

📉 **电量趋势：** 快速下降 (-2.5 度/天)
💡 **日均消耗：** 2.5 度/天
⏱️ **预计剩余：** 3 天

---
**⚠️ 请及时充值，避免断电！**
```

## 免费额度

- **免费版**：每天 5 条消息
- **付费版**：无限制（￥9.9/年）

对于宿舍电量监控来说，免费版完全够用。

## 常见问题

### Q: 推送失败怎么办？

1. 检查 SendKey 是否正确
2. 确认已关注「Server酱Turbo」公众号
3. 查看日志文件 `data/logs/` 中的错误信息

### Q: 能否只使用 Server酱，不用邮件？

可以。设置 `NOTIFICATION_METHODS=serverchan` 即可。

### Q: 推送消息延迟多久？

通常在 1-2 秒内送达微信，非常及时。

### Q: 支持其他推送方式吗？

当前支持：
- ✅ 邮件（SMTP）
- ✅ Server酱（微信）

未来可能添加：
- 钉钉机器人
- 企业微信
- Telegram Bot

## 技术实现

项目使用 Server酱 Turbo 版 API：

- API endpoint: `https://sctapi.ftqq.com/{SendKey}.send`
- 支持 Markdown 格式内容
- 自动重试机制
- 错误处理和日志记录

详见源码：`src/ecust_electricity_monitor/notifier.py`

## 相关链接

- [Server酱官网](https://sct.ftqq.com/)
- [Server酱文档](https://sct.ftqq.com/sendkey)
- [项目 GitHub](https://github.com/yourusername/ecust-dorm-electricity-monitor)
