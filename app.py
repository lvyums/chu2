import json
import os
from flask import Flask, jsonify, request, render_template, url_for, send_from_directory
from flask_cors import CORS

# 指向 templates 文件夹
app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def get_file_path(filename):
    return os.path.join(BASE_DIR, filename)


def load_sites_data():
    file_path = get_file_path('sites.json')
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"读取 sites.json 失败: {e}")
        return {"error": "Data file not found", "center_point": {}, "sites": []}


def load_artifacts_data():
    file_path = get_file_path('artifacts.json')
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"读取 artifacts.json 失败: {e}")
        return []


# ===========================
# 1. 页面路由配置 (新增部分)
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
# 2. API 数据接口 (保持不变)
# ===========================

@app.route('/api/sites', methods=['GET'])
def get_map_data():
    data = load_sites_data()
    return jsonify(data)


@app.route('/api/sites/filter', methods=['GET'])
def filter_sites_by_year():
    year_param = request.args.get('year', type=int)
    if year_param is None:
        return jsonify({"error": "Missing year parameter"}), 400
    data = load_sites_data()
    all_sites = data.get('sites', [])
    filtered_sites = [site for site in all_sites if site.get('year', 0) <= year_param + 30]
    return jsonify({"count": len(filtered_sites), "sites": filtered_sites})


@app.route('/api/sites/<int:site_id>', methods=['GET'])
def get_site_detail(site_id):
    data = load_sites_data()
    sites = data.get('sites', [])
    target_site = next((site for site in sites if site['id'] == site_id), None)
    if target_site:
        return jsonify(target_site)
    else:
        return jsonify({"error": "Site not found"}), 404


@app.route('/api/artifacts', methods=['GET'])
def get_artifacts():
    data = load_artifacts_data()
    return jsonify(data)


# ===========================
# 3. 资料库文件服务
# ===========================

# 配置资料存放的真实路径
# 确保在你的项目里有一个 static 文件夹，里面有个 materials 文件夹
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


if __name__ == '__main__':
    # host='0.0.0.0' 允许外网/局域网访问
    # debug=False 关闭调试模式，生产环境建议关闭
    print(f"服务启动成功! 请访问: http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)