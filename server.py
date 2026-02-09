from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import psycopg2
import json
from datetime import datetime
import os

app = Flask(__name__, static_folder='.')
CORS(app)

# 数据库连接配置
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://face_recognition_db_5xpi_user:Ore2mZISqtaMnrbqEEmEQzugO9EtRtJ0@dpg-d64qerggjchc739u73lg-a/face_recognition_db_5xpi')

def init_db():
    """初始化数据库"""
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quiz_results (
            id SERIAL PRIMARY KEY,
            class_name TEXT NOT NULL,
            student_name TEXT NOT NULL,
            seat_number TEXT NOT NULL,
            score INTEGER NOT NULL,
            answers TEXT NOT NULL,
            submit_time TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    """获取数据库连接"""
    return psycopg2.connect(DATABASE_URL)

@app.route('/')
def index():
    """首页"""
    return send_from_directory('.', 'test.html')

@app.route('/dashboard')
def dashboard():
    """管理员看板"""
    return send_from_directory('.', 'dashboard.html')

@app.route('/api/submit', methods=['POST'])
def submit_result():
    """提交答题结果"""
    try:
        data = request.json
        
        user_info = data.get('userInfo', {})
        score = data.get('score', 0)
        answers = data.get('answers', [])
        submit_time = data.get('submitTime', datetime.now().isoformat())
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO quiz_results (class_name, student_name, seat_number, score, answers, submit_time)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (
            user_info.get('class', ''),
            user_info.get('name', ''),
            user_info.get('number', ''),
            score,
            json.dumps(answers),
            submit_time
        ))
        
        conn.commit()
        result_id = cursor.lastrowid
        conn.close()
        
        return jsonify({
            'success': True,
            'id': result_id,
            'message': '提交成功'
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/dashboard/stats', methods=['GET'])
def get_stats():
    """获取统计数据"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 总参与人数
        cursor.execute('SELECT COUNT(*) as count FROM quiz_results')
        total_count = cursor.fetchone()[0]
        
        # 平均分
        cursor.execute('SELECT AVG(score) as avg_score FROM quiz_results')
        avg_score = cursor.fetchone()[0] or 0
        
        # 最高分
        cursor.execute('SELECT MAX(score) as max_score FROM quiz_results')
        max_score = cursor.fetchone()[0] or 0
        
        # 及格率（60分及以上）
        cursor.execute('SELECT COUNT(*) as count FROM quiz_results WHERE score >= 60')
        pass_count = cursor.fetchone()[0]
        pass_rate = (pass_count / total_count * 100) if total_count > 0 else 0
        
        # 分数段分布
        cursor.execute('''
            SELECT 
                CASE 
                    WHEN score >= 90 THEN '优秀'
                    WHEN score >= 80 THEN '良好'
                    WHEN score >= 70 THEN '中等'
                    WHEN score >= 60 THEN '及格'
                    ELSE '不及格'
                END as grade,
                COUNT(*) as count
            FROM quiz_results
            GROUP BY grade
            ORDER BY grade DESC
        ''')
        score_distribution = []
        for row in cursor.fetchall():
            score_distribution.append({'grade': row[0], 'count': row[1]})
        
        # 题目错误率统计
        cursor.execute('SELECT answers FROM quiz_results')
        all_answers = cursor.fetchall()
        
        question_stats = {}
        for row in all_answers:
            answers = json.loads(row[0])
            for i, is_correct in enumerate(answers):
                if i not in question_stats:
                    question_stats[i] = {'correct': 0, 'wrong': 0}
                if is_correct:
                    question_stats[i]['correct'] += 1
                else:
                    question_stats[i]['wrong'] += 1
        
        # 计算错误率
        error_rates = []
        for q_num, stats in question_stats.items():
            total = stats['correct'] + stats['wrong']
            error_rate = (stats['wrong'] / total * 100) if total > 0 else 0
            error_rates.append({
                'question': f'第{q_num + 1}题',
                'error_rate': round(error_rate, 2)
            })
        
        # 按错误率排序
        error_rates.sort(key=lambda x: x['error_rate'], reverse=True)
        
        conn.close()
        
        return jsonify({
            'total_count': total_count,
            'avg_score': round(avg_score, 2),
            'max_score': max_score,
            'pass_rate': round(pass_rate, 2),
            'score_distribution': score_distribution,
            'error_rates': error_rates
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/api/dashboard/students', methods=['GET'])
def get_students():
    """获取学生详细成绩列表"""
    try:
        # 获取查询参数
        class_filter = request.args.get('class')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 构建查询
        query = 'SELECT * FROM quiz_results'
        params = []
        
        if class_filter:
            query += ' WHERE class_name = %s'
            params.append(class_filter)
        
        query += ' ORDER BY submit_time DESC'
        
        # 获取总数
        count_query = query.replace('SELECT *', 'SELECT COUNT(*)')
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]
        
        # 分页
        offset = (page - 1) * per_page
        query += ' LIMIT %s OFFSET %s'
        params.extend([per_page, offset])
        
        cursor.execute(query, params)
        students = []
        for row in cursor.fetchall():
            students.append({
                'id': row[0],
                'class_name': row[1],
                'student_name': row[2],
                'seat_number': row[3],
                'score': row[4],
                'answers': row[5],
                'submit_time': row[6]
            })
        
        conn.close()
        
        return jsonify({
            'students': students,
            'pagination': {
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/api/dashboard/students/<int:id>', methods=['DELETE'])
def delete_student(id):
    """删除学生记录"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM quiz_results WHERE id = %s', (id,))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '删除成功'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
