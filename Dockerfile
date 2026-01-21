# 1. 指定基础镜像
FROM python:3.10-slim

# 2. 设置工作目录
WORKDIR /app

# 3. 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 4. 复制依赖文件并安装
COPY requirements.txt .
# 这里的 pip 安装可能会慢，如果慢我们下一步再换源，先试试
RUN pip install --no-cache-dir -r requirements.txt && pip install gunicorn

# 5. 复制项目所有代码
COPY . .

# 6. 暴露端口
EXPOSE 5000

# 7. 启动命令
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]