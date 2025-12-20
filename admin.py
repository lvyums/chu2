from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.theme import Bootstrap4Theme
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask import request, redirect, url_for, render_template_string, Blueprint
import os
from database import db, CenterPoint, ArchaeologicalSite, QuizQuestion

# 初始化登录管理器
login_manager = LoginManager()


# 管理员模型
class AdminUser(UserMixin):
    def __init__(self, id):
        self.id = id


@login_manager.user_loader
def load_user(user_id):
    return AdminUser(1) if user_id == '1' else None


# 1. 优化模型视图：添加搜索和过滤功能，使其更具"功能性"
class SecureModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin_auth.login', next=request.url))

    # 开启显示条目数自定义
    page_size = 20
    can_export = True  # 允许导出数据


# 2. 优化首页视图：注入统计数据
class SecureAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        if not current_user.is_authenticated:
            return redirect(url_for('admin_auth.login', next=request.url))

        # 获取统计数据
        site_count = ArchaeologicalSite.query.count()
        center_count = CenterPoint.query.count()
        quiz_count = QuizQuestion.query.count()

        # 渲染自定义的 dashboard 模板，并传入 quiz_count
        return self.render('admin/index.html',
                           site_count=site_count,
                           center_count=center_count,
                           quiz_count=quiz_count)


# 创建认证蓝图
admin_bp = Blueprint('admin_auth', __name__, url_prefix='/admin')


@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        admin_password = os.getenv('ADMIN_PASSWORD', '123456')
        if request.form.get('password') == admin_password:
            login_user(AdminUser(1))
            next_page = request.args.get('next', url_for('admin.index'))
            return redirect(next_page)

    # 稍微美化一下登录页
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>楚文化数据库 - 管理登录</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.6.0/dist/css/bootstrap.min.css">
        <style>
            body { background: #f4f6f9; display: flex; align-items: center; justify-content: center; height: 100vh; }
            .login-box { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); width: 100%; max-width: 400px; }
            .btn-primary { background-color: #2c3e50; border-color: #2c3e50; }
        </style>
    </head>
    <body>
        <div class="login-box">
            <h4 class="text-center mb-4">管理员登录</h4>
            <form method="POST">
                <div class="form-group">
                    <label>管理密码</label>
                    <input type="password" name="password" class="form-control" required>
                </div>
                <button type="submit" class="btn btn-primary btn-block">进入系统</button>
            </form>
        </div>
    </body>
    </html>
    ''')


@admin_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('admin_auth.login'))


def init_admin(app):
    app.register_blueprint(admin_bp)
    login_manager.init_app(app)
    login_manager.login_view = 'admin_auth.login'

    admin = Admin(
        app,
        name='楚文化数据库后台',
        url='/admin',
        index_view=SecureAdminIndexView(),
        theme=Bootstrap4Theme(swatch='flatly')
    )

    # 注册视图
    site_view = SecureModelView(ArchaeologicalSite, db.session, name='遗址列表', category='地图数据', endpoint='site_admin')
    try:
        site_view.column_searchable_list = ['name', 'location']
        site_view.column_filters = ['year']
    except:
        pass
    admin.add_view(site_view)

    # 中心点管理
    admin.add_view(SecureModelView(
        CenterPoint,
        db.session,
        name='中心点配置',
        category='地图数据',
        endpoint='center_admin'
    ))

    # 题库管理
    quiz_view = SecureModelView(QuizQuestion, db.session, name='题库管理', category='互动游戏', endpoint='quiz_admin')
    try:
        quiz_view.column_searchable_list = ['question', 'visual']
        quiz_view.column_filters = ['answer']
    except:
        pass
    admin.add_view(quiz_view)