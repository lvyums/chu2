"""
数据库初始化和模型定义模块
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os
import secrets

# 初始化核心组件
db = SQLAlchemy()
login_manager = LoginManager()

# 注意：Admin 的初始化已经移动到 admin.py，这里不再保留

# ===== 1. 数据库模型定义 =====

class CenterPoint(db.Model):
    __tablename__ = 'center_points'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'description': self.description
        }

class ArchaeologicalSite(db.Model):
    __tablename__ = 'archaeological_sites'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, onupdate=db.func.current_timestamp())

    __table_args__ = (
        db.CheckConstraint('year BETWEEN -770 AND -221', name='valid_year_range'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'location': self.location,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'year': self.year,
            'description': self.description
        }


# ===== 2. 初始化函数 =====

def init_app(app: Flask):
    """初始化数据库配置"""
    # 配置密钥（用于Session）
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY') or secrets.token_hex(32)

    # 数据库配置
    basedir = os.path.abspath(os.path.dirname(__file__))
    # 优先读取环境变量，否则使用本地 sqlite
    db_uri = os.getenv('DATABASE_URL', f'sqlite:///{os.path.join(basedir, "chu.db")}')
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # 绑定扩展到 app
    db.init_app(app)

    # 配置登录管理（仅初始化，具体视图在 admin.py 中指定）
    login_manager.init_app(app)