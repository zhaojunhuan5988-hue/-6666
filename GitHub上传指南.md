# GitHub 上传指南

## 第一步：注册 GitHub 账号

1. 打开 https://github.com
2. 点击 **Sign up**（注册）
3. 输入邮箱地址，点击 **Continue**
4. 设置密码（至少8位，包含数字和字母）
5. 设置用户名（这是您的GitHub ID）
6. 验证邮箱（会收到验证邮件）
7. 完成注册！

---

## 第二步：创建新仓库

1. 登录 GitHub 后，点击右上角 **+** 号
2. 选择 **New repository**
3. 填写：
   - **Repository name**: `factory-erp`（或您喜欢的名字）
   - **Description**: `物料出入库智能化管理系统`
   - 选择 **Public**（公开）
   - **不要**勾选 "Add a README file"（代码已有）
4. 点击 **Create repository**

---

## 第三步：上传代码

### 方法一：上传文件夹（简单推荐）

1. 在新建的仓库页面，点击 **uploading an existing file**
2. 打开文件资源管理器
3. 导航到 `C:\Users\13662\WorkBuddy\2026-05-06-task-1\factory-erp`
4. **全选所有文件**（Ctrl+A）
5. 拖拽到 GitHub 上传区域
6. 点击 **Commit changes**

### 方法二：使用命令行

1. 打开 Git Bash 或 PowerShell
2. 运行以下命令：

```bash
# 进入项目目录
cd "C:\Users\13662\WorkBuddy\2026-05-06-task-1\factory-erp"

# 初始化Git（如果还没有）
git init

# 添加所有文件
git add .

# 提交
git commit -m "Initial commit - 物料出入库系统"

# 添加远程仓库（替换 YOUR_USERNAME 为您的GitHub用户名）
git remote add origin https://github.com/YOUR_USERNAME/factory-erp.git

# 推送
git branch -M main
git push -u origin main
```

---

## 第四步：确认上传成功

刷新GitHub页面，应该能看到所有文件了：
- ✅ app.py
- ✅ requirements.txt
- ✅ Procfile
- ✅ .gitignore
- ✅ static/
- ✅ templates/
- ✅ db/
- ✅ 其他文件

---

## 常见问题

### Q: 上传后看不到代码？
A: 确保点击了 "Commit changes" 按钮

### Q: 提示需要登录？
A: 在浏览器中确认已登录GitHub

### Q: 文件夹是空的？
A: 确保进入了正确的目录 `factory-erp`

---

## 下一步

上传完成后告诉我，我会帮您部署到 Render！
