#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
考试评分系统 (Exam Grading System)
====================================
A GUI application for teachers to grade student exam papers.
Built with tkinter (single-window, frame-switching architecture).

Roles:
  - Teacher:  grades assigned student papers (BiDao, JiaHao, WangBay)
  - Admin:    views overall progress, exports scores, clears/resets data
              (Chubbyemu / Shangbaida)

Scoring Rules:
  - 内容 (Content):    max 10 points, tiered A(9-10), B(7-8), C(5-6), D(3-4), E(0-2)
  - 语言 (Language):   max 10 points, tiered A(9-10), B(7-8), C(5-6), D(3-4), E(0-2)
  - 调整项 (Adjustment): max 5 points, tiered A(5), B(4), C(3), D(2), E(1)

Constraints:
  (i)  If Content + Language >= 15, then Adjustment must be 3-5; otherwise 0-3.
  (ii) Content and Language must be in the same tier or adjacent tiers.
"""

import tkinter as tk
from tkinter import messagebox, ttk
import json
import os
import random
import sys
import shutil
from datetime import datetime

# ======================== Constants ========================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEACHERS_FILE = os.path.join(BASE_DIR, 'teachers.json')
ADMIN_FILE = os.path.join(BASE_DIR, 'admin.json')
STUDENT_GRADES_FILE = os.path.join(BASE_DIR, 'student_grades.json')
PROGRESS_FILE = os.path.join(BASE_DIR, 'progress.json')
EXPORT_DIR = os.path.join(BASE_DIR, 'exports')

NUM_STUDENTS = 360
NUM_TEACHERS = 3
STUDENTS_PER_TEACHER = NUM_STUDENTS // NUM_TEACHERS  # 120

INITIAL_TEACHERS = ['BiDao', 'JiaHao', 'WangBay']
INITIAL_PASSWORD = '123456'

ADMIN_USERNAME = 'Chubbyemu'
ADMIN_PASSWORD = 'Shangbaida'

TIER_ORDER = {'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4}

SCORING_RULES_TEXT = """
════════════ 评分细则 ════════════
  等级   内容      语言      调整项
  A     9~10     9~10       5
  B     7~8      7~8        4
  C     5~6      5~6        3
  D     3~4      3~4        2
  E     0~2      0~2        1

约束 (i):  内容+语言 ≥ 15 → 调整项 3~5
          内容+语言 < 15 → 调整项 0~3
约束 (ii): 内容和语言必须同档或相邻档
═══════════════════════════════════
"""


# ======================== Scoring Logic ========================

def get_tier(score, is_adjustment=False):
    if is_adjustment:
        mapping = {5: 'A', 4: 'B', 3: 'C', 2: 'D', 1: 'E'}
        return mapping.get(score)
    else:
        if 9 <= score <= 10:
            return 'A'
        elif 7 <= score <= 8:
            return 'B'
        elif 5 <= score <= 6:
            return 'C'
        elif 3 <= score <= 4:
            return 'D'
        elif 0 <= score <= 2:
            return 'E'
        return None


def validate_scores(content, language, adjustment):
    for val in [content, language, adjustment]:
        if not isinstance(val, int):
            return False, "非法输入"

    if not (0 <= content <= 10):
        return False, "非法输入"
    if not (0 <= language <= 10):
        return False, "非法输入"
    if not (0 <= adjustment <= 5):
        return False, "非法输入"

    content_tier = get_tier(content, is_adjustment=False)
    language_tier = get_tier(language, is_adjustment=False)

    if content_tier is None or language_tier is None:
        return False, "非法输入"

    tier_diff = abs(TIER_ORDER[content_tier] - TIER_ORDER[language_tier])
    if tier_diff > 1:
        return False, "错误给分"

    total_cl = content + language
    if total_cl >= 15:
        if not (3 <= adjustment <= 5):
            return False, "错误给分"
    else:
        if not (0 <= adjustment <= 3):
            return False, "错误给分"

    return True, ""


# ======================== Data File Management ========================

def init_data_files():
    if not os.path.exists(ADMIN_FILE):
        _save_json(ADMIN_FILE, {'username': ADMIN_USERNAME, 'password': ADMIN_PASSWORD})
        print(f"[初始化] 已创建 {ADMIN_FILE}")

    if not os.path.exists(TEACHERS_FILE):
        teachers = {}
        for name in INITIAL_TEACHERS:
            teachers[name] = {'password': INITIAL_PASSWORD, 'first_login': True}
        _save_json(TEACHERS_FILE, teachers)
        print(f"[初始化] 已创建 {TEACHERS_FILE}")

    if not os.path.exists(STUDENT_GRADES_FILE):
        _initialize_student_grades()

    if not os.path.exists(PROGRESS_FILE):
        progress = {teacher: 0 for teacher in INITIAL_TEACHERS}
        _save_json(PROGRESS_FILE, progress)
        print(f"[初始化] 已创建 {PROGRESS_FILE}")

    if not os.path.exists(EXPORT_DIR):
        os.makedirs(EXPORT_DIR)
        print(f"[初始化] 已创建 {EXPORT_DIR}")


def _initialize_student_grades():
    all_students = [f'student_{i:03d}' for i in range(1, NUM_STUDENTS + 1)]
    random.shuffle(all_students)
    student_grades = {}
    for i, teacher in enumerate(INITIAL_TEACHERS):
        start_idx = i * STUDENTS_PER_TEACHER
        end_idx = start_idx + STUDENTS_PER_TEACHER
        student_grades[teacher] = {}
        for sid in all_students[start_idx:end_idx]:
            student_grades[teacher][sid] = {
                'content': None, 'language': None, 'adjustment': None
            }
    _save_json(STUDENT_GRADES_FILE, student_grades)
    print(f"[初始化] 已创建 {STUDENT_GRADES_FILE}")


def _load_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def _save_json(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ======================== Grading Statistics ========================

def count_graded_for_teacher(teacher_name, student_grades):
    count = 0
    if teacher_name not in student_grades:
        return 0
    for g in student_grades[teacher_name].values():
        if g['content'] is not None and g['language'] is not None and g['adjustment'] is not None:
            count += 1
    return count


def count_total_graded(student_grades):
    return sum(count_graded_for_teacher(t, student_grades) for t in INITIAL_TEACHERS)


def is_all_graded(student_grades):
    return count_total_graded(student_grades) == NUM_STUDENTS


# ======================== Export & Clear ========================

def export_all_scores():
    if not os.path.exists(STUDENT_GRADES_FILE):
        return None

    student_grades = _load_json(STUDENT_GRADES_FILE)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    export_data = {
        'export_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'exam_name': f'考试_{timestamp}',
        'total_students': NUM_STUDENTS,
        'teachers': {},
        'all_scores_flat': []
    }

    for teacher in INITIAL_TEACHERS:
        teacher_data = {}
        for sid, scores in student_grades.get(teacher, {}).items():
            c = scores.get('content')
            l = scores.get('language')
            a = scores.get('adjustment')
            total = (c or 0) + (l or 0) + (a or 0)

            record = {
                'student_id': sid,
                'teacher': teacher,
                'content': c,
                'language': l,
                'adjustment': a,
                'total': total,
                'content_tier': get_tier(c, False) if c is not None else None,
                'language_tier': get_tier(l, False) if l is not None else None,
                'adjustment_tier': get_tier(a, True) if a is not None else None,
            }
            teacher_data[sid] = record
            export_data['all_scores_flat'].append(record)

        graded = count_graded_for_teacher(teacher, student_grades)
        export_data['teachers'][teacher] = {
            'assigned': STUDENTS_PER_TEACHER,
            'graded': graded,
            'students': teacher_data
        }

    export_path = os.path.join(EXPORT_DIR, f'export_{timestamp}.json')
    _save_json(export_path, export_data)

    csv_path = os.path.join(EXPORT_DIR, f'export_{timestamp}.csv')
    with open(csv_path, 'w', encoding='utf-8-sig') as f:
        f.write('学号,评阅教师,内容(10),语言(10),调整项(5),总分(25),内容等级,语言等级,调整项等级\n')
        for record in export_data['all_scores_flat']:
            f.write(f"{record['student_id']},{record['teacher']},"
                    f"{record['content'] if record['content'] is not None else 'N/A'},"
                    f"{record['language'] if record['language'] is not None else 'N/A'},"
                    f"{record['adjustment'] if record['adjustment'] is not None else 'N/A'},"
                    f"{record['total']},"
                    f"{record['content_tier'] or 'N/A'},"
                    f"{record['language_tier'] or 'N/A'},"
                    f"{record['adjustment_tier'] or 'N/A'}\n")

    print(f"[导出] 成绩已导出到: {export_path}")
    print(f"[导出] CSV 摘要已导出到: {csv_path}")
    return export_path


def clear_grading_data():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = os.path.join(EXPORT_DIR, f'backup_before_clear_{timestamp}')

    try:
        os.makedirs(backup_dir, exist_ok=True)
        if os.path.exists(STUDENT_GRADES_FILE):
            shutil.copy2(STUDENT_GRADES_FILE, os.path.join(backup_dir, 'student_grades.json'))
        if os.path.exists(PROGRESS_FILE):
            shutil.copy2(PROGRESS_FILE, os.path.join(backup_dir, 'progress.json'))
        if os.path.exists(TEACHERS_FILE):
            shutil.copy2(TEACHERS_FILE, os.path.join(backup_dir, 'teachers.json'))
        print(f"[安全] 数据已备份到: {backup_dir}")

        if os.path.exists(STUDENT_GRADES_FILE):
            os.remove(STUDENT_GRADES_FILE)
        if os.path.exists(PROGRESS_FILE):
            os.remove(PROGRESS_FILE)

        _initialize_student_grades()
        progress = {teacher: 0 for teacher in INITIAL_TEACHERS}
        _save_json(PROGRESS_FILE, progress)

        print("[清空] 评分数据已清空，系统已重置为初始状态")
        return True
    except Exception as e:
        print(f"[错误] 清空数据失败: {e}")
        return False


# ======================== Application (Single-Window Frame-Switching) ========================

class App(tk.Tk):
    """Main application — owns the single root window and manages screen switching."""

    def __init__(self):
        super().__init__()
        self.title("考试评分系统")
        self.resizable(False, False)
        self.current_frame = None

        # Center on screen
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f'420x320+{(sw - 420) // 2}+{(sh - 320) // 2}')

        self.protocol('WM_DELETE_WINDOW', self._on_exit)

        # Start at role selection
        self.show_role_selection()

    def _clear_frame(self):
        if self.current_frame is not None:
            self.current_frame.destroy()
            self.current_frame = None

    def _set_window_size(self, w, h):
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f'{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}')

    def show_role_selection(self):
        self._clear_frame()
        self._set_window_size(420, 280)
        self.title("考试评分系统 — 角色选择")
        self.current_frame = RoleSelectionFrame(self)
        self.current_frame.pack(fill=tk.BOTH, expand=True)

    def show_teacher_login(self):
        self._clear_frame()
        self._set_window_size(420, 320)
        self.title("考试评分系统 — 教师登录")
        self.current_frame = TeacherLoginFrame(self)
        self.current_frame.pack(fill=tk.BOTH, expand=True)

    def show_admin_login(self):
        self._clear_frame()
        self._set_window_size(420, 280)
        self.title("考试评分系统 — 管理员登录")
        self.current_frame = AdminLoginFrame(self)
        self.current_frame.pack(fill=tk.BOTH, expand=True)

    def show_password_change(self, username, teachers_data):
        self._clear_frame()
        self._set_window_size(420, 300)
        self.title("首次登录 — 修改密码")
        self.current_frame = PasswordChangeFrame(self, username, teachers_data)
        self.current_frame.pack(fill=tk.BOTH, expand=True)

    def show_grading(self, username):
        self._clear_frame()
        self._set_window_size(620, 600)
        self.title(f"考试评分系统 — 欢迎，{username}")
        self.current_frame = GradingFrame(self, username)
        self.current_frame.pack(fill=tk.BOTH, expand=True)

    def show_admin_panel(self):
        self._clear_frame()
        self._set_window_size(580, 520)
        self.title("考试评分系统 — 管理员面板")
        self.current_frame = AdminPanelFrame(self)
        self.current_frame.pack(fill=tk.BOTH, expand=True)

    def _on_exit(self):
        self.destroy()
        sys.exit(0)


# ======================== Role Selection Frame ========================

class RoleSelectionFrame(tk.Frame):
    """First screen: choose Teacher or Admin login."""

    def __init__(self, app):
        super().__init__(app)
        self.app = app

        tk.Label(self, text="📝 考试评分系统", font=('Microsoft YaHei', 20, 'bold')).pack(pady=(40, 10))
        tk.Label(self, text="请选择登录身份", font=('Microsoft YaHei', 12), fg='#666666').pack(pady=(0, 30))

        btn_frame = tk.Frame(self)
        btn_frame.pack()

        tk.Button(btn_frame, text="👨‍🏫 教师登录", font=('Microsoft YaHei', 13, 'bold'),
                  width=16, height=2, bg='#0078D4', fg='white',
                  command=self._go_teacher).pack(side=tk.LEFT, padx=10)

        tk.Button(btn_frame, text="🔧 管理员登录", font=('Microsoft YaHei', 13, 'bold'),
                  width=16, height=2, bg='#107C10', fg='white',
                  command=self._go_admin).pack(side=tk.LEFT, padx=10)

        tk.Button(self, text="退出", font=('Microsoft YaHei', 10),
                  width=10, command=self.app._on_exit).pack(pady=(30, 0))

    def _go_teacher(self):
        self.app.show_teacher_login()

    def _go_admin(self):
        self.app.show_admin_login()


# ======================== Teacher Login Frame ========================

class TeacherLoginFrame(tk.Frame):
    """Teacher login screen."""

    def __init__(self, app):
        super().__init__(app)
        self.app = app

        tk.Label(self, text="👨‍🏫 教师登录", font=('Microsoft YaHei', 18, 'bold')).pack(pady=(30, 20))

        f1 = tk.Frame(self)
        f1.pack(pady=6)
        tk.Label(f1, text="用户名：", font=('Microsoft YaHei', 12), width=8).pack(side=tk.LEFT)
        self.entry_user = tk.Entry(f1, font=('Microsoft YaHei', 12), width=22)
        self.entry_user.pack(side=tk.LEFT)
        self.entry_user.focus_set()

        f2 = tk.Frame(self)
        f2.pack(pady=6)
        tk.Label(f2, text="密  码：", font=('Microsoft YaHei', 12), width=8).pack(side=tk.LEFT)
        self.entry_pass = tk.Entry(f2, font=('Microsoft YaHei', 12), width=22, show='*')
        self.entry_pass.pack(side=tk.LEFT)

        tk.Button(self, text="登  录", font=('Microsoft YaHei', 13, 'bold'),
                  width=16, bg='#0078D4', fg='white',
                  command=self._login).pack(pady=(20, 5))

        tk.Button(self, text="← 返回角色选择", font=('Microsoft YaHei', 9),
                  command=self.app.show_role_selection).pack(pady=(5, 0))

        self.bind_all('<Return>', lambda e: self._login())

    def _login(self):
        username = self.entry_user.get().strip()
        password = self.entry_pass.get().strip()

        if not username or not password:
            messagebox.showerror("错误", "请输入用户名和密码")
            return

        if username == ADMIN_USERNAME:
            messagebox.showerror("错误", "管理员请从管理员入口登录！")
            return

        teachers = _load_json(TEACHERS_FILE)

        if username not in teachers:
            messagebox.showerror("错误", "用户名不存在")
            return

        if password != teachers[username]['password']:
            messagebox.showerror("错误", "密码错误")
            return

        if teachers[username]['first_login']:
            self.app.show_password_change(username, teachers)
        else:
            self.app.show_grading(username)


# ======================== Admin Login Frame ========================

class AdminLoginFrame(tk.Frame):
    """Admin login screen."""

    def __init__(self, app):
        super().__init__(app)
        self.app = app

        tk.Label(self, text="🔧 管理员登录", font=('Microsoft YaHei', 18, 'bold')).pack(pady=(30, 20))

        f1 = tk.Frame(self)
        f1.pack(pady=6)
        tk.Label(f1, text="用户名：", font=('Microsoft YaHei', 12), width=8).pack(side=tk.LEFT)
        self.entry_user = tk.Entry(f1, font=('Microsoft YaHei', 12), width=22)
        self.entry_user.pack(side=tk.LEFT)
        self.entry_user.focus_set()

        f2 = tk.Frame(self)
        f2.pack(pady=6)
        tk.Label(f2, text="密  码：", font=('Microsoft YaHei', 12), width=8).pack(side=tk.LEFT)
        self.entry_pass = tk.Entry(f2, font=('Microsoft YaHei', 12), width=22, show='*')
        self.entry_pass.pack(side=tk.LEFT)

        tk.Button(self, text="登  录", font=('Microsoft YaHei', 13, 'bold'),
                  width=16, bg='#107C10', fg='white',
                  command=self._login).pack(pady=(20, 5))

        tk.Button(self, text="← 返回角色选择", font=('Microsoft YaHei', 9),
                  command=self.app.show_role_selection).pack(pady=(5, 0))

        self.bind_all('<Return>', lambda e: self._login())

    def _login(self):
        username = self.entry_user.get().strip()
        password = self.entry_pass.get().strip()

        if not username or not password:
            messagebox.showerror("错误", "请输入用户名和密码")
            return

        if username != ADMIN_USERNAME:
            messagebox.showerror("错误", "教师请从教师入口登录！")
            return

        admin_data = _load_json(ADMIN_FILE)
        if password != admin_data['password']:
            messagebox.showerror("错误", "密码错误")
            return

        self.app.show_admin_panel()


# ======================== Password Change Frame ========================

class PasswordChangeFrame(tk.Frame):
    """First-login password change screen."""

    def __init__(self, app, username, teachers_data):
        super().__init__(app)
        self.app = app
        self.username = username
        self.teachers_data = teachers_data

        tk.Label(self, text=f"欢迎，{username}！\n首次登录，请修改密码。",
                 font=('Microsoft YaHei', 13), justify=tk.CENTER).pack(pady=(25, 15))

        f1 = tk.Frame(self)
        f1.pack(pady=5)
        tk.Label(f1, text="新密码：", font=('Microsoft YaHei', 11), width=10).pack(side=tk.LEFT)
        self.entry_new = tk.Entry(f1, font=('Microsoft YaHei', 11), width=22, show='*')
        self.entry_new.pack(side=tk.LEFT)
        self.entry_new.focus_set()

        f2 = tk.Frame(self)
        f2.pack(pady=5)
        tk.Label(f2, text="确认密码：", font=('Microsoft YaHei', 11), width=10).pack(side=tk.LEFT)
        self.entry_confirm = tk.Entry(f2, font=('Microsoft YaHei', 11), width=22, show='*')
        self.entry_confirm.pack(side=tk.LEFT)

        tk.Button(self, text="确认修改", font=('Microsoft YaHei', 12),
                  width=14, command=self._confirm).pack(pady=20)

        self.entry_new.bind('<Return>', lambda e: self.entry_confirm.focus_set())
        self.entry_confirm.bind('<Return>', lambda e: self._confirm())

    def _confirm(self):
        new_pw = self.entry_new.get().strip()
        confirm_pw = self.entry_confirm.get().strip()

        if not new_pw:
            messagebox.showerror("错误", "密码不能为空！")
            return
        if new_pw != confirm_pw:
            messagebox.showerror("错误", "两次输入的密码不一致！")
            return
        if len(new_pw) < 3:
            messagebox.showerror("错误", "密码长度不能少于3位！")
            return

        self.teachers_data[self.username]['password'] = new_pw
        self.teachers_data[self.username]['first_login'] = False
        _save_json(TEACHERS_FILE, self.teachers_data)

        messagebox.showinfo("成功", "密码修改成功！请牢记新密码。\n此后不支持修改密码和找回密码。")
        self.app.show_grading(self.username)


# ======================== Grading Frame (Teacher) ========================

class GradingFrame(tk.Frame):
    """Main grading screen for teachers."""

    def __init__(self, app, username):
        super().__init__(app)
        self.app = app
        self.username = username

        self.student_grades = _load_json(STUDENT_GRADES_FILE)
        self.progress = _load_json(PROGRESS_FILE)
        self.student_list = list(self.student_grades[self.username].keys())
        self.total_count = len(self.student_list)

        self.current_index = self.progress.get(self.username, 0)
        if self.current_index < 0:
            self.current_index = 0
        if self.current_index >= self.total_count:
            self.current_index = self.total_count - 1

        self.var_content = tk.StringVar()
        self.var_language = tk.StringVar()
        self.var_adjustment = tk.StringVar()

        self._build_ui()
        self._jump_to_first_ungraded()

    def _build_ui(self):
        main = tk.Frame(self, padx=20, pady=15)
        main.pack(fill=tk.BOTH, expand=True)

        tk.Label(main, text=f"评阅教师：{self.username}",
                 font=('Microsoft YaHei', 13, 'bold')).pack(anchor=tk.W)

        # Progress
        pf = tk.Frame(main)
        pf.pack(fill=tk.X, pady=(12, 4))
        tk.Label(pf, text="评阅进度：", font=('Microsoft YaHei', 11)).pack(side=tk.LEFT)

        self.progress_bar = ttk.Progressbar(pf, length=360, mode='determinate',
                                            maximum=self.total_count)
        self.progress_bar.pack(side=tk.LEFT, padx=(5, 10))
        self.label_progress = tk.Label(pf, text="0 / 120", font=('Microsoft YaHei', 11, 'bold'),
                                       fg='#0078D4')
        self.label_progress.pack(side=tk.LEFT)

        ttk.Separator(main, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        # Student card
        card = tk.LabelFrame(main, text=" 当前评阅 ", font=('Microsoft YaHei', 12, 'bold'),
                             padx=15, pady=10)
        card.pack(fill=tk.X, pady=5)

        self.label_student = tk.Label(card, text="学生：---",
                                      font=('Microsoft YaHei', 13, 'bold'), fg='#333333')
        self.label_student.pack(anchor=tk.W, pady=(0, 10))

        grid = tk.Frame(card)
        grid.pack()

        tk.Label(grid, text="内容（0~10）：", font=('Microsoft YaHei', 12),
                 width=14, anchor=tk.E).grid(row=0, column=0, pady=6, sticky=tk.E)
        self.entry_content = tk.Entry(grid, textvariable=self.var_content,
                                      font=('Microsoft YaHei', 12), width=12, justify=tk.CENTER)
        self.entry_content.grid(row=0, column=1, pady=6, padx=(5, 0))
        tk.Label(grid, text="等级 A(9-10) B(7-8) C(5-6) D(3-4) E(0-2)",
                 font=('Microsoft YaHei', 8), fg='#888888').grid(row=0, column=2, padx=10)

        tk.Label(grid, text="语言（0~10）：", font=('Microsoft YaHei', 12),
                 width=14, anchor=tk.E).grid(row=1, column=0, pady=6, sticky=tk.E)
        self.entry_language = tk.Entry(grid, textvariable=self.var_language,
                                       font=('Microsoft YaHei', 12), width=12, justify=tk.CENTER)
        self.entry_language.grid(row=1, column=1, pady=6, padx=(5, 0))
        tk.Label(grid, text="等级 A(9-10) B(7-8) C(5-6) D(3-4) E(0-2)",
                 font=('Microsoft YaHei', 8), fg='#888888').grid(row=1, column=2, padx=10)

        tk.Label(grid, text="调整项（0~5）：", font=('Microsoft YaHei', 12),
                 width=14, anchor=tk.E).grid(row=2, column=0, pady=6, sticky=tk.E)
        self.entry_adjustment = tk.Entry(grid, textvariable=self.var_adjustment,
                                         font=('Microsoft YaHei', 12), width=12, justify=tk.CENTER)
        self.entry_adjustment.grid(row=2, column=1, pady=6, padx=(5, 0))
        tk.Label(grid, text="等级 A(5) B(4) C(3) D(2) E(1)",
                 font=('Microsoft YaHei', 8), fg='#888888').grid(row=2, column=2, padx=10)

        tk.Label(card, text="约束 (i)：内容+语言 ≥ 15 → 调整项 3~5；否则 0~3\n"
                            "约束 (ii)：内容和语言必须同档或相邻档，不可跨档",
                 font=('Microsoft YaHei', 9), fg='#C00000', justify=tk.LEFT).pack(anchor=tk.W, pady=(10, 0))

        # Rules reference
        rf = tk.LabelFrame(main, text=" 评分细则参考 ", font=('Microsoft YaHei', 11, 'bold'),
                           padx=10, pady=5)
        rf.pack(fill=tk.X, pady=8)
        rt = tk.Text(rf, font=('Consolas', 9), height=9, width=64)
        rt.pack()
        rt.insert(tk.END, SCORING_RULES_TEXT)
        rt.configure(state=tk.DISABLED)

        # Buttons
        bf = tk.Frame(main)
        bf.pack(fill=tk.X, pady=(12, 5))

        nav = tk.Frame(bf)
        nav.pack(side=tk.LEFT)

        self.btn_prev = tk.Button(nav, text="◀ 上一份", font=('Microsoft YaHei', 11),
                                  width=10, command=self._go_previous)
        self.btn_prev.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_submit = tk.Button(nav, text="✓ 提交评分", font=('Microsoft YaHei', 11, 'bold'),
                                    width=12, bg='#0078D4', fg='white', command=self._submit_score)
        self.btn_submit.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_next = tk.Button(nav, text="下一份 ▶", font=('Microsoft YaHei', 11),
                                  width=10, command=self._go_next)
        self.btn_next.pack(side=tk.LEFT)

        tk.Button(bf, text="保存并退出", font=('Microsoft YaHei', 11),
                  width=14, command=self._save_and_exit).pack(side=tk.RIGHT)

        # Keyboard bindings
        self.entry_content.bind('<Return>', lambda e: self.entry_language.focus_set())
        self.entry_language.bind('<Return>', lambda e: self.entry_adjustment.focus_set())
        self.entry_adjustment.bind('<Return>', lambda e: self._submit_score())

    # ---- Navigation ----

    def _jump_to_first_ungraded(self):
        grades = self.student_grades[self.username]
        for i, sid in enumerate(self.student_list):
            g = grades[sid]
            if g['content'] is None and g['language'] is None and g['adjustment'] is None:
                self.current_index = i
                self._load_paper()
                return
        self.current_index = self.total_count - 1
        self._load_paper()
        if self._all_my_graded():
            self._show_all_done()

    def _load_paper(self):
        if self.current_index < 0:
            self.current_index = 0
        if self.current_index >= self.total_count:
            self.current_index = self.total_count - 1

        sid = self.student_list[self.current_index]
        grades = self.student_grades[self.username][sid]

        self.label_student.config(text=f"学生：{sid}")
        self.var_content.set(str(grades['content']) if grades['content'] is not None else '')
        self.var_language.set(str(grades['language']) if grades['language'] is not None else '')
        self.var_adjustment.set(str(grades['adjustment']) if grades['adjustment'] is not None else '')

        self._update_progress()
        self._update_buttons()
        self.entry_content.focus_set()

    def _update_progress(self):
        graded = self._count_my_graded()
        self.progress_bar['value'] = graded
        self.label_progress.config(text=f"{graded} / {self.total_count}")

    def _update_buttons(self):
        self.btn_prev.config(state=tk.DISABLED if self.current_index <= 0 else tk.NORMAL)
        self.btn_next.config(state=tk.DISABLED if self.current_index >= self.total_count - 1 else tk.NORMAL)

    def _go_previous(self):
        self._save_progress()
        if self.current_index > 0:
            self.current_index -= 1
        self._load_paper()

    def _go_next(self):
        self._save_progress()
        if self.current_index < self.total_count - 1:
            self.current_index += 1
        self._load_paper()

    # ---- Score Submission ----

    def _submit_score(self):
        raw_c = self.var_content.get().strip()
        raw_l = self.var_language.get().strip()
        raw_a = self.var_adjustment.get().strip()

        try:
            c = int(raw_c)
            l = int(raw_l)
            a = int(raw_a)
        except ValueError:
            messagebox.showerror("错误", "非法输入：请输入整数！")
            return

        if raw_c != str(c) or raw_l != str(l) or raw_a != str(a):
            messagebox.showerror("错误", "非法输入：请输入有效的整数！")
            return

        valid, err_msg = validate_scores(c, l, a)
        if not valid:
            messagebox.showerror("错误", err_msg)
            return

        sid = self.student_list[self.current_index]
        self.student_grades[self.username][sid] = {'content': c, 'language': l, 'adjustment': a}
        _save_json(STUDENT_GRADES_FILE, self.student_grades)
        self._save_progress()
        self._update_progress()

        next_ug = self._find_next_ungraded()
        if next_ug is not None:
            self.current_index = next_ug
            self._load_paper()
        elif self._all_my_graded():
            self._show_all_done()
        else:
            self._load_paper()

    # ---- Helpers ----

    def _count_my_graded(self):
        return count_graded_for_teacher(self.username, self.student_grades)

    def _all_my_graded(self):
        return self._count_my_graded() == self.total_count

    def _find_next_ungraded(self):
        grades = self.student_grades[self.username]
        for i in range(self.current_index + 1, self.total_count):
            g = grades[self.student_list[i]]
            if g['content'] is None and g['language'] is None and g['adjustment'] is None:
                return i
        return None

    def _save_progress(self):
        self.progress[self.username] = self.current_index
        _save_json(PROGRESS_FILE, self.progress)

    def _show_all_done(self):
        self.label_student.config(text="✓ 所有试卷已评阅完毕！", fg='green')
        self.label_progress.config(text=f"{self.total_count} / {self.total_count} ✓", fg='green')
        self.progress_bar['value'] = self.total_count
        self.var_content.set('')
        self.var_language.set('')
        self.var_adjustment.set('')
        self.btn_submit.config(state=tk.DISABLED)
        self.btn_prev.config(state=tk.DISABLED)
        self.btn_next.config(state=tk.DISABLED)
        messagebox.showinfo("完成", "没有要评阅的试卷。\n所有试卷已评阅完毕！")

    def _save_and_exit(self):
        self._save_progress()
        self.app._on_exit()


# ======================== Admin Panel Frame ========================

class AdminPanelFrame(tk.Frame):
    """Admin panel screen."""

    def __init__(self, app):
        super().__init__(app)
        self.app = app

        self.teacher_bars = {}
        self.teacher_labels = {}

        self._build_ui()
        self._refresh_progress()

    def _build_ui(self):
        main = tk.Frame(self, padx=20, pady=15)
        main.pack(fill=tk.BOTH, expand=True)

        tk.Label(main, text="🔧 管理员面板", font=('Microsoft YaHei', 18, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        tk.Label(main, text=f"欢迎，{ADMIN_USERNAME}  |  仅管理员可导出成绩和清空数据",
                 font=('Microsoft YaHei', 10), fg='#666666').pack(anchor=tk.W, pady=(0, 15))

        # Progress section
        ps = tk.LabelFrame(main, text=" 评阅进度总览 ", font=('Microsoft YaHei', 12, 'bold'),
                           padx=15, pady=10)
        ps.pack(fill=tk.X, pady=5)

        for teacher in INITIAL_TEACHERS:
            tf = tk.Frame(ps)
            tf.pack(fill=tk.X, pady=4)
            tk.Label(tf, text=teacher, font=('Microsoft YaHei', 11, 'bold'),
                     width=10, anchor=tk.W).pack(side=tk.LEFT)
            bar = ttk.Progressbar(tf, length=280, mode='determinate',
                                  maximum=STUDENTS_PER_TEACHER)
            bar.pack(side=tk.LEFT, padx=5)
            label = tk.Label(tf, text="0 / 120", font=('Microsoft YaHei', 11), width=10)
            label.pack(side=tk.LEFT)
            self.teacher_bars[teacher] = bar
            self.teacher_labels[teacher] = label

        ttk.Separator(ps, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8)

        tf2 = tk.Frame(ps)
        tf2.pack(fill=tk.X)
        tk.Label(tf2, text="总计", font=('Microsoft YaHei', 12, 'bold'),
                 width=10, anchor=tk.W).pack(side=tk.LEFT)
        self.total_bar = ttk.Progressbar(tf2, length=280, mode='determinate',
                                         maximum=NUM_STUDENTS)
        self.total_bar.pack(side=tk.LEFT, padx=5)
        self.total_label = tk.Label(tf2, text="0 / 360", font=('Microsoft YaHei', 12, 'bold'),
                                    fg='#0078D4', width=10)
        self.total_label.pack(side=tk.LEFT)

        # Status
        self.status_label = tk.Label(main, text="", font=('Microsoft YaHei', 11),
                                     fg='#C00000', wraplength=520, justify=tk.CENTER)
        self.status_label.pack(pady=(12, 8))

        ttk.Separator(main, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)

        # Action buttons
        af = tk.Frame(main)
        af.pack(fill=tk.X, pady=(10, 5))

        self.btn_export = tk.Button(af, text="📤 导出成绩", font=('Microsoft YaHei', 12, 'bold'),
                                    width=18, height=2, bg='#107C10', fg='white',
                                    command=self._export)
        self.btn_export.pack(side=tk.LEFT, padx=(0, 15))

        self.btn_clear = tk.Button(af, text="🗑 清空数据并重置", font=('Microsoft YaHei', 12),
                                   width=18, height=2, bg='#C00000', fg='white',
                                   command=self._clear)
        self.btn_clear.pack(side=tk.LEFT)

        tk.Button(af, text="🔄 刷新进度", font=('Microsoft YaHei', 11),
                  width=12, command=self._refresh_progress).pack(side=tk.RIGHT)

        # Warning
        tk.Label(main, text="⚠ 数据安全提醒：\n"
                            "• 清空数据前请务必先导出成绩\n"
                            "• 清空操作会自动备份当前数据到 exports/ 目录\n"
                            "• 清空后所有评分记录将被删除，系统重置为初始状态\n"
                            "• 教师账号及密码将被保留",
                 font=('Microsoft YaHei', 9), fg='#888888', justify=tk.LEFT).pack(anchor=tk.W, pady=(10, 0))

        # Bottom buttons
        bf = tk.Frame(main)
        bf.pack(fill=tk.X, pady=(12, 0))
        tk.Button(bf, text="退出管理面板", font=('Microsoft YaHei', 11),
                  width=16, command=self.app.show_role_selection).pack(side=tk.RIGHT)

    def _refresh_progress(self):
        if not os.path.exists(STUDENT_GRADES_FILE):
            for t in INITIAL_TEACHERS:
                self.teacher_bars[t]['value'] = 0
                self.teacher_labels[t].config(text="0 / 120")
            self.total_bar['value'] = 0
            self.total_label.config(text="0 / 360")
            self.status_label.config(text="暂无评分数据。")
            self.btn_clear.config(state=tk.DISABLED)
            return

        sg = _load_json(STUDENT_GRADES_FILE)
        total = 0
        for teacher in INITIAL_TEACHERS:
            graded = count_graded_for_teacher(teacher, sg)
            total += graded
            self.teacher_bars[teacher]['value'] = graded
            self.teacher_labels[teacher].config(text=f"{graded} / {STUDENTS_PER_TEACHER}")

        self.total_bar['value'] = total
        self.total_label.config(text=f"{total} / {NUM_STUDENTS}")

        if total == NUM_STUDENTS:
            self.status_label.config(
                text="✓ 所有 360 份试卷已评阅完毕！可以导出成绩并清空数据。", fg='green')
            self.btn_clear.config(state=tk.NORMAL)
            self.btn_export.config(state=tk.NORMAL)
        elif total == 0:
            self.status_label.config(text="尚未有任何评分记录。请等待教师完成评阅。", fg='#888888')
            self.btn_clear.config(state=tk.DISABLED)
            self.btn_export.config(state=tk.NORMAL)
        else:
            remaining = NUM_STUDENTS - total
            self.status_label.config(
                text=f"评阅进行中… 还有 {remaining} 份试卷未完成评阅。\n全部完成后才能清空数据。",
                fg='#C00000')
            self.btn_clear.config(state=tk.DISABLED)
            self.btn_export.config(state=tk.NORMAL)

    def _export(self):
        if not os.path.exists(STUDENT_GRADES_FILE):
            messagebox.showerror("错误", "没有评分数据可供导出。")
            return

        sg = _load_json(STUDENT_GRADES_FILE)
        total = count_total_graded(sg)
        if total == 0:
            messagebox.showinfo("提示", "尚未有任何评分记录，无需导出。")
            return

        if not messagebox.askyesno("确认导出",
                                   f"当前共有 {total} / {NUM_STUDENTS} 份试卷已完成评阅。\n\n"
                                   f"将导出为 JSON 和 CSV 两种格式到 exports/ 目录。\n是否继续？"):
            return

        ep = export_all_scores()
        if ep:
            messagebox.showinfo("导出成功",
                                f"成绩已成功导出！\n\n导出目录：exports/\n"
                                f"文件格式：JSON + CSV\n\n导出 {total} 条评分记录。")
        else:
            messagebox.showerror("错误", "导出失败，请检查文件权限。")
        self._refresh_progress()

    def _clear(self):
        if not os.path.exists(STUDENT_GRADES_FILE):
            messagebox.showerror("错误", "没有评分数据可供清空。")
            return

        sg = _load_json(STUDENT_GRADES_FILE)
        total = count_total_graded(sg)

        if total < NUM_STUDENTS:
            messagebox.showwarning("无法清空",
                                   f"目前仅有 {total} / {NUM_STUDENTS} 份试卷完成评阅。\n"
                                   f"所有 360 份试卷评阅完毕后才能清空数据。\n\n"
                                   f"请等待所有教师完成评阅后再操作。")
            return

        # Step 1: offer export
        if messagebox.askyesno("步骤 1/3 — 导出成绩",
                               "清空数据前，强烈建议先导出成绩。\n\n"
                               "是否现在导出所有成绩？\n（选择「否」将跳过导出，直接进行下一步）"):
            if not export_all_scores():
                messagebox.showerror("错误", "导出失败，操作已取消。")
                return

        # Step 2: confirm
        if not messagebox.askyesno("步骤 2/3 — 确认清空",
                                   "⚠ 即将清空所有评分数据！\n\n"
                                   "此操作将执行以下步骤：\n"
                                   "  1. 自动备份当前数据到 exports/ 目录\n"
                                   "  2. 删除所有学生评分记录\n"
                                   "  3. 重新随机分配 360 份试卷\n"
                                   "  4. 重置所有教师评阅进度\n\n"
                                   "教师账号及密码将被保留。\n\n确定要继续吗？",
                                   icon='warning'):
            return

        # Step 3: final confirm
        if not messagebox.askyesno("步骤 3/3 — 最终确认",
                                   "⚠⚠ 这是最后确认！⚠⚠\n\n"
                                   "清空后数据将无法恢复（除非从备份中手动恢复）。\n\n"
                                   "确定要清空所有评分数据并重置系统吗？",
                                   icon='warning'):
            return

        if clear_grading_data():
            messagebox.showinfo("操作完成",
                                "数据已成功清空！\n\n"
                                "• 备份文件已保存到 exports/ 目录\n"
                                "• 评分数据已全部清除\n"
                                "• 试卷已重新随机分配\n"
                                "• 系统已重置为初始状态\n"
                                "• 教师账号及密码保持不变\n\n"
                                "教师可重新登录开始新一轮评阅。")
            self._refresh_progress()
        else:
            messagebox.showerror("错误", "清空数据失败！请检查文件权限。\n"
                                       "备份文件可能已保存在 exports/ 目录。")


# ======================== Entry Point ========================

def main():
    """Application entry point."""
    init_data_files()
    App().mainloop()


if __name__ == '__main__':
    main()
