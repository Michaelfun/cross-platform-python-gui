import os, sys
import math
import sqlite3
from datetime import date, datetime, timedelta

from fpdf import FPDF
from kivy.resources import resource_add_path, resource_find
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.utils import get_color_from_hex
from kivymd.app import MDApp
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import ThreeLineListItem
from kivymd.uix.picker import MDDatePicker

_today = date.today()
totay_date = _today.strftime("%Y-%m-%d")
_previous_date = _today-timedelta(days=1)
previous_date = _previous_date.strftime("%Y-%m-%d")

_now = datetime.now()
current_time = _now.strftime("%H:%M")
db_name = []
screens = ScreenManager()
groups = set()

conn = sqlite3.connect(f'mydb.sqlite')
cur = conn.cursor()

cur.executescript('''
CREATE TABLE IF NOT EXISTS Question(
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    question TEXT UNIQUE,
    'group' TEXT,
    'created_date' TEXT, 
    'due_date' TEXT 
);

CREATE TABLE IF NOT EXISTS Probability(
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    question_id INTEGER,
    probability INTEGER,
    'entry_date' TEXT
);

CREATE TABLE IF NOT EXISTS Final(
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    question_ids INTEGER,
    'questions' TEXT,
    brier_score INTEGER,
    'answer' TEXT,
    'group' TEXT,
    'created_date' TEXT,
    'due_date' TEXT
);

CREATE TABLE IF NOT EXISTS User(
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    name TEXT UNIQUE,
    'reg_date' TEXT
);

''')


class Content(BoxLayout):
    pass


class Content1(Screen):
    pass


class questionCard(MDCard):
    text = StringProperty()
    text1 = StringProperty()


class questionCard2(MDCard):
    text = StringProperty()
    text1 = StringProperty()


class Login_page(Screen):
    pass


class Home_Screen(Screen):
    pass


class New_Questions_Screen(Screen):
    pass


class Completed_Question_Screen(Screen):
    pass


class Pending_question(Screen):
    pass


screens.add_widget(Login_page(name='login'))
screens.add_widget(Pending_question(name='pending'))
screens.add_widget(Home_Screen(name='Home'))
screens.add_widget(New_Questions_Screen(name='New-Questions'))
screens.add_widget(Completed_Question_Screen(name='Compleated-Questions'))


class QuestionApp(MDApp):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.dialog = None
        self.dialog2 = None
        self.dialog1 = None
        self.data_out = None

        self.menu = MDDropdownMenu()

    def menu_group(self):
        menu_items = [
            {
                "text": f"Item {i}",
                "viewclass": "OneLineListItem",
                "on_release": lambda x=f"{i}": self.on_selections(x),
            } for i in groups
        ]
        self.menu.caller = self.root.ids.home.ids.menu_group
        self.menu.items = menu_items
        self.menu.width_mult = 4
        self.menu.open()

    def log_out(self):
        self.root.current = "login"
        self.root.ids.Login.ids.memo2.text = " "

    def login(self, user_name):
        user = user_name
        cur.execute('SELECT name FROM User')
        data = cur.fetchall()
        if data:
            for i in data:
                if user == i[0]:
                    db_name.append(user)
                    self.root.current = "Home"
                    self.root.ids.home.ids.User.text = "Name:" + " " + user
                else:
                    self.root.ids.Login.ids.memo2.text = "Your not registed"
        if not data:
            self.root.ids.Login.ids.memo2.text = "Your not registed"

        if user == '':
            self.root.ids.Login.ids.memo2.text = "username required"

    def user_registration(self):
        if not self.dialog:
            self.dialog = MDDialog(
                title="User registration:",
                type="custom",
                auto_dismiss=False,
                content_cls=Content(),
            )
        self.dialog.open()
        self.dialog.content_cls.ids.memo.text = ''

    def report_generating(self):
        if not self.dialog1:
            self.dialog1 = MDDialog(
                title="Generate Report:",
                type="custom",
                auto_dismiss=False,
                content_cls=Content1(),
            )
        self.dialog1.open()

    def get_user_info(self):
        texts = self.dialog.content_cls.ids.names.text
        if texts:
            cur.execute('SELECT name FROM User')
            data = cur.fetchall()
            if not data:
                cur.execute(''' INSERT OR IGNORE INTO User(name, 'reg_date') VALUES(?,?)''',
                            (texts, totay_date))
                conn.commit()
                self.dialog.content_cls.ids.memo.text = 'registration successfully'
            if data:
                for i in data:
                    if texts == i[0]:
                        self.dialog.content_cls.ids.memo.text = 'name exsist, try another name'
                    else:
                        cur.execute(''' INSERT OR IGNORE INTO User(name, 'reg_date') VALUES(?,?)''',
                                    (texts, totay_date))
                        conn.commit()
                        self.dialog.content_cls.ids.memo.text = 'registration successfully'
            self.root.ids.Login.ids.memo2.text = " "
        else:
            self.dialog.content_cls.ids.memo.text = 'name required'

        self.dialog.content_cls.ids.names.text = ''

    def close_dialog(self):
        self.dialog.dismiss()
        self.root.ids.Login.ids.memo2.text = ""

    def close_dialog1(self):
        self.dialog1.dismiss()

    def data_roller_over(self):
        cur.execute('SELECT id FROM Question')
        qn_ids = cur.fetchall()
        for num in qn_ids:
            cur.execute('SELECT question_id, entry_date FROM Probability WHERE question_id =? AND "entry_date" = ?',
                        (num[0], totay_date))
            data_num = cur.fetchall()
            if not data_num:
                cur.execute('SELECT probability FROM Probability WHERE question_id =? AND "entry_date" = ?',
                            (num[0], previous_date))
                datas = cur.fetchall()
                if datas:
                    cur.execute('SELECT "due_date" FROM Question WHERE id =?', (num[0],))
                    date_due = cur.fetchone()[0]
                    if date_due != previous_date:
                        inseted = datas[0][0]
                        ids = num[0]
                        cur.execute(
                            'INSERT OR IGNORE INTO Probability(question_id, probability, "entry_date") VALUES(?,?,?)',
                            (ids, inseted, totay_date))
                        conn.commit()

    def pending_question(self):
        self.root.ids.pending.ids.question_box.clear_widgets()
        cur.execute('SELECT id, question, "group" FROM Question WHERE "due_date" <=?', (totay_date,))
        data_question = cur.fetchall()

        for i_quest in data_question:
            cur.execute('SELECT entry_date FROM Probability WHERE question_id =? AND "entry_date" = ?',
                        (i_quest[0], totay_date))
            datas = cur.fetchall()
            if datas:
                self.root.ids.pending.ids.question_box.add_widget(
                    questionCard2(text=f"{i_quest[2]}", text1=f"{i_quest[1]}")
                )
        self.root.current = "pending"

    def on_start(self):
        self.root.ids.home.ids.today_date.text = "Date:" + " " + totay_date
        self.root.ids.home.ids.question_box.clear_widgets()
        cur.execute('SELECT question,"group" FROM Question WHERE "due_date" >= ?', (totay_date,))
        data_all = cur.fetchall()
        for i_all in data_all:
            self.root.ids.home.ids.question_box.add_widget(
                questionCard(text=f"{i_all[1]}", text1=f"{i_all[0]}")
            )

    def save_properbility_entry(self, question_proper, proper_entry):
        cur.execute('SELECT id FROM Question WHERE question = ?', (question_proper,))
        qn_id = cur.fetchone()[0]
        cur.execute('SELECT question_id, entry_date FROM Probability WHERE question_id =? AND "entry_date" = ?',
                    (qn_id, totay_date))
        data_prop = cur.fetchall()
        if not data_prop:
            cur.execute(''' INSERT OR IGNORE INTO Probability(question_id, probability, 'entry_date') VALUES(?,?,?)''',
                        (qn_id, proper_entry, totay_date))
        else:
            cur.execute('UPDATE Probability SET probability=? WHERE question_id =? AND "entry_date" = ?',
                        (proper_entry, qn_id, totay_date))
        conn.commit()

    def add_new_question(self, Question, Question_group, Due_date):
        cur.execute(''' INSERT OR IGNORE INTO Question(question, 'group', 'created_date', 'due_date') VALUES(?,?,?,?)''',
                    (Question, Question_group, totay_date, Due_date))
        cur.execute('SELECT id,"group","created_date","due_date" FROM Question WHERE question = ?',
                    (Question,))
        data_q = cur.fetchall()
        data_q = list(data_q[0])
        question_id = data_q[0]
        catergory = data_q[1]
        creatain_date = data_q[2]
        ending_date = data_q[3]

        cur.execute(''' INSERT OR IGNORE INTO Final(question_ids,questions, 'group', 'created_date', 'due_date') VALUES(?,?,?,?,?)''',
                    (question_id, Question, catergory, creatain_date, ending_date))

        conn.commit()

    def on_save(self, instance, value, date_range):
        self.root.ids.new_question.ids.Due_date.text = str(value)

    def on_save1(self, instance, value, date_range):
        self.dialog1.content_cls.ids.date_from.text = str(value)

    def on_save2(self, instance, value, date_range):
        self.dialog1.content_cls.ids.date_till.text = str(value)

    def on_cancel(self, instance, value):
        """Events called when the "CANCEL" dialog box button is clicked."""

    def show_date_picker(self):
        date_dialog = MDDatePicker(
            primary_color=get_color_from_hex("#303438"),
            selector_color=get_color_from_hex("#303438"),
            text_button_color=get_color_from_hex("#303438"),
            text_current_color=get_color_from_hex("#303438"),
        )
        date_dialog.bind(on_save=self.on_save, on_cancel=self.on_cancel)
        date_dialog.open()

    def show_date_picker1(self):
        date_dialog = MDDatePicker(
            primary_color=get_color_from_hex("#303438"),
            selector_color=get_color_from_hex("#303438"),
            text_button_color=get_color_from_hex("#303438"),
            text_current_color=get_color_from_hex("#303438"),
        )
        date_dialog.bind(on_save=self.on_save1, on_cancel=self.on_cancel)
        date_dialog.open()

    def show_date_picker2(self):
        date_dialog = MDDatePicker(
            primary_color=get_color_from_hex("#303438"),
            selector_color=get_color_from_hex("#303438"),
            text_button_color=get_color_from_hex("#303438"),
            text_current_color=get_color_from_hex("#303438"),
        )
        date_dialog.bind(on_save=self.on_save2, on_cancel=self.on_cancel)
        date_dialog.open()

    def calculate_brier_score(self, question_proper1, val):
        sumation = []
        sumation2 = []
        cur.execute('SELECT id FROM Question WHERE question =?', (question_proper1,))
        data_id = cur.fetchone()[0]
        cur.execute('SELECT probability FROM Probability WHERE question_id =?', (data_id,))
        datas_p = cur.fetchall()
        for i_id in datas_p:
            sumation.append(i_id[0])
        len_n = len(sumation)
        for j in datas_p:
            p = j[0]
            p2 = round((1-p), 2)
            if val == 'True':
                t1 = math.pow((p-1), 2)
                t2 = math.pow((p2-0), 2)
                sumation2.append(t1)
                sumation2.append(t2)
            else:
                t1 = math.pow((p-0), 2)
                t2 = math.pow((p2-1), 2)
                sumation2.append(t1)
                sumation2.append(t2)
        brier_scores = sum(sumation2) / len_n
        brier_scores = round(brier_scores, 2)
        cur.execute('UPDATE Final SET brier_score=?, answer=? WHERE question_ids =?',
                    (brier_scores, val, data_id))
        cur.execute('DELETE FROM Question WHERE id=?', (data_id,))

        conn.commit()

    def completed_question(self):
        self.root.ids.completed_question.ids.completed.clear_widgets()
        score_total = []
        cur.execute('SELECT question_ids, questions, brier_score, answer, "group" FROM Final WHERE brier_score != " "')
        data_final = cur.fetchall()
        for new in data_final:
            self.root.ids.completed_question.ids.completed.add_widget(
                ThreeLineListItem(text=f'{new[0]} {new[1]}',
                                  secondary_text="Brier Score is" + " " + str(new[2]),
                                  tertiary_text="Value is" + " " + new[3])
            )
            score_total.append(new[2])
        total = round(sum(score_total), 2)
        self.root.ids.completed_question.ids.agrgate.text = f'TOTAL BRIER SCORE:   {total:>5}'
        for group in data_final:
            groups.add(group[4])

    def report(self, group_name, date_from, date_till):
        summation = []
        cur.execute('SELECT brier_score FROM Final WHERE brier_score != " " AND "group"=? AND due_date >= ? AND due_date <= ?',
                    (group_name, date_from, date_till))
        data_final = cur.fetchall()
        cur.execute('SELECT questions, brier_score FROM Final WHERE brier_score != " " AND "group"=? AND due_date >= ? AND due_date <= ?',
                    (group_name, date_from, date_till))
        data_final1 = cur.fetchall()
        if data_final:
            for i in data_final:
                summation.append(i[0])
        try:
            average_score = sum(summation)/len(summation)
            average_score2 = round(average_score, 2)
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=15)
            pdf.cell(200, 10, txt=f'Date Range:   {date_from}  -  {date_till}', ln=1, align='C')
            pdf.cell(200, 10, txt=f'Group:  {group_name}', ln=1, align='L')
            pdf.cell(200, 10, txt=f'Average Score:  {average_score2}', ln=1, align='L')
            pdf.cell(200, 10, txt='Individual Scores:', ln=1, align='L')
            if data_final1:
                for j in data_final1:
                    pdf.cell(200, 10, txt=f'   {j[0]:>10}:   {j[1]:>8}', ln=1, align='L')

            pdf.output("Report.pdf")
        except ZeroDivisionError:
            pass

    def on_selections(self, group):
        self.root.ids.completed_question.ids.completed.clear_widgets()
        score_total = []
        cur.execute('SELECT question_ids, questions, brier_score, answer, "group" FROM Final WHERE brier_score != " " AND "group"=?', (group,))
        data_final = cur.fetchall()
        for new in data_final:
            self.root.ids.completed_question.ids.completed.add_widget(
                ThreeLineListItem(text=f'{new[0]} {new[1]}',
                                  secondary_text="Brier Score is" + " " + str(new[2]),
                                  tertiary_text="Value is" + " " + new[3])
            )
            score_total.append(new[2])
        total = round(sum(score_total), 2)
        self.root.ids.completed_question.ids.agrgate.text = f'TOTAL BRIER SCORE:   {total:>5}'
        self.root.ids.completed_question.ids.completed_group.text = 'Completed Questions From' + ' ' + str(group) + ' ' + 'Group'
        self.root.current = 'Compleated-Questions'
        self.menu.dismiss()


if __name__ == "__main__":
    try:
        if hasattr(sys, '_MEIPASS'):
            resource_add_path(os.path.join(sys._MEIPASS))
        QuestionApp().run()
    except Exception as e:
        print(e)
        input("Press enter")
