from flask import Flask, request, jsonify, render_template
import pandas as pd
import glob
import re
import logging
from pypinyin import lazy_pinyin, Style

app = Flask(__name__)

# 读取所有xlsx文件并合并数据
def load_data():
    all_files = glob.glob("data/*.json")
    df_list = []
    for file in all_files:
        print(f'Reading {file}')
        df = pd.read_json(file)
        df_list.append(df)
    combined_df = pd.concat(df_list, ignore_index=True)
    return combined_df

data = load_data()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search/teacher', methods=['GET'])
def search_teacher():
    teacher_name = request.args.get('name')
    if not teacher_name:
        return jsonify({'error': 'Teacher name is required'}), 400
    
    # 精准匹配
    exact_match = data[data['教师'] == teacher_name]
    
    # 构建正则表达式模式，允许在字符之间有任意字符
    pattern = '.*'.join(teacher_name)
    regex = re.compile(pattern, re.IGNORECASE)
    
    # 模糊匹配
    partial_match = data[data['教师'].str.contains(regex, na=False) & (data['教师'] != teacher_name)]
    
    # 拼音首字母匹配
    def match_pinyin_initials(name, initials):
        if pd.isna(name):
            return False
        pinyin_initials = ''.join([p[0] for p in lazy_pinyin(name, style=Style.FIRST_LETTER)])
        return pinyin_initials.startswith(initials.lower())
    
    pinyin_match = data[data['教师'].apply(lambda x: match_pinyin_initials(x, teacher_name))]

    # 合并结果，精准匹配的结果在前
    result = pd.concat([exact_match, partial_match, pinyin_match]).drop_duplicates()
    result = result.apply(lambda x: x.dropna(), axis=1)
    
    if result.empty:
        return jsonify({'message': 'No courses found for this teacher'}), 404
    
    return result.to_json(orient='records', force_ascii=False)

@app.route('/search/course', methods=['GET'])
def search_course():
    course_name = request.args.get('name')
    if not course_name:
        return jsonify({'error': 'Course name is required'}), 400
    
    # 精准匹配
    exact_match = data[data['课程名称'] == course_name]
    
    # 构建正则表达式模式，允许在字符之间有任意字符
    pattern = '.*'.join(course_name)
    regex = re.compile(pattern)
    
    # 模糊匹配
    partial_match = data[data['课程名称'].str.contains(regex, na=False) & (data['课程名称'] != course_name)]
    
    # 合并结果，精准匹配的结果在前
    result = pd.concat([exact_match, partial_match])
    result = result.apply(lambda x: x.dropna(), axis=1)
    
    if result.empty:
        return jsonify({'message': 'No reviews found for this course'}), 404
    
    return result.to_json(orient='records', force_ascii=False)

if __name__ == '__main__':
    app.run(debug=True)