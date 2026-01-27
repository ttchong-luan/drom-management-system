import os
import logging
from datetime import datetime
from flask import Flask, flash,render_template, request, redirect, url_for, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required,current_user
from sqlalchemy import UniqueConstraint
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Pagination

# 配置详细日志
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

app = Flask(__name__)
app.secret_key = 'dormitory_management_secret_key'

# 数据库配置 - 使用您的实际凭据
app.config['SQLALCHEMY_DATABASE_URI'] = (
    'mssql+pyodbc://sa:li035492@LAPTOP-5OJPUNBJ/学生公寓管理?' 
    'driver=ODBC+Driver+17+for+SQL+Server&'
    'autocommit=True&charset=utf8'  # 指定编码为 UTF-8
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True  # 显示所有SQL查询

db = SQLAlchemy(app)
# 初始化 Flask-Login

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # 设置登录页面的路由
login_manager.login_message = '请先登录以访问此页面'
# 测试数据库连接
try:
    with app.app_context():
        db.engine.connect()
        print(" 数据库连接成功!")
except Exception as e:
    print(f" x 数据库连接失败: {str(e)}")


# 数据模型定义
class User(UserMixin, db.Model):
    __tablename__ = '用户'
    username = db.Column(db.String(10), primary_key=True)
    userpw = db.Column(db.String(10), nullable=False)
    userpower = db.Column(db.String(20), nullable=False)

    # Flask-Login 要求用户模型有 get_id() 方法
    def get_id(self):
        return self.username  # 使用 username 作为用户ID

# 用户加载回调函数
@login_manager.user_loader
def load_user(username):
    return User.query.filter_by(username=username.strip()).first()

class Student(db.Model):
    __tablename__ = '学生'
    stu_sno = db.Column(db.String(10), primary_key=True)
    stu_name = db.Column(db.String(10), nullable=False)
    stu_sex = db.Column(db.String(2))
    stu_age = db.Column(db.Integer)
    stu_entrance = db.Column(db.Date)
    stu_grade = db.Column(db.String(10))
    stu_dept = db.Column(db.String(20))
    stu_class = db.Column(db.String(10))
    stu_tel = db.Column(db.String(30), nullable=False)
    checkin = db.relationship('CheckIn', backref='student', uselist=False)

class Building(db.Model):
    __tablename__ = '公寓楼'
    bui_bno = db.Column(db.String(10), primary_key=True)
    bui_floornum = db.Column(db.Integer)
    bui_dornum = db.Column(db.Integer)
    bui_livesex = db.Column(db.String(2))
    Admin_ano = db.Column(db.String(10), db.ForeignKey('管理员.Admin_ano'), name='Admin_ano')

class Dormitory(db.Model):
    __tablename__ = '寝室'
    dor_dno = db.Column(db.String(10), primary_key=True)
    dor_price = db.Column(db.Float)
    dor_fact = db.Column(db.Integer)
    dor_num = db.Column(db.Integer)
    bui_bno = db.Column(db.String(10), db.ForeignKey('公寓楼.bui_bno'))
    dor_ds = db.Column(db.String(50))
class CheckIn(db.Model):
    __tablename__ = '入住'
    record_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    stu_sno = db.Column(db.String(10), db.ForeignKey('学生.stu_sno'))
    dor_dno = db.Column(db.String(10), db.ForeignKey('寝室.dor_dno'))
    checkin_date = db.Column(db.Date, nullable=False)
    __table_args__ = (
        UniqueConstraint('stu_sno', 'dor_dno', 'checkin_date'),
    )

class Admin(db.Model):
    __tablename__ = '管理员'
    Admin_ano = db.Column(db.String(10), primary_key=True)
    Admin_name = db.Column(db.String(10), nullable=False)  # 补充非空约束
    Admin_age = db.Column(db.Integer)
    Admin_sex = db.Column(db.String(2))
    Admin_tel = db.Column(db.String(30), nullable=False)  # 补充非空约束

    # 关键：关联用户表（一个管理员对应一个系统用户）
    user_id = db.Column(db.String(10), db.ForeignKey('用户.username'), unique=True)
    user = db.relationship('User', backref=db.backref('admin_info', uselist=False))

class Visitor(db.Model):
    __tablename__ = '来访人员'
    vis_ID = db.Column(db.String(20), primary_key=True)
    vis_name = db.Column(db.String(10))
    vis_relation = db.Column(db.String(20))
    vis_age = db.Column(db.Integer)
    vis_entime = db.Column(db.DateTime)
    vis_leatime = db.Column(db.DateTime)
    vis_host = db.Column(db.String(20))
    vis_tel = db.Column(db.String(20))
    vis_notes = db.Column(db.Text)


class Repair(db.Model):
    __tablename__ = '维修'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    stu_sno = db.Column(db.String(20), nullable=False)
    dor_dno = db.Column(db.String(20), nullable=False)
    ml_pro = db.Column(db.String(50), nullable=False)
    ml_repair = db.Column(db.String(20), default='未处理')
    ml_time = db.Column(db.DateTime, default=datetime.now)
    description = db.Column(db.Text)
    handler = db.Column(db.String(20))

class BuildingProperty(db.Model):
    __tablename__ = '公寓财产'
    pro_id = db.Column(db.String(20), primary_key=True, name='pro_id')
    name = db.Column(db.String(50), name='name')  # 名称
    model = db.Column(db.String(50), name='model')  # 型号
    location = db.Column(db.String(50), name='location')  # 位置
    status = db.Column(db.String(20), name='status')  # 状态
    bpro_time = db.Column(db.DateTime, name='bpro_time')  # 时间
    Admin_ano = db.Column(db.String(10), db.ForeignKey('管理员.Admin_ano'), name='Admin_ano') # 管理员编号
    notes = db.Column(db.String(200), name='notes')  # 备注

# 登录和用户认证
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password').strip()
        print(f"尝试登录: 用户名={username}, 密码={password}")

        try:
            user = User.query.filter_by(username=username).first()

            if not user:
                flash('用户名或密码错误!', 'danger')
                return render_template('login.html')

            print(f"找到用户: {user.username}, 密码={user.userpw}")

            if user.userpw.strip() == password:
                # 使用 Flask-Login 的 login_user 函数登录用户
                login_user(user)
                session['user_id'] = username
                user_role = user.userpower.strip().lower()
                if user_role in {'管理员', 'admin', '超级管理员'}:
                    session['user_role'] = '管理员'
                else:
                    session['user_role'] = '学生'
                    session['student_id'] = password

                flash('登录成功!', 'success')
                print("登录成功，重定向到首页")
                return redirect(url_for('index'))
            else:
                flash('用户名或密码错误!', 'danger')
                print("用户名或密码错误")
        except Exception as error:
            print(f"数据库查询错误: {str(error)}")
            flash(f'数据库错误: {str(error)}', 'danger')

    return render_template('login.html')
ALLOWED_ROLES = {'管理员', 'admin', '超级管理员', '系统管理员'}
@app.route('/logout')
def logout():
    # 使用 Flask-Login 的 logout_user 函数登出用户
    logout_user()
    session.clear()  # 清除所有会话数据
    flash('您已成功退出系统', 'success')
    return redirect(url_for('login'))

# 首页
@app.route('/')
@login_required
def index():
    print("当前会话内容:", dict(session))  # 开发环境调试用
    try:
        student_count = Student.query.count()
        dormitory_count = Dormitory.query.count()
        building_count = Building.query.count()

        today = datetime.now().date()
        # 确保 SQL Server 日期查询正确（之前的修复）
        today_visitors = Visitor.query.filter(
            db.func.CAST(Visitor.vis_entime, db.DATE) == today
        ).count()

        pending_repairs = Repair.query.filter(Repair.ml_repair == '未处理').limit(5).all()
        recent_visitors = Visitor.query.order_by(Visitor.vis_entime.desc()).limit(5).all()

        return render_template(
            'index.html',
            student_count=student_count,
            dormitory_count=dormitory_count,
            building_count=building_count,
            today_visitors=today_visitors,
            pending_repairs=pending_repairs,
            recent_visitors=recent_visitors,
            now=datetime.now()
        )
    except Exception as error:
        # 捕获首页所有异常，避免 500 错误
        flash(f'首页加载失败: {str(error)}', 'danger')
        return redirect(url_for('login'))  # 异常时跳回登录页


@app.route('/students', methods=['GET'])
@login_required
def student_management():
    if session.get('user_role') == '学生':
        student_id = session.get('student_id')
        student = Student.query.get(student_id)
        if not student:
            flash('学生信息不存在', 'danger')
            return redirect(url_for('index'))

        class MockPagination(Pagination):
            def __init__(self, items):
                self.items = items
                self.page = 1
                self.per_page = 1
                self.total = 1
                self.pages = 1
                self.has_prev = False
                self.has_next = False

            @staticmethod
            def iter_pages():
                return [1]

        students = MockPagination([student])
        return render_template('student.html', students=students, is_student=True)
    page = request.args.get('page', 1, type=int)
    per_page = 10

    try:
        query = Student.query.order_by(Student.stu_sno)

        # 关键：使用与前端一致的参数名（stu_dept、stu_grade、stu_class）
        dept = request.args.get('stu_dept', '').strip()  # 接收 stu_dept 参数
        grade = request.args.get('stu_grade', '').strip()  # 接收 stu_grade 参数
        class_name = request.args.get('stu_class', '').strip()  # 接收 stu_class 参数
        dormitory = request.args.get('dor_dno', '').strip()

        # 应用筛选条件（去除空格，避免空字符串导致的筛选错误）
        if dept:
            query = query.filter(Student.stu_dept == dept)
        if grade:
            query = query.filter(Student.stu_grade == grade)
        if class_name:
            query = query.filter(Student.stu_class == class_name)
        if dormitory:  # 新增寝室筛选逻辑
            query = query.join(CheckIn).filter(CheckIn.dor_dno == dormitory)

        students = query.paginate(page=page, per_page=per_page, error_out=False)

        # 获取筛选列表（同上，保持不变）
        departments = [d.stu_dept for d in Student.query.with_entities(Student.stu_dept).distinct().all()]
        grades = [g.stu_grade for g in Student.query.with_entities(Student.stu_grade).distinct().all()]
        classes = [c.stu_class for c in Student.query.with_entities(Student.stu_class).distinct().all()]
        dormitories = [d.dor_dno for d in Dormitory.query.with_entities(Dormitory.dor_dno).distinct().all()]

        return render_template(
            'student.html',
            students=students,
            departments=departments,
            grades=grades,
            classes=classes,
            dormitories=dormitories,
            page=page,
            # 传递当前筛选条件到模板（使用处理后的参数）
            current_dept=dept,
            current_grade=grade,
            current_class=class_name,
            current_dormitory=dormitory,
            pagination=students
        )
    except Exception as error:
        app.logger.error(f"学生管理页面错误: {str(error)}")
        return render_template('500.html', now=datetime.now()), 500

# 获取单个学生信息
@app.route('/api/student/<sno>', methods=['GET'])
def api_get_student(sno):
    # 1. 校验登录状态（不依赖 @login_required，手动检查）
    if not current_user.is_authenticated:
        print("用户未登录")
        return jsonify({'error': '未登录'}), 401

    # 2. 处理角色空格（关键修复）
    user_role = session.get('user_role', '').strip().lower()  # 去除所有空格并转为小写
    print(f"处理后的角色: {user_role}")  # 调试用

    # 3. 放宽角色校验（支持 'admin' 或 '管理员'）
    if user_role not in ['admin', '管理员']:
        print(f"权限不足，当前角色: {user_role}")
        return jsonify({'error': '权限不足'}), 403

    # 4. 查询学生
    student = Student.query.get(sno)
    if not student:
        app.logger.warning(f"学生 {sno} 不存在")
        return jsonify({'error': f'学号 {sno} 不存在'}), 404

    # 5. 返回数据
    response_data = {
        'sno': student.stu_sno,
        'name': student.stu_name,
        'sex': student.stu_sex,
        'age': student.stu_age,
        'entrance': student.stu_entrance.strftime('%Y-%m-%d') if student.stu_entrance else '',
        'grade': student.stu_grade,
        'dept': student.stu_dept,
        'class': student.stu_class,
        'tel': student.stu_tel
    }
    app.logger.info(f"返回学生数据: {response_data}")
    return jsonify(response_data)


@app.route('/api/students', methods=['GET'])
@login_required
def api_search_students():
    query = request.args.get('query', '').strip()
    if not query:
        return jsonify([])

    # 查询学号或姓名匹配的学生
    students = Student.query.filter(
        (Student.stu_sno.ilike(f'%{query}%')) |
        (Student.stu_name.ilike(f'%{query}%'))
    ).limit(10).all()

    results = [{
        'sno': s.stu_sno,
        'name': s.stu_name,
        'dorm': s.checkin.dor_dno if s.checkin else '未分配'
    } for s in students]

    return jsonify(results)

@app.route('/add_student', methods=['POST'])
@login_required  # 自动校验登录状态，未登录会跳转或返回401
def add_student():
    # 此时已确保用户已登录，无需再检查 'user_id' in session
    try:
        # 权限校验（基于角色）
        user_role = session.get('user_role', '').strip().lower()
        # 注意：日志中角色是 'admin               '（带空格的 'admin'）
        if user_role not in ['管理员', 'admin']:  # 兼容两种角色值
            return jsonify({'success': False, 'message': '权限不足'}), 403

        # 处理添加学生逻辑
        stu_sno = request.form.get('stu_sno', '').strip()
        if not stu_sno:
            return jsonify({'success': False, 'message': '学号不能为空'}), 400

        # 检查学号是否存在
        if Student.query.get(stu_sno):
            return jsonify({'success': False, 'message': f'学号 {stu_sno} 已存在'}), 400

            # 获取寝室信息
        dor_dno = request.form.get('dor_dno', '').strip()
        if not dor_dno:
            return jsonify({'success': False, 'message': '请选择寝室'}), 400

            # 检查寝室是否存在
        dormitory = Dormitory.query.get(dor_dno)
        if not dormitory:
            # 尝试用空格填充后再查询（模拟数据库存储方式）
            padded_dor_dno = dor_dno.ljust(20)  # 假设数据库字段长度为20
            dormitory = Dormitory.query.get(padded_dor_dno)
            if not dormitory:
                return jsonify({'success': False, 'message': f'寝室 {dor_dno} 不存在'}), 400
            else:
                dor_dno = padded_dor_dno

            # 检查寝室是否已满
        if dormitory.dor_fact >= dormitory.dor_num:
            return jsonify({'success': False, 'message': f'寝室 {dor_dno} 已满'}), 400

        # 创建学生记录
        new_student = Student(
            stu_sno=stu_sno,
            stu_name=request.form.get('stu_name', '').strip(),
            stu_sex=request.form.get('stu_sex', '').strip(),
            stu_age=int(request.form.get('stu_age', 0)) if request.form.get('stu_age') else None,
            stu_entrance=datetime.strptime(request.form.get('stu_entrance'), '%Y-%m-%d')
            if request.form.get('stu_entrance') else None,
            stu_grade=request.form.get('stu_grade', '').strip(),
            stu_dept=request.form.get('stu_dept', '').strip(),
            stu_class=request.form.get('stu_class', '').strip(),
            stu_tel=request.form.get('stu_tel', '').strip()
        )

        db.session.add(new_student)

        checkin_date = datetime.strptime(request.form.get('checkin_date'), '%Y-%m-%d')
        new_checkin = CheckIn(
            stu_sno=stu_sno,
            dor_dno=dor_dno,
            checkin_date=checkin_date
        )
        db.session.add(new_checkin)
        app.logger.info(f"即将插入学生记录: {new_student.__dict__}")
        app.logger.info(f"即将插入入住记录: {new_checkin.__dict__}")
        dormitory.dor_fact += 1
        db.session.commit()
        return jsonify({'success': True, 'message': '学生添加成功'}), 201

    except ValueError as error:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'参数错误：{str(error)}'}), 400
    except Exception as error:
        app.logger.error(f"添加学生时出现异常: {str(error)}")
        db.session.rollback()
        return jsonify({'success': False, 'message': f'服务器错误：{str(error)}'}), 500


@app.route('/edit_student', methods=['POST'])
@login_required
def edit_student():
    # 调试日志
    app.logger.info(f"接收到的表单数据: {request.form.to_dict()}")

    # 权限校验
    user_role = session.get('user_role', '未设置角色')
    if user_role.strip() not in ALLOWED_ROLES:
        app.logger.warning(f"权限不足: {user_role}")
        return jsonify({
            'success': False,
            'message': f'权限不足（需要角色：{ALLOWED_ROLES}，当前角色：{user_role}）'
        }), 403

    # 1. 获取并校验学号
    stu_sno = request.form.get('edit_stu_sno','').strip()
    app.logger.info(f"获取到的学号: {stu_sno}")
    if not stu_sno:
        app.logger.warning("学号为空")
        return jsonify({
            'success': False,
            'message': '学号不能为空',
            'field': 'edit_stu_sno'
        }), 400

    # 2. 获取其他字段
    stu_sno = request.form.get('edit_stu_sno', '').strip()
    stu_name = request.form.get('edit_stu_name', '').strip()
    stu_sex = request.form.get('edit_stu_sex', '').strip()
    stu_age = request.form.get('edit_stu_age')
    stu_entrance = request.form.get('edit_stu_entrance')
    stu_grade = request.form.get('edit_stu_grade', '').strip()
    stu_dept = request.form.get('edit_stu_dept', '').strip()
    stu_class = request.form.get('edit_stu_class', '').strip()
    stu_tel = request.form.get('edit_stu_tel', '').strip()

    # 3. 校验年龄格式
    app.logger.info(f"获取到的年龄: {stu_age}")
    if stu_age:
        try:
            stu_age = int(stu_age)
            if stu_age < 1 or stu_age > 100:
                raise ValueError("年龄必须在1-100之间")
        except (ValueError, TypeError) as error:
            app.logger.warning(f"年龄格式错误: {stu_age}")
            return jsonify({
                'success': False,
                'message': f'年龄格式错误：{str(error)}',
                'field': 'edit_stu_age',
                'value': stu_age
            }), 400

    # 4. 校验日期格式
    app.logger.info(f"获取到的入学日期: {stu_entrance}")
    if stu_entrance:
        try:
            stu_entrance = datetime.strptime(stu_entrance, '%Y-%m-%d')
        except ValueError as error:
            app.logger.warning(f"日期格式错误: {stu_entrance}")
            return jsonify({
                'success': False,
                'message': f'入学日期格式错误：{str(error)}，应为YYYY-MM-DD',
                'field': 'edit_stu_entrance',
                'value': stu_entrance
            }), 400

    # 5. 校验学生是否存在
    student = Student.query.get(stu_sno)
    if not student:
        app.logger.warning(f"学号不存在: {stu_sno}")
        return jsonify({
            'success': False,
            'message': f'学号 {stu_sno} 不存在'
        }), 404

    # 获取新寝室信息
    new_dor_dno = request.form.get('edit_dor_dno', '').strip()
    checkin_date = datetime.strptime(request.form.get('edit_checkin_date'), '%Y-%m-%d')

    # 查找新寝室
    new_dormitory = Dormitory.query.get(new_dor_dno)
    if not new_dormitory:
        return jsonify({'success': False, 'message': f'寝室 {new_dor_dno} 不存在'}), 400

    # 检查新寝室是否已满
    if new_dormitory.dor_fact >= new_dormitory.dor_num:
        return jsonify({'success': False, 'message': f'寝室 {new_dor_dno} 已满'}), 400

    # 获取原寝室信息
    old_dormitory = None
    if student.checkin:
        old_dormitory = Dormitory.query.get(student.checkin.dor_dno)

    # 6. 更新学生信息
    student.stu_sno = stu_sno
    student.stu_name = stu_name
    student.stu_sex = stu_sex
    student.stu_age = stu_age if stu_age else None
    student.stu_entrance = stu_entrance
    student.stu_grade = stu_grade
    student.stu_dept = stu_dept
    student.stu_class = stu_class
    student.stu_tel = stu_tel

    # 更新入住记录
    if student.checkin:  # 如果已有入住记录
        # 如果更换了寝室
        if student.checkin.dor_dno != new_dor_dno:
            # 原寝室人数减1
            if old_dormitory and old_dormitory.dor_fact > 0:
                old_dormitory.dor_fact -= 1

            # 新寝室人数加1
            new_dormitory.dor_fact += 1

            # 更新入住记录
            student.checkin.dor_dno = new_dor_dno
            student.checkin.checkin_date = checkin_date
        else:
            # 只更新入住日期
            student.checkin.checkin_date = checkin_date
    else:  # 如果没有入住记录
        # 创建新入住记录
        new_checkin = CheckIn(
            stu_sno=stu_sno,
            dor_dno=new_dor_dno,
            checkin_date=checkin_date
        )
        db.session.add(new_checkin)
        # 新寝室人数加1
        new_dormitory.dor_fact += 1

    try:
        db.session.commit()
        app.logger.info(f"学生信息更新成功: {stu_sno}")
        return jsonify({'success': True, 'message': '修改成功'}), 200
    except Exception as error:
        db.session.rollback()
        app.logger.error(f"数据库错误: {str(error)}")
        return jsonify({
            'success': False,
            'message': f'数据库错误：{str(error)}'
        }), 500


@app.route('/delete_student/<sno>', methods=['DELETE'])  # 支持 DELETE 方法
@login_required
def delete_student(sno):
    try:
        # 权限校验（如需要）
        if session.get('user_role', '').strip() not in ALLOWED_ROLES:
            return jsonify({
                'success': False,
                'message': '权限不足，无法删除学生'
            }), 403

        # 查找学生
        student = Student.query.get(sno)
        if not student:
            return jsonify({
                'success': False,
                'message': f'学号 {sno} 不存在'
            }), 404

        # 获取入住记录
        checkin = CheckIn.query.filter_by(stu_sno=sno).first()

        # 如果有关联的入住记录
        if checkin:
            # 获取寝室并更新人数
            dormitory = Dormitory.query.get(checkin.dor_dno)
            if dormitory and dormitory.dor_fact > 0:
                dormitory.dor_fact -= 1

            # 删除入住记录
            db.session.delete(checkin)

        # 删除学生
        db.session.delete(student)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': '删除成功'
        }), 200

    except Exception as error:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'删除失败：{str(error)}'
        }), 500

# 寝室管理
@app.route('/dormitories')
@login_required
def dormitory_management():
    app.logger.info(f"当前 session: {session}")

    if 'user_id' not in session:
        app.logger.warning("用户未登录，重定向到登录页")
        return redirect(url_for('login'))
    # 获取分页参数（默认第1页，每页10条）
    page = request.args.get('page', 1, type=int)
    per_page = 10

    # 获取筛选参数（与前端表单name对应）
    building = request.args.get('bui_bno', '').strip()  # 楼栋号
    status = request.args.get('status', '').strip()  # 状态（可用/已满）

    # 构建查询
    query = Dormitory.query.order_by(Dormitory.dor_dno)  # 按寝室号排序

    # 应用筛选条件
    if building:
        query = query.filter(Dormitory.bui_bno == building)
    if status:
        if status == 'available':
            # 可用：实际入住 < 额定人数
            query = query.filter(Dormitory.dor_fact < Dormitory.dor_num)
        elif status == 'full':
            # 已满：实际入住 = 额定人数
            query = query.filter(Dormitory.dor_fact == Dormitory.dor_num)

    # 执行分页查询
    dormitories = query.paginate(page=page, per_page=per_page, error_out=False)

    # 获取用于筛选的楼栋列表（去重）
    buildings = [b.bui_bno for b in Dormitory.query.with_entities(Dormitory.bui_bno).distinct().all()]

    return render_template(
        'dormitory.html',  # 前端模板文件名
        dormitories=dormitories,  # 分页对象（含列表和分页信息）
        buildings=buildings,  # 楼栋列表（用于筛选）
        current_building=building,  # 当前选中的楼栋
        current_status=status,  # 当前选中的状态
        pagination=dormitories  # 分页对象（用于页码导航）
    )

@app.route('/add_dormitory', methods=['POST'])
@login_required
def add_dormitory():
    try:
        # 权限校验（基于角色）
        user_role = session.get('user_role', '').strip().lower()
        if user_role not in ['管理员', 'admin']:
            return jsonify({'success': False, 'message': '权限不足'}), 403

        # 处理添加寝室逻辑
        dor_dno = request.form.get('dor_dno', '').strip()
        if not dor_dno:
            return jsonify({'success': False, 'message': '寝室号不能为空'}), 400

        dormitory_id = request.form.get('dor_dno', '').strip()
        if Dormitory.query.get(dormitory_id):
            flash(f'寝室 {dormitory_id} 已存在', 'danger')
            return redirect(url_for('dormitory_management'))

        building_id = request.form.get('bui_bno', '').strip()
        if not Building.query.get(building_id):
            flash(f'公寓楼 {building_id} 不存在', 'danger')
            return redirect(url_for('dormitory_management'))
        # 创建寝室记录
        new_dormitory = Dormitory(
            dor_dno=dormitory_id,
            dor_price=float(request.form.get('dor_price', 0)),
            dor_fact=int(request.form.get('dor_fact', 0)),
            dor_num=int(request.form.get('dor_num', 0)),
            bui_bno=request.form.get('bui_bno', '').strip(),
            dor_ds=request.form.get('dor_ds', '').strip()
        )

        db.session.add(new_dormitory)
        db.session.commit()
        return jsonify({'success': True, 'message': '寝室添加成功'}), 201

    except ValueError as error:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'参数错误：{str(error)}'}), 400
    except Exception as error:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'服务器错误：{str(error)}'}), 500

@app.route('/api/dormitory/<dno>', methods=['GET'])
def api_get_dormitory(dno):
    if not current_user.is_authenticated:
        print("用户未登录")
        return jsonify({'error': '未登录'}), 401

    user_role = session.get('user_role', '').strip().lower()
    if user_role not in ['admin', '管理员']:
        print(f"权限不足，当前角色: {user_role}")
        return jsonify({'error': '权限不足'}), 403

    dormitory = Dormitory.query.get(dno)
    if not dormitory:
        app.logger.warning(f"寝室 {dno} 不存在")
        return jsonify({'error': f'寝室号 {dno} 不存在'}), 404

    response_data = {
        'dno': dormitory.dor_dno,
        'price': dormitory.dor_price,
        'fact': dormitory.dor_fact,
        'num': dormitory.dor_num,
        'bno': dormitory.bui_bno,
        'ds': dormitory.dor_ds
    }
    app.logger.info(f"返回寝室数据: {response_data}")
    return jsonify(response_data)


@app.route('/api/dormitories', methods=['GET'])
def api_get_dormitories():
    if not current_user.is_authenticated:
        return jsonify({'error': '未登录'}), 401

    user_role = session.get('user_role', '').strip().lower()
    if user_role not in ['admin', '管理员']:
        return jsonify({'error': '权限不足'}), 403

    try:
        # 查询所有寝室，只返回必要字段
        dormitories = Dormitory.query.with_entities(
            Dormitory.dor_dno,
            Dormitory.bui_bno,
            Dormitory.dor_fact,
            Dormitory.dor_num
        ).all()

        # 转换为字典列表
        dorm_list = [{
            'dno': d.dor_dno,
            'bno': d.bui_bno,
            'fact': d.dor_fact,
            'num': d.dor_num,
            'available': d.dor_num - d.dor_fact  # 计算可用床位
        } for d in dormitories]

        return jsonify(dorm_list)
    except Exception as error:
        app.logger.error(f"获取寝室列表失败: {str(error)}")
        return jsonify({'error': '服务器内部错误'}), 500
@app.route('/edit_dormitory', methods=['POST'])
@login_required
def edit_dormitory():
    app.logger.info(f"接收到的表单数据: {request.form.to_dict()}")

    user_role = session.get('user_role', '未设置角色')
    if user_role.strip() not in ['管理员', 'admin']:
        app.logger.warning(f"权限不足: {user_role}")
        return jsonify({
            'success': False,
            'message': f'权限不足（需要角色：管理员或admin，当前角色：{user_role}）'
        }), 403

    dor_dno = request.form.get('edit_dor_dno', '').strip()
    if not dor_dno:
        app.logger.warning("寝室号为空")
        return jsonify({
            'success': False,
            'message': '寝室号不能为空',
            'field': 'edit_dor_dno'
        }), 400

    dor_price = request.form.get('edit_dor_price')
    dor_fact = request.form.get('edit_dor_fact')
    dor_num = request.form.get('edit_dor_num')
    bui_bno = request.form.get('edit_bui_bno', '').strip()
    dor_ds = request.form.get('edit_dor_ds', '').strip()

    try:
        dor_price = float(dor_price) if dor_price else None
        dor_fact = int(dor_fact) if dor_fact else None
        dor_num = int(dor_num) if dor_num else None
    except (ValueError, TypeError) as error:
        app.logger.warning(f"数据格式错误: {error}")
        return jsonify({
            'success': False,
            'message': f'数据格式错误：{str(error)}',
            'field': 'data_format'
        }), 400

    dormitory = Dormitory.query.get(dor_dno)
    if not dormitory:
        app.logger.warning(f"寝室号不存在: {dor_dno}")
        return jsonify({
            'success': False,
            'message': f'寝室号 {dor_dno} 不存在'
        }), 404

    dormitory.dor_dno = dor_dno
    dormitory.dor_price = dor_price
    dormitory.dor_fact = dor_fact
    dormitory.dor_num = dor_num
    dormitory.bui_bno = bui_bno
    dormitory.dor_ds = dor_ds

    try:
        db.session.commit()
        app.logger.info(f"寝室信息更新成功: {dor_dno}")
        return jsonify({'success': True, 'message': '修改成功'}), 200
    except Exception as error:
        db.session.rollback()
        app.logger.error(f"数据库错误: {str(error)}")
        return jsonify({
            'success': False,
            'message': f'数据库错误：{str(error)}'
        }), 500

@app.route('/delete_dormitory/<dno>', methods=['DELETE'])
@login_required
def delete_dormitory(dno):
    try:
        # 权限校验（如需要）
        if session.get('user_role', '').strip() not in ALLOWED_ROLES:
            return jsonify({
                'success': False,
                'message': '权限不足，无法删除寝室'
            }), 403

        # 查找寝室
        dormitory = Dormitory.query.get(dno)
        if not dormitory:
            return jsonify({
                'success': False,
                'message': f'寝室号 {dno} 不存在'
            }), 404
        if dormitory.dor_fact > 0:
            return jsonify({
                'success': False,
                'message': '该寝室还有学生入住，无法删除'
            }), 400

        # 删除寝室
        db.session.delete(dormitory)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': '删除成功'
        }), 200

    except Exception as error:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'删除失败：{str(error)}'
        }), 500

@app.route('/buildings')
@login_required  # 确保登录验证
def building_management():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # 分页参数
    page = request.args.get('page', 1, type=int)
    per_page = 10  # 每页显示10条

    # 筛选参数（从请求中获取，默认空表示不筛选）
    live_sex = request.args.get('live_sex', '').strip()  # 按居住性别筛选

    # 基础查询
    query = Building.query.order_by(Building.bui_bno)

    # 应用筛选条件
    if live_sex:
        query = query.filter(Building.bui_livesex == live_sex)

    # 执行分页查询
    buildings = query.paginate(page=page, per_page=per_page, error_out=False)

    # 获取所有可选的居住性别（用于前端下拉框选项）
    sex_options = [
        item[0] for item in Building.query.with_entities(Building.bui_livesex).distinct().all()
    ]

    return render_template(
        'building.html',
        buildings=buildings,
        pagination=buildings,
        current_sex=live_sex,  # 当前选中的筛选条件（用于回显）
        sex_options=sex_options  # 所有可选的居住性别
    )

# 查询单个公寓楼
@app.route('/api/building/<bui_bno>', methods=['GET'])
def api_get_building(bui_bno):
    if not current_user.is_authenticated:
        print("用户未登录")
        return jsonify({'error': '未登录'}), 401

    user_role = session.get('user_role', '').strip().lower()
    print(f"处理后的角色: {user_role}")

    if user_role not in ['admin', '管理员']:
        print(f"权限不足，当前角色: {user_role}")
        return jsonify({'error': '权限不足'}), 403

    building = Building.query.get(bui_bno)
    if not building:
        app.logger.warning(f"公寓楼 {bui_bno} 不存在")
        return jsonify({'error': f'公寓楼编号 {bui_bno} 不存在'}), 404

    response_data = {
        'bui_bno': building.bui_bno,
        'bui_floornum': building.bui_floornum,
        'bui_dornum': building.bui_dornum,
        'bui_livesex': building.bui_livesex
    }
    app.logger.info(f"返回公寓楼数据: {response_data}")
    return jsonify(response_data)

# 添加公寓楼
@app.route('/add_building', methods=['POST'])
@login_required
def add_building():
    try:
        user_role = session.get('user_role', '').strip().lower()
        if user_role not in ['管理员', 'admin']:
            return jsonify({'success': False, 'message': '权限不足'}), 403

        bui_bno = request.form.get('bui_bno', '').strip()
        if not bui_bno:
            return jsonify({'success': False, 'message': '公寓楼编号不能为空'}), 400

        if Building.query.get(bui_bno):
            return jsonify({'success': False, 'message': f'公寓楼编号 {bui_bno} 已存在'}), 400

        new_building = Building(
            bui_bno=bui_bno,
            bui_floornum=int(request.form.get('bui_floornum', 0)),
            bui_dornum=int(request.form.get('bui_dornum', 0)),
            bui_livesex=request.form.get('bui_livesex', '').strip()
        )

        db.session.add(new_building)
        db.session.commit()
        return jsonify({'success': True, 'message': '公寓楼添加成功'}), 201

    except ValueError as error:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'参数错误：{str(error)}'}), 400
    except Exception as error:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'服务器错误：{str(error)}'}), 500

# 删除公寓楼
@app.route('/delete_building/<bui_bno>', methods=['DELETE'])
@login_required
def delete_building(bui_bno):
    try:
        if session.get('user_role', '').strip() not in ALLOWED_ROLES:
            return jsonify({
                'success': False,
                'message': '权限不足，无法删除公寓楼'
            }), 403

        building = Building.query.get(bui_bno)
        if not building:
            return jsonify({
                'success': False,
                'message': f'公寓楼编号 {bui_bno} 不存在'
            }), 404

        # 检查是否有寝室关联
        dormitories = Dormitory.query.filter_by(bui_bno=bui_bno).all()
        if dormitories:
            return jsonify({
                'success': False,
                'message': '该公寓楼下还有寝室，无法删除'
            }), 400

        db.session.delete(building)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': '删除成功'
        }), 200

    except Exception as error:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'删除失败：{str(error)}'
        }), 500

# 财产管理
# 公寓财产管理 - 列表与筛选
@app.route('/building_properties')
@login_required
def building_property_management():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    # 筛选参数
    status = request.args.get('status', '').strip()
    location = request.args.get('location', '').strip()

    query = BuildingProperty.query.order_by(BuildingProperty.pro_id)
    # 应用筛选
    if status:
        query = query.filter(BuildingProperty.status == status)
    if location:
        query = query.filter(BuildingProperty.location == location)

    properties = query.paginate(page=page, per_page=per_page, error_out=False)
    # 筛选选项
    status_options = [item[0] for item in BuildingProperty.query.with_entities(BuildingProperty.status).distinct().all()]
    location_options = [item[0] for item in BuildingProperty.query.with_entities(BuildingProperty.location).distinct().all()]

    return render_template(
        'building_property.html',
        properties=properties,
        pagination=properties,
        current_status=status,
        current_location=location,
        status_options=status_options,
        location_options=location_options,
        datetime=datetime
    )

# 公寓财产 - 获取单个详情
@app.route('/api/building_property/<pro_id>', methods=['GET'])
@login_required
def api_get_building_property(pro_id):
    user_role = session.get('user_role', '').strip().lower()
    if user_role not in ['admin', '管理员']:
        return jsonify({'error': '权限不足'}), 403

    prop = BuildingProperty.query.get(pro_id)
    if not prop:
        return jsonify({'error': f'财产ID {pro_id} 不存在'}), 404

    return jsonify({
        'pro_id': prop.pro_id,
        'name': prop.name,
        'model': prop.model,
        'location': prop.location,
        'status': prop.status,
        'bpro_time': prop.bpro_time.strftime('%Y-%m-%d') if prop.bpro_time else '',
        'Admin_ano': prop.Admin_ano,
        'notes': prop.notes
    })
# 公寓财产 - 添加
@app.route('/add_building_property', methods=['POST'])
@login_required
def add_building_property():
    user_role = session.get('user_role', '').strip().lower()
    if user_role not in ['admin', '管理员']:
        return jsonify({'success': False, 'message': '权限不足'}), 403

    try:
        pro_id = request.form.get('pro_id', '').strip()
        if not pro_id:
            return jsonify({'success': False, 'message': 'id不能为空'}), 400
        if BuildingProperty.query.get(pro_id):
            return jsonify({'success': False, 'message': f'财产ID {pro_id} 已存在'}), 400

        new_prop = BuildingProperty(
            pro_id=pro_id,
            name=request.form.get('name', '').strip(),
            model=request.form.get('model', '').strip(),
            location=request.form.get('location', '').strip(),
            status=request.form.get('status', '').strip(),
            bpro_time=datetime.strptime(request.form.get('bpro_time'), '%Y-%m-%d') if request.form.get('bpro_time') else datetime.now(),
            Admin_ano=session.get('user_id'),
            notes=request.form.get('notes', '').strip()
        )
        db.session.add(new_prop)
        db.session.commit()
        return jsonify({'success': True, 'message': '公寓财产添加成功'}), 201
    except Exception as error:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'添加失败：{str(error)}'}), 500

# 公寓财产 - 编辑
@app.route('/edit_building_property', methods=['POST'])
@login_required
def edit_building_property():
    if session.get('user_role', '').strip() not in ALLOWED_ROLES:
        return jsonify({'success': False, 'message': '权限不足'}), 403

    try:
        pro_id = request.form.get('pro_id', '').strip()
        prop = BuildingProperty.query.get(pro_id)
        if not prop:
            return jsonify({'success': False, 'message': f'财产ID {pro_id} 不存在'}), 404

        prop.name = request.form.get('name', '').strip()
        prop.model = request.form.get('model', '').strip()
        prop.location = request.form.get('location', '').strip()
        prop.status = request.form.get('status', '').strip()
        prop.notes = request.form.get('notes', '').strip()
        if request.form.get('bpro_time'):
            prop.bpro_time = datetime.strptime(request.form.get('bpro_time'), '%Y-%m-%d')

        db.session.commit()
        return jsonify({'success': True, 'message': '公寓财产更新成功'}), 200
    except Exception as error:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'更新失败：{str(error)}'}), 500

# 公寓财产 - 删除
@app.route('/delete_building_property/<prop_id>', methods=['DELETE'])
@login_required
def delete_building_property(pro_id):
    if session.get('user_role', '').strip() not in ALLOWED_ROLES:
        return jsonify({'success': False, 'message': '权限不足'}), 403

    try:
        prop = BuildingProperty.query.get(pro_id)
        if not prop:
            return jsonify({'success': False, 'message': f'财产ID {pro_id} 不存在'}), 404

        db.session.delete(prop)
        db.session.commit()
        return jsonify({'success': True, 'message': '公寓财产删除成功'}), 200
    except Exception as error:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'删除失败：{str(error)}'}), 500


# 出入登记
@app.route('/access')
@login_required
def access_management():
    try:
        visitors = Visitor.query.order_by(
            Visitor.vis_entime.desc()
        ).limit(50).all()

        # 处理空访客列表的情况，避免空IN查询
        student_ids = {v.vis_host for v in visitors if v.vis_host and v.vis_host.strip()}
        students = {}
        if student_ids:
            # 一次性查询所有关联学生，避免循环查询（优化效率）
            students = {s.stu_sno: s for s in Student.query.filter(
                Student.stu_sno.in_(student_ids)
            ).all()}

        return render_template(
            'access.html',
            visitors=visitors,
            students=students
        )

    except Exception as error:
        app.logger.error(f"访问管理页面错误: {str(error)}", exc_info=True)  # 记录完整堆栈
        return render_template('access.html', visitors=[], students={})
# 访客管理API
@app.route('/api/visitors', methods=['GET'])
@login_required
def api_get_visitors():
    try:
        # 获取分页参数（默认第1页，每页20条）
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        query = request.args.get('query', '').strip()
        status = request.args.get('status', 'all').strip().lower()

        # 构建基础查询（使用外连接保留所有访客）
        base_query = Visitor.query.outerjoin(
            Student, Visitor.vis_host == Student.stu_sno
        ).order_by(Visitor.vis_entime.desc())

        # 筛选条件：支持访客姓名、电话、学生学号/姓名
        if query:
            base_query = base_query.filter(
                db.or_(
                    Visitor.vis_name.ilike(f'%{query}%'),
                    Visitor.vis_tel.ilike(f'%{query}%'),
                    Student.stu_sno.ilike(f'%{query}%'),
                    Student.stu_name.ilike(f'%{query}%')
                )
            )

        # 状态筛选
        if status == 'active':
            base_query = base_query.filter(Visitor.vis_leatime.is_(None))
        elif status == 'departed':
            base_query = base_query.filter(Visitor.vis_leatime.isnot(None))

        # 执行分页查询
        pagination = base_query.paginate(page=page, per_page=per_page)
        visitors = pagination.items

        # 转换为响应数据（复用已关联的学生，避免重复查询）
        visitors_data = []
        for v in visitors:

            student = v.student if hasattr(v, 'student') else None
            visitors_data.append({
                'id': v.vis_ID,
                'name': v.vis_name,
                'relation': v.vis_relation,
                'age': v.vis_age,
                'host_sno': v.vis_host.strip() if (v.vis_host and v.vis_host.strip()) else None,
                'host_name': student.stu_name if student else None,
                'phone': v.vis_tel,
                'enter_time': v.vis_entime.isoformat() if v.vis_entime else None,
                'leave_time': v.vis_leatime.isoformat() if v.vis_leatime else None,
                'status': 'active' if v.vis_leatime is None else 'departed',
                'notes': v.vis_notes
            })

        return jsonify({
            'success': True,
            'data': visitors_data,
            'total': pagination.total,  # 总条数
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages  # 总页数
        })

    except Exception as error:
        app.logger.error(f"获取访客列表失败: {str(error)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': '获取数据失败',
            'error': str(error)
        }), 500

# 添加访客
@app.route('/add_visitor', methods=['POST'])
@login_required
def add_visitor():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '请提交JSON数据'}), 400

        # 验证必填字段
        required_fields = ['visitor_name', 'visitor_phone', 'visited_student', 'visit_time']
        for field in required_fields:
            if not data.get(field) or str(data.get(field)).strip() == '':
                return jsonify({'success': False, 'message': f'字段 {field} 不能为空'}), 400

        visited_sno = data['visited_student'].strip()
        student = Student.query.get(visited_sno)
        if not student:
            return jsonify({'success': False, 'message': f'被访学生 {visited_sno} 不存在'}), 400

        # 处理年龄
        vis_age = None
        if data.get('visitor_age'):
            try:
                vis_age = int(data['visitor_age'])
                if vis_age < 1 or vis_age > 120:
                    return jsonify({'success': False, 'message': '年龄必须在1-120之间'}), 400
            except ValueError:
                return jsonify({'success': False, 'message': '年龄必须是整数'}), 400

        # 处理来访时间（校验格式）
        try:
            vis_entime = datetime.fromisoformat(data['visit_time'])
        except ValueError:
            return jsonify({'success': False, 'message': '时间格式错误（需符合ISO 8601，如2025-07-09T12:00）'}), 400

        # 创建访客记录
        new_visitor = Visitor(
            vis_ID=f"V{datetime.now().strftime('%Y%m%d%H%M%S')}",
            vis_name=data['visitor_name'].strip(),
            vis_relation=data.get('visitor_relation', '').strip(),
            vis_age=vis_age,
            vis_entime=vis_entime,
            vis_leatime=None,
            vis_host=visited_sno,
            vis_tel=data['visitor_phone'].strip(),
            vis_notes=data.get('visit_notes', '').strip()
        )

        db.session.add(new_visitor)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '访客登记成功',
            'visitor_id': new_visitor.vis_ID
        })

    except ValueError as error:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'数据格式错误: {str(error)}'}), 400
    except IntegrityError as error:
        db.session.rollback()
        app.logger.error(f"访客ID重复: {str(error)}")
        return jsonify({'success': False, 'message': '登记失败，可能重复提交'}), 409  # 409冲突
    except Exception as error:
        db.session.rollback()
        app.logger.error(f"添加访客失败: {str(error)}", exc_info=True)
        return jsonify({'success': False, 'message': f'服务器错误: {str(error)}'}), 500

# 标记访客离开
@app.route('/mark_visitor_depart/<visitor_id>', methods=['POST'])
@login_required
def mark_visitor_depart(visitor_id):
    try:
        visitor = Visitor.query.get(visitor_id)
        if not visitor:
            return jsonify({
                'success': False,
                'message': '访客记录不存在'
            }), 404

        if visitor.vis_leatime is not None:
            return jsonify({
                'success': False,
                'message': '访客已标记离开'
            }), 400

        visitor.vis_leatime = datetime.now()
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '访客离开时间已记录'
        })

    except Exception as error:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'操作失败: {str(error)}'
        }), 500

# 删除访客记录
@app.route('/delete_visitor/<visitor_id>', methods=['DELETE'])
@login_required
def delete_visitor(visitor_id):
    try:
        # 权限校验
        if session.get('user_role', '').strip() not in ALLOWED_ROLES:
            return jsonify({
                'success': False,
                'message': '权限不足，无法删除访客记录'
            }), 403

        visitor = Visitor.query.get(visitor_id)
        if not visitor:
            return jsonify({
                'success': False,
                'message': '访客记录不存在'
            }), 404

        db.session.delete(visitor)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '访客记录已删除'
        })

    except Exception as error:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'删除失败: {str(error)}'
        }), 500
# 维修管理
@app.route('/repairs')
def repair_management():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    status = request.args.get('status', 'all')

    if status == 'pending':
        repairs = Repair.query.filter(
            Repair.ml_repair == '未处理'
        ).all()
    elif status == 'completed':
        repairs = Repair.query.filter(
            Repair.ml_repair == '已处理'
        ).all()
    else:
        repairs = Repair.query.all()

    return render_template(
        'repair.html',
        repairs=repairs,
        current_status=status
    )

# 添加维修记录
@app.route('/add_repair', methods=['POST'])
def add_repair():
    if 'user_id' not in session:
        flash('请先登录', 'danger')
        return redirect(url_for('login'))

    try:
        new_repair = Repair(
            stu_sno=session.get('user_id', ''),
            dor_dno=request.form['dor_dno'],
            ml_pro=request.form['ml_pro'],
            ml_repair='未处理',
            ml_time=datetime.now(),
            description=request.form['description']
        )

        db.session.add(new_repair)
        db.session.commit()
        flash('报修申请已提交', 'success')
    except Exception as error:
        db.session.rollback()
        flash(f'提交失败: {str(error)}', 'danger')

    return redirect(url_for('repair_management'))

# 删除维修记录
@app.route('/delete_repair/<repair_id>', methods=['DELETE'])
def delete_repair(repair_id):
    try:
        # 权限校验
        if session.get('user_role', '').strip() not in ALLOWED_ROLES:
            return jsonify({
                'success': False,
                'message': '权限不足，无法删除维修记录'
            }), 403

        # 查找维修记录
        repair = Repair.query.get(repair_id)
        if not repair:
            return jsonify({
                'success': False,
                'message': f'维修记录 {repair_id} 不存在'
            }), 404

        # 删除维修记录
        db.session.delete(repair)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': '删除成功'
        }), 200

    except Exception as error:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'删除失败：{str(error)}'
        }), 500

# 编辑维修记录
@app.route('/edit_repair', methods=['POST'])
def edit_repair():
    # 权限校验
    user_role = session.get('user_role', '未设置角色')
    if user_role.strip() not in ALLOWED_ROLES:
        return jsonify({
            'success': False,
            'message': f'权限不足（需要角色：{ALLOWED_ROLES}，当前角色：{user_role}）'
        }), 403

    # 获取并校验维修记录ID
    repair_id = request.form.get('repair_id')
    if not repair_id:
        return jsonify({
            'success': False,
            'message': '维修记录ID不能为空',
            'field': 'repair_id'
        }), 400

    # 获取其他字段
    dor_dno = request.form.get('dor_dno', '').strip()
    ml_pro = request.form.get('ml_pro', '').strip()
    ml_repair = request.form.get('ml_repair', '').strip()
    description = request.form.get('description', '').strip()

    # 校验维修记录是否存在
    repair = Repair.query.get(repair_id)
    if not repair:
        return jsonify({
            'success': False,
            'message': f'维修记录 {repair_id} 不存在'
        }), 404

    # 更新维修记录信息
    repair.dor_dno = dor_dno
    repair.ml_pro = ml_pro
    repair.ml_repair = ml_repair
    repair.description = description

    try:
        db.session.commit()
        return jsonify({'success': True, 'message': '修改成功'}), 200
    except Exception as error:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'数据库错误：{str(error)}'
        }), 500

# 获取单个维修记录
@app.route('/api/repair/<repair_id>', methods=['GET'])
@login_required
def api_get_repair(repair_id):
    # 处理角色空格
    user_role = session.get('user_role', '').strip().lower()

    # 放宽角色校验
    if user_role not in ['admin', '管理员']:
        return jsonify({'error': '权限不足'}), 403

    # 查询维修记录
    repair = Repair.query.get(repair_id)
    if not repair:
        return jsonify({'error': f'维修记录 {repair_id} 不存在'}), 404

    # 返回数据
    response_data = {
        'id': repair.id,
        'stu_sno': repair.stu_sno,
        'dor_dno': repair.dor_dno,
        'ml_pro': repair.ml_pro,
        'ml_repair': repair.ml_repair,
        'ml_time': repair.ml_time.strftime('%Y-%m-%d %H:%M:%S'),
        'description': repair.description,
        'handler': repair.handler
    }
    return jsonify(response_data)

# 系统管理
@app.route('/system')
def system_management():
    if 'user_id' not in session or session['user_role'] != '管理员':
        flash('无权访问此页面', 'danger')
        return redirect(url_for('index'))

    users = User.query.all()
    return render_template('system.html', users=users)

@app.route('/add_user', methods=['POST'])
@login_required  # 使用 Flask-Login 的认证机制
def add_user():
    # 检查用户权限
    if current_user.userpower != '管理员':
        flash('无权执行此操作', 'danger')
        return redirect(url_for('system_management'))

    # 获取表单数据
    username = request.form.get('username').strip()
    password = request.form.get('password').strip()
    role = request.form.get('role').strip()

    # 输入验证
    if not username or not password or not role:
        flash('用户名、密码和角色不能为空', 'danger')
        return redirect(url_for('system_management'))

    # 角色验证
    valid_roles = ['管理员', '普通用户', '宿管']
    if role not in valid_roles:
        flash('无效的角色选择', 'danger')
        return redirect(url_for('system_management'))

    # 检查用户名是否已存在
    if User.query.filter_by(username=username).first():
        flash('该用户名已存在', 'danger')
        return redirect(url_for('system_management'))

    try:

        db.session.commit()
        flash('用户添加成功', 'success')
    except IntegrityError:  # 专门处理数据库唯一约束冲突
        db.session.rollback()
        flash('该用户名已存在', 'danger')
    except Exception as error:
        db.session.rollback()
        app.logger.error(f"添加用户失败: {str(error)}")
        flash(f'添加失败: 服务器内部错误', 'danger')

    return redirect(url_for('system_management'))


@app.route('/update_user/<username>', methods=['POST'])
def update_user(username):
    if 'user_id' not in session or session['user_role'] != '管理员':
        flash('无权执行此操作', 'danger')
        return redirect(url_for('system_management'))

    user = User.query.filter_by(username=username).first_or_404()

    try:
        user.userpower = request.form['role']
        if request.form['password']:
            user.userpw = request.form['password']

        db.session.commit()
        flash('用户信息更新成功', 'success')
    except Exception as error:
        db.session.rollback()
        flash(f'更新失败: {str(error)}', 'danger')

    return redirect(url_for('system_management'))


@app.route('/delete_user/<username>')
def delete_user(username):
    if 'user_id' not in session or session['user_role'] != '管理员':
        flash('无权执行此操作', 'danger')
        return redirect(url_for('system_management'))

    if username == session['user_id']:
        flash('不能删除当前登录用户', 'danger')
        return redirect(url_for('system_management'))

    user = User.query.filter_by(username=username).first_or_404()

    try:
        db.session.delete(user)
        db.session.commit()
        flash('用户删除成功', 'success')
    except Exception as error:
        db.session.rollback()
        flash(f'删除失败: {str(error)}', 'danger')

    return redirect(url_for('system_management'))


@app.route('/backup_database')
def backup_database():
    if 'user_id' not in session or session['user_role'] != '管理员':
        return jsonify({'success': False, 'message': '无权执行此操作'}), 403

    try:
        # 创建备份文件
        backup_dir = "backups"
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        backup_file = os.path.join(backup_dir, f"backup_{datetime.now().strftime('%Y%m%d%H%M%S')}.bak")
        with open(backup_file, 'w') as f:
            f.write("Database backup content - this is just a demo")

        return jsonify({'success': True, 'message': f'数据库备份成功: {backup_file}'})
    except Exception as error:
        return jsonify({'success': False, 'message': f'备份失败: {str(error)}'})


# 获取寝室入住学生
@app.route('/dormitory_students/<dormitory_id>')
def dormitory_students(dormitory_id):
    checkins = CheckIn.query.filter_by(dor_dno=dormitory_id).all()
    students = []

    for checkin in checkins:
        student = Student.query.get(checkin.stu_sno)
        if student:
            students.append({
                'sno': student.stu_sno,
                'name': student.stu_name,
                'dept': student.stu_dept,
                'class': student.stu_class
            })

    return jsonify(students)


# 错误处理
@app.errorhandler(404)
def page_not_found():
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error():
    now = datetime.now()  # 定义 now 变量
    return render_template('500.html', now=now), 500


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    with app.test_request_context():
        print("所有注册的路由：")
        for rule in app.url_map.iter_rules():
            print(f"{rule.rule} -> {rule.endpoint} ({', '.join(rule.methods)})")
    app.run(debug=True, port=5000)