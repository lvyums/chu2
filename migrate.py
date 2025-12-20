#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库初始化和数据迁移脚本
"""

import sys
import os
import json
from app import app, db
from database import CenterPoint, ArchaeologicalSite, QuizQuestion

def init_db():
    """初始化数据库"""
    print("正在初始化数据库...")
    with app.app_context():
        # 创建所有表
        db.create_all()
        print("数据库表创建完成!")

def migrate_data():
    """从JSON文件迁移数据到数据库"""
    print("开始迁移数据...")

    with app.app_context():
        # 检查是否已有数据
        if CenterPoint.query.first() or ArchaeologicalSite.query.first():
            response = input("数据库中已存在数据，是否继续迁移？(y/N): ")
            if response.lower() != 'y':
                print("数据迁移取消")
                return

        # 读取sites.json文件
        sites_file = os.path.join(os.path.dirname(__file__), 'sites.json')
        try:
            with open(sites_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            print(f"错误: 找不到文件 {sites_file}")
            return
        except json.JSONDecodeError as e:
            print(f"错误: JSON解析失败 {e}")
            return

        # 迁移中心点数据
        center_point_data = data.get('center_point', {})
        if center_point_data:
            center_point = CenterPoint(
                name=center_point_data.get('name', ''),
                latitude=center_point_data.get('lat', 0),
                longitude=center_point_data.get('lng', 0),
                description=center_point_data.get('desc', '')
            )
            db.session.add(center_point)
            print(f"已迁移中心点: {center_point.name}")

        # 迁移遗址数据
        sites_data = data.get('sites', [])
        for site_data in sites_data:
            # Auto-generate ID to avoid uniqueness conflicts
            site = ArchaeologicalSite(
                name=site_data.get('name', ''),
                location=site_data.get('loc', ''),
                latitude=site_data.get('lat', 0),
                longitude=site_data.get('lng', 0),
                year=site_data.get('year', 0),
                description=site_data.get('desc', '')
            )
            db.session.add(site)
            print(f"已迁移遗址: {site.name}")

        # 提交事务
        db.session.commit()
        print(f"数据迁移完成! 共迁移 {len(sites_data)} 个遗址")

        # 迁移题库数据
        quiz_file = os.path.join(os.path.dirname(__file__), 'quiz_questions.json')
        if os.path.exists(quiz_file):
            try:
                with open(quiz_file, 'r', encoding='utf-8') as f:
                    quiz_data = json.load(f)

                for q in quiz_data:
                    quiz_question = QuizQuestion(
                        visual=q['visual'],
                        question=q['question'],
                        option1=q['options'][0],
                        option2=q['options'][1],
                        option3=q['options'][2],
                        option4=q['options'][3],
                        answer=q['answer'],
                        explanation=q['explanation']
                    )
                    db.session.add(quiz_question)

                db.session.commit()
                print(f"已迁移 {len(quiz_data)} 道题库题目")
            except Exception as e:
                print(f"题库数据迁移失败: {str(e)}")
        else:
            print("未找到 quiz_questions.json，跳过题库迁移")

def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python migrate.py init     # 初始化数据库")
        print("  python migrate.py migrate  # 迁移数据")
        print("  python migrate.py all      # 初始化数据库并迁移数据")
        return

    command = sys.argv[1]

    if command == 'init':
        init_db()
    elif command == 'migrate':
        migrate_data()
    elif command == 'all':
        init_db()
        migrate_data()
    else:
        print(f"未知命令: {command}")
        print("可用命令: init, migrate, all")

if __name__ == '__main__':
    main()