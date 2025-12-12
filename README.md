# 楚文化时空考古数据库系统

## 项目简介

本系统是展示楚文化时空分布的交互式Web平台，以**时空可视化**为核心，整合考古遗址数据、文物信息和学术资源，呈现从西周至战国时期的楚文明发展脉络。系统采用现代Web技术栈构建，支持高效数据查询与动态可视化，适用于学术研究、文化展示和教育应用。

### 核心特性
- **时空可视化**：动态时间轴展示楚文化演变
- **结构化数据**：考古遗址、文物信息的标准化管理
- **多层验证**：坐标范围、年代范围自动校验
- **数据溯源**：完整的JSON备份与操作审计系统

### 技术栈
- **后端**：Flask + SQLAlchemy
- **数据库**：SQLite (开发) / PostgreSQL (生产)
- **前端**：HTML5 + JavaScript (Leaflet地图库)
- **部署**：Gunicorn + Nginx

---

## 生产环境 .env 配置指引

项目根目录下的 `.env` 文件用于存放**敏感配置**，**切勿提交到 Git**（已加入 `.gitignore`）。

### 必需字段

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| `DATABASE_URL` | 数据库连接串 | `sqlite:///production.db` |
| `ADMIN_PASSWORD` | 后台登录密码（≥20 位随机字符） | `sXRt9G3pQMVRKLnY8mTq` |
| `SECRET_KEY` | Flask session 密钥（64 位随机） | `qK3t7f9b3a0e...` |

### 一键生成随机值（PowerShell）

```powershell
# 生成 20 位安全密码
$rng = New-Object System.Security.Cryptography.RNGCryptoServiceProvider
$bytes = New-Object byte[] 15
$rng.GetBytes($bytes)
$env:ADMIN_PASSWORD = [Convert]::ToBase64String($bytes) -replace '[+/=]',''

# 生成 64 位 SECRET_KEY
$bytes = New-Object byte[] 48
$rng.GetBytes($bytes)
$env:SECRET_KEY = [Convert]::ToBase64String($bytes)

# 查看结果
echo $env:ADMIN_PASSWORD
echo $env:SECRET_KEY
---
```

## 部署到服务器


### 1. 环境准备

```bash
# 安装系统依赖
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv nginx postgresql

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装项目依赖
pip install -r requirements.txt
```

### 2. 数据库配置

```bash
# 创建PostgreSQL数据库
sudo -u postgres psql -c "CREATE DATABASE chu_db;"
sudo -u postgres psql -c "CREATE USER chu_user WITH PASSWORD 'secure_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE chu_db TO chu_user;"
```

编辑`.env`文件配置数据库连接：
```env
DATABASE_URL=postgresql://chu_user:secure_password@localhost/chu_db
```

### 3. 初始化系统

```bash
# 初始化数据库结构
python migrate.py init

# 迁移JSON数据到数据库
python migrate.py migrate

# 验证数据完整性
python migrate.py validate
```

### 4. 配置Web服务器

**Gunicorn服务配置** (`/etc/systemd/system/chu.service`):
```ini
[Unit]
Description=Chu Culture Web Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/project
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/gunicorn --workers 3 --bind unix:chu.sock app:app

[Install]
WantedBy=multi-user.target
```

**Nginx配置** (`/etc/nginx/sites-available/chu`):
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        include proxy_params;
        proxy_pass http://unix:/path/to/project/chu.sock;
    }

    location /static {
        alias /path/to/project/static;
    }
}
```

### 5. 启动服务

```bash
sudo systemctl start chu
sudo systemctl enable chu
sudo systemctl restart nginx
```

---

## 数据库日常维护

### 1. 添加新考古遗址

```bash
# 1. 编辑JSON源文件
nano sites.json

# 2. 添加新遗址示例
{
  "id": 101,
  "name": "新遗址名称",
  "loc": "现代城市名",
  "lat": 30.5,
  "lng": 114.3,
  "year": -600,
  "desc": "遗址详细描述..."
}

# 3. 执行数据迁移
python migrate.py migrate

# 4. 验证结果
python migrate.py validate
```

### 2. 数据验证与修复

```bash
# 验证坐标范围和年代约束
python migrate.py validate

# 自动修复无效坐标（示例）
python -c "import migrate; migrate.fix_invalid_coordinates()"
```

### 3. 数据备份与恢复

**自动备份**：
- 每日JSON备份存储在 `.json_history/` 目录
- 所有修改记录在 `data_audit.log`

**手动备份**：
```bash
# 备份当前数据库
cp chu.db chu_db_$(date +"%Y%m%d").bak

# 备份JSON源文件
cp sites.json .json_history/sites_$(date +"%Y%m%d").json
```

**从备份恢复**：
```bash
# 恢复特定日期的JSON数据
cp .json_history/sites_20251210.json sites.json

# 重新迁移数据
python migrate.py migrate
```

### 4. 管理后台操作

访问管理界面：`http://your-domain.com/admin`

**常用操作**：
- 查看/编辑考古遗址数据
- 管理中心点坐标
- 查看操作审计日志
- 执行数据库验证

> **注意**：直接通过管理后台修改数据库后，应同步更新JSON源文件以保持一致性

---

## 技术支持

- **问题排查**：检查 `data_audit.log` 和系统日志
- **性能优化**：对 `year` 和 `location` 字段建立索引
- **扩展建议**：
  - 将文物数据迁移到数据库
  - 增加Redis缓存层
  - 实现API速率限制