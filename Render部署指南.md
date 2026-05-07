# Render 部署指南

## 部署前准备

确保代码已上传到 GitHub（参考 GitHub上传指南.md）

---

## 第一步：注册 Render 账号

1. 打开 https://render.com
2. 点击 **Get Started** 或 **Sign Up**
3. 选择 **GitHub** 登录（推荐，更方便）
4. 授权 GitHub 访问
5. 完成注册！

---

## 第二步：创建 Web Service

1. 登录 Render 后，点击 **New +**
2. 选择 **Web Service**
3. 连接 GitHub 仓库：
   - 点击 **Connect GitHub**
   - 选择您的 `factory-erp` 仓库
   - 点击 **Connect**

---

## 第三步：配置部署

填写以下信息：

| 配置项 | 值 |
|--------|-----|
| **Name** | `factory-erp` |
| **Region** | Singapore（亚太地区，推荐）或 Oregon |
| **Branch** | `main` |
| **Root Directory** | （留空） |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn app:app --bind 0.0.0.0:$PORT` |
| **Plan** | `Free` |

---

## 第四步：环境变量（如需要）

点击 **Advanced**，然后 **Add Environment Variable**：

| Key | Value |
|-----|-------|
| `PYTHON_VERSION` | `3.11.0` |

---

## 第五步：部署

1. 点击 **Create Web Service**
2. 等待构建（约2-3分钟）
3. 看到绿色 "Live" 状态表示成功！
4. 会生成一个网址，如：`https://factory-erp.onrender.com`

---

## 恭喜！获得永久免费网址

```
https://factory-erp-xxxx.onrender.com
```

- ✅ 任意电脑都能打开
- ✅ 手机也能访问
- ✅ 电脑关闭也不影响
- ✅ 完全免费（每月750小时）
- ✅ 永久在线

---

## 注意事项

### 免费版休眠
Render 免费版如果30分钟没访问会自动休眠，下次访问会"冷启动"约30秒。

**解决方案**（可选）：
1. 注册 UptimeRobot 免费监控
2. 设置每25分钟ping一下网址
3. 这样就能保持一直在线

### 访问速度
Render 美国服务器，国内访问可能稍慢。如需更快速度：
- 换 Railway（亚太节点）
- 或使用 Vercel + 镜像

---

## 部署后验证

1. 打开生成的网址
2. 应该能看到 ERP 系统
3. 有默认数据（3个物料、2个仓库等）

---

## 后续更新代码

1. 修改本地代码
2. 推送到 GitHub
3. Render 会自动检测并重新部署

```bash
git add .
git commit -m "更新内容"
git push
```

---

## 遇到问题？

常见问题：
- **Build Failed**: 检查 requirements.txt 和 Procfile
- **Application Error**: 检查 app.py 是否有语法错误
- **数据库问题**: 云端会自动创建新数据库（无默认数据）

如有需要，随时告诉我错误信息！
