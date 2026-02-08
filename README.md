# 学生答题系统 - 部署指南

## 文件清单

### 后端文件
- ✅ `server.py` - Flask后端服务器
- ✅ `requirements.txt` - Python依赖
- ✅ `dashboard.html` - 管理员看板页面

### 前端文件
- ✅ `test.html` - 学生答题页面（需要修改）
- ⚠️ 需要修改test.html以支持数据提交

## 部署步骤

### 第一步：安装依赖

```bash
cd c:\Users\11367\Desktop\trae\class
pip install -r requirements.txt
```

### 第二步：启动后端服务器

```bash
python server.py
```

服务器将在 http://localhost:5000 启动

### 第三步：访问页面

- 学生答题页面：http://localhost:5000
- 管理员看板：http://localhost:5000/dashboard

## 前端代码修改说明

### 需要修改的位置

#### 1. 添加答题记录数组（约第274行）

在状态变量部分添加：
```javascript
let score = 0;
let userInfo = {};
let answers = [];  // 新增：记录每道题的对错情况
```

#### 2. 修改checkAnswer函数（约第317行）

在函数开始处添加答案记录：
```javascript
function checkAnswer(selectedIndex, btn) {
    if (isAnswered) return;
    isAnswered = true;

    const q = questions[currentQuestionIndex];
    const isCorrect = selectedIndex === q.correct;
    
    // 新增：记录答案
    answers.push(isCorrect);
    
    // ... 其余代码保持不变
}
```

#### 3. 修改showResult函数（约第363行）

在函数末尾添加数据提交：
```javascript
async function showResult() {
    quizScreen.classList.add('hidden');
    resultScreen.classList.remove('hidden');
    resultScreen.classList.add('fade-in');

    document.getElementById('result-user').textContent = `${userInfo.class} - ${userInfo.name}`;
    
    // 分数滚动动画
    anime({
        targets: { val: 0 },
        val: score,
        round: 1,
        duration: 1500,
        easing: 'easeOutExpo',
        update: function(anim) {
            document.getElementById('final-score').textContent = anim.animatables[0].target.val;
        }
    });

    // 评价语
    const comment = document.getElementById('score-comment');
    if (score === 100) comment.textContent = "太棒了！你是人脸识别专家！🌟";
    else if (score >= 80) comment.textContent = "成绩优秀！掌握得不错哦！👏";
    else if (score >= 60) comment.textContent = "及格啦！继续加油！💪";
    else comment.textContent = "还需要多复习一下相关知识哦 📚";
    
    // 新增：提交数据到后端
    await submitResult();
}

// 新增：提交结果函数
async function submitResult() {
    try {
        const response = await fetch('/api/submit', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                userInfo: userInfo,
                score: score,
                answers: answers,
                submitTime: new Date().toISOString()
            })
        });
        
        if (response.ok) {
            console.log('数据提交成功');
        } else {
            console.error('数据提交失败');
        }
    } catch (error) {
        console.error('提交数据时出错:', error);
    }
}
```

## API接口说明

### POST /api/submit
提交答题结果

**请求体**：
```json
{
  "userInfo": {
    "class": "七年级1班",
    "name": "张三",
    "number": "05"
  },
  "score": 80,
  "answers": [true, false, true, true, false],
  "submitTime": "2024-01-01T12:00:00.000Z"
}
```

**响应**：
```json
{
  "success": true,
  "id": 1,
  "message": "提交成功"
}
```

### GET /api/dashboard/stats
获取统计数据

**响应**：
```json
{
  "total_count": 10,
  "avg_score": 75.5,
  "max_score": 100,
  "pass_rate": 80.0,
  "score_distribution": [
    {"grade": "优秀", "count": 3},
    {"grade": "良好", "count": 2},
    {"grade": "中等", "count": 3},
    {"grade": "及格", "count": 1},
    {"grade": "不及格", "count": 1}
  ],
  "error_rates": [
    {"question": "第2题", "error_rate": 30.0},
    {"question": "第5题", "error_rate": 20.0}
  ]
}
```

### GET /api/dashboard/students
获取学生列表

**查询参数**：
- `class`: 班级筛选（可选）
- `page`: 页码（默认1）
- `per_page`: 每页数量（默认20）

**响应**：
```json
{
  "students": [
    {
      "id": 1,
      "class_name": "七年级1班",
      "student_name": "张三",
      "seat_number": "05",
      "score": 80,
      "answers": "[true,false,true,true,false]",
      "submit_time": "2024-01-01T12:00:00.000Z"
    }
  ],
  "pagination": {
    "total": 10,
    "page": 1,
    "per_page": 20,
    "total_pages": 1
  }
}
```

### DELETE /api/dashboard/students/<id>
删除学生记录

**响应**：
```json
{
  "success": true,
  "message": "删除成功"
}
```

## 数据库结构

### quiz_results 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| class_name | TEXT | 班级 |
| student_name | TEXT | 姓名 |
| seat_number | TEXT | 座号 |
| score | INTEGER | 得分 |
| answers | TEXT | 答题详情（JSON字符串） |
| submit_time | TEXT | 提交时间 |

## 功能特性

### 学生端
- ✅ 输入班级、姓名、座号
- ✅ 完成5道选择题
- ✅ 实时显示答题结果和解释
- ✅ 自动提交数据到后端

### 管理员端
- ✅ 统计概览（总人数、平均分、最高分、及格率）
- ✅ 分数段分布图
- ✅ 题目错误率统计
- ✅ 学生详细成绩列表
- ✅ 按班级筛选
- ✅ 分页显示
- ✅ 删除记录功能

## 测试流程

1. 启动后端服务器
2. 访问 http://localhost:5000
3. 输入学生信息并完成答题
4. 查看结果页面，确认数据提交成功
5. 访问 http://localhost:5000/dashboard
6. 查看统计数据和学生列表

## 注意事项

1. **前端修改**：必须修改test.html文件以支持数据提交
2. **数据库文件**：quiz_results.db会在首次运行时自动创建
3. **端口冲突**：如果5000端口被占用，修改server.py中的端口号
4. **CORS配置**：已启用CORS，支持跨域请求

## 常见问题

### Q: 如何修改题目？
A: 修改test.html中的questions数组即可。

### Q: 如何备份数据？
A: 复制quiz_results.db文件即可。

### Q: 如何清空所有数据？
A: 删除quiz_results.db文件，重启服务器会自动创建新的数据库。

### Q: 如何部署到服务器？
A: 可以使用Render、Heroku等平台部署Python Flask应用。