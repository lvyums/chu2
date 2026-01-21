import json
import os
from flask import Flask, jsonify, request, render_template, url_for, send_from_directory, redirect
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask import send_from_directory
import database
from database import db, CenterPoint, ArchaeologicalSite, QuizQuestion
# Admin imports moved to init_admin() in admin.py
# from flask_admin import Admin
# from flask_admin.contrib.sqla import ModelView
# from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

# 指向 templates 文件夹
app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

# 1. 优先读取环境变量 DATABASE_URL (Docker环境会传这个变量)
db_url = os.environ.get('DATABASE_URL')

# 2. 如果没读到 (说明是在本地直接运行，没有用 Docker)，就回退用 SQLite
if db_url is None:
    # 使用 instance 文件夹下的 chu.db
    db_path = os.path.join(app.instance_path, 'chu.db')
    # 确保 instance 目录存在
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    db_url = 'sqlite:///' + db_path

# 3. 将最终确定的数据库地址赋值给 Flask 配置
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev')
database.init_app(app)

# Admin initialization moved after route definitions to prevent routing conflicts

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def get_file_path(filename):
    return os.path.join(BASE_DIR, filename)


def load_sites_data():
    """从数据库加载遗址数据"""
    try:
        with app.app_context():
            # 获取中心点数据
            center_point = CenterPoint.query.first()
            center_point_data = center_point.to_dict() if center_point else {}

            # 获取所有遗址数据
            sites = ArchaeologicalSite.query.all()
            sites_data = [site.to_dict() for site in sites]

            return {
                "center_point": center_point_data,
                "sites": sites_data
            }
    except Exception as e:
        print(f"从数据库读取遗址数据失败: {e}")
        return {"error": "Database query failed", "center_point": {}, "sites": []}


def load_artifacts_data():
    """从JSON文件加载文物数据（暂未迁移到数据库）"""
    file_path = get_file_path('artifacts.json')
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"读取 artifacts.json 失败: {e}")
        return []


# ===========================
# 1. 页面路由配置
# ===========================

# 首页
@app.route('/')
@app.route('/index.html')
def index():
    return render_template('index.html')


# 时空地图页
@app.route('/map.html')
def map_page():
    return render_template('map.html')


# 文物图鉴页
@app.route('/gallery.html')
def gallery_page():
    return render_template('gallery.html')


# 资料库页
@app.route('/library.html')
def library_page():
    return render_template('library.html')


# 互动挑战页
@app.route('/game.html')
def game_page():
    return render_template('game.html')


# ===========================
# 2. API 数据接口
# ===========================

@app.route('/api/sites', methods=['GET'])
def get_map_data():
    """获取所有遗址数据"""
    data = load_sites_data()
    return jsonify(data)


@app.route('/api/sites/filter', methods=['GET'])
def filter_sites_by_year():
    """根据年份筛选遗址"""
    year_param = request.args.get('year', type=int)
    if year_param is None:
        return jsonify({"error": "Missing year parameter"}), 400

    try:
        with app.app_context():
            # 直接从数据库筛选数据
            filtered_sites = ArchaeologicalSite.query.filter(
                ArchaeologicalSite.year <= year_param + 30
            ).all()
            sites_data = [site.to_dict() for site in filtered_sites]
            return jsonify({"count": len(sites_data), "sites": sites_data})
    except Exception as e:
        print(f"数据库查询失败: {e}")
        return jsonify({"error": "Database query failed"}), 500


@app.route('/api/sites/<int:site_id>', methods=['GET'])
def get_site_detail(site_id):
    """获取特定遗址详情"""
    try:
        with app.app_context():
            site = ArchaeologicalSite.query.get(site_id)
            if site:
                return jsonify(site.to_dict())
            else:
                return jsonify({"error": "Site not found"}), 404
    except Exception as e:
        print(f"数据库查询失败: {e}")
        return jsonify({"error": "Database query failed"}), 500


@app.route('/api/artifacts', methods=['GET'])
def get_artifacts():
    data = load_artifacts_data()
    return jsonify(data)

@app.route('/quiz_questions.json')
def serve_quiz_json():
    # 允许浏览器读取根目录下的 quiz_questions.json
    return send_from_directory('.', 'quiz_questions.json')


@app.route('/api/quiz-questions', methods=['GET'])
def get_quiz_questions():
    """获取5道随机题库题目"""
    try:
        with app.app_context():
            questions = QuizQuestion.query.order_by(db.func.random()).limit(5).all()
            return jsonify([q.to_dict() for q in questions])
    except Exception as e:
        print(f"数据库查询失败: {e}")
        return jsonify({"error": "Database query failed"}), 500





# ===========================
# 3. 资料库文件服务
# ===========================

MATERIALS_FOLDER = os.path.join(app.static_folder, 'materials')


@app.route('/api/materials', methods=['GET'])
def list_materials():
    files_list = []

    # 检查文件夹是否存在，防止报错
    if not os.path.exists(MATERIALS_FOLDER):
        os.makedirs(MATERIALS_FOLDER)

    for filename in os.listdir(MATERIALS_FOLDER):
        if not filename.startswith('.'):
            file_url = url_for('static', filename=f'materials/{filename}')
            files_list.append({
                "name": filename,
                "type": filename.split('.')[-1].lower(),
                "url": file_url
            })

    return jsonify(files_list)


@app.route('/api/download/<path:filename>')
def download_file(filename):
    return send_from_directory(MATERIALS_FOLDER, filename, as_attachment=True)

# app.py
@app.route('/admin/static/<path:filename>.map')
def no_map(filename):
    return '', 204
# Removed deprecated before_first_request - tables created in main block

# Initialize admin after all route definitions to prevent routing conflicts
from admin import init_admin
init_admin(app)

if __name__ == '__main__':
    # host='0.0.0.0' 允许外网/局域网访问
    # debug=False 关闭调试模式，生产环境建议关闭
    with app.app_context():
        db.create_all()  # 确保在应用启动时创建表
    print(f"服务启动成功! 请访问: http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)