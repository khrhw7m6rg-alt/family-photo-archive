import os
import shutil
import sqlite3
from datetime import datetime

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.properties import StringProperty
from kivy.core.window import Window

try:
    from plyer import filechooser
except Exception:
    filechooser = None


# =========================================================
# إعدادات التطبيق
# =========================================================

APP_NAME = "أرشيف الصور العائلية"

KV = r'''
#:import dp kivy.metrics.dp

<MainScreen>:
    BoxLayout:
        orientation: "vertical"

        canvas.before:
            Color:
                rgba: 0.96, 0.96, 0.96, 1
            Rectangle:
                pos: self.pos
                size: self.size

        BoxLayout:
            size_hint_y: None
            height: dp(70)
            padding: dp(10)
            spacing: dp(8)

            Label:
                text: "📷 أرشيف الصور العائلية"
                font_size: "22sp"
                bold: True
                color: 0.05, 0.15, 0.25, 1

        Label:
            text: "د. تامر داود"
            size_hint_y: None
            height: dp(30)
            font_size: "14sp"
            color: 0.25, 0.25, 0.25, 1

        ScrollView:
            do_scroll_x: False

            BoxLayout:
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                padding: dp(12)
                spacing: dp(10)

                TextInput:
                    id: persons
                    hint_text: "بتاع مين؟ الأشخاص في الصورة"
                    multiline: False
                    size_hint_y: None
                    height: dp(48)

                TextInput:
                    id: photo_date
                    hint_text: "التاريخ - مثال: 1995/06/20"
                    multiline: False
                    size_hint_y: None
                    height: dp(48)

                TextInput:
                    id: location
                    hint_text: "المكان - اختياري"
                    multiline: False
                    size_hint_y: None
                    height: dp(48)

                TextInput:
                    id: occasion
                    hint_text: "المناسبة - اختياري"
                    multiline: False
                    size_hint_y: None
                    height: dp(48)

                TextInput:
                    id: notes
                    hint_text: "ملاحظات"
                    multiline: True
                    size_hint_y: None
                    height: dp(100)

                Button:
                    text: "📁 اختيار صورة"
                    size_hint_y: None
                    height: dp(52)
                    on_release: root.choose_image()

                Label:
                    id: selected_file
                    text: root.selected_file
                    text_size: self.width, None
                    size_hint_y: None
                    height: dp(50)
                    color: 0.2, 0.2, 0.2, 1

                Button:
                    text: "💾 حفظ الصورة في الأرشيف"
                    size_hint_y: None
                    height: dp(55)
                    on_release: root.save_photo()

                Label:
                    text: "البحث في الأرشيف"
                    size_hint_y: None
                    height: dp(35)
                    font_size: "18sp"
                    bold: True

                TextInput:
                    id: search
                    hint_text: "ابحث باسم الشخص أو التاريخ أو المكان أو المناسبة أو الملاحظات"
                    multiline: False
                    size_hint_y: None
                    height: dp(48)

                Button:
                    text: "🔎 بحث"
                    size_hint_y: None
                    height: dp(50)
                    on_release: root.search_photos()

                Button:
                    text: "📚 عرض كل الصور"
                    size_hint_y: None
                    height: dp(50)
                    on_release: root.show_all()

                Label:
                    id: results
                    text: root.results_text
                    text_size: self.width, None
                    size_hint_y: None
                    height: dp(400)
                    valign: "top"
                    halign: "right"
                    color: 0.1, 0.1, 0.1, 1
'''


class MainScreen(Screen):

    selected_file = StringProperty("")
    results_text = StringProperty(
        "لا توجد نتائج بعد.\n\nأضف صورة إلى الأرشيف ثم استخدم البحث."
    )

    def on_enter(self):
        self.create_database()

    def get_base_dir(self):
        return App.get_running_app().user_data_dir

    def get_images_dir(self):
        path = os.path.join(self.get_base_dir(), "images")
        os.makedirs(path, exist_ok=True)
        return path

    def get_db_path(self):
        return os.path.join(self.get_base_dir(), "archive.db")

    def create_database(self):
        os.makedirs(self.get_base_dir(), exist_ok=True)
        os.makedirs(self.get_images_dir(), exist_ok=True)

        conn = sqlite3.connect(self.get_db_path())
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS photos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_path TEXT NOT NULL,
                persons TEXT,
                photo_date TEXT,
                location TEXT,
                occasion TEXT,
                notes TEXT,
                created_at TEXT
            )
        """)

        conn.commit()
        conn.close()

    def choose_image(self):
        if filechooser is None:
            self.show_message(
                "خطأ",
                "لم يتم تحميل أداة اختيار الصور."
            )
            return

        try:
            filechooser.open_file(
                on_selection=self.file_selected,
                filters=["*.jpg", "*.jpeg", "*.png", "*.webp"]
            )
        except Exception as e:
            self.show_message("خطأ", str(e))

    def file_selected(self, selection):
        try:
            if not selection:
                return

            path = selection[0]

            if path:
                self.selected_file = path

        except Exception as e:
            self.show_message("خطأ", str(e))

    def save_photo(self):

        if not self.selected_file:
            self.show_message(
                "تنبيه",
                "اختر صورة أولًا."
            )
            return

        persons = self.ids.persons.text.strip()
        photo_date = self.ids.photo_date.text.strip()
        location = self.ids.location.text.strip()
        occasion = self.ids.occasion.text.strip()
        notes = self.ids.notes.text.strip()

        if not persons:
            self.show_message(
                "تنبيه",
                "اكتب اسم الشخص أو الأشخاص في الصورة."
            )
            return

        try:
            original = self.selected_file

            if not os.path.exists(original):
                self.show_message(
                    "خطأ",
                    "تعذر الوصول إلى الصورة المحددة."
                )
                return

            extension = os.path.splitext(original)[1].lower()

            if extension not in [".jpg", ".jpeg", ".png", ".webp"]:
                self.show_message(
                    "تنبيه",
                    "صيغة الصورة غير مدعومة."
                )
                return

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

            new_name = "photo_" + timestamp + extension

            destination = os.path.join(
                self.get_images_dir(),
                new_name
            )

            shutil.copy2(original, destination)

            conn = sqlite3.connect(self.get_db_path())
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO photos
                (
                    image_path,
                    persons,
                    photo_date,
                    location,
                    occasion,
                    notes,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                destination,
                persons,
                photo_date,
                location,
                occasion,
                notes,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))

            conn.commit()
            conn.close()

            self.clear_form()

            self.show_message(
                "تم الحفظ",
                "تم حفظ الصورة وبياناتها في أرشيف الصور العائلية."
            )

        except Exception as e:
            self.show_message(
                "خطأ أثناء الحفظ",
                str(e)
            )

    def search_photos(self):

        keyword = self.ids.search.text.strip()

        if not keyword:
            self.show_all()
            return

        try:
            conn = sqlite3.connect(self.get_db_path())
            cur = conn.cursor()

            pattern = "%" + keyword + "%"

            cur.execute("""
                SELECT
                    id,
                    persons,
                    photo_date,
                    location,
                    occasion,
                    notes
                FROM photos
                WHERE
                    persons LIKE ?
                    OR photo_date LIKE ?
                    OR location LIKE ?
                    OR occasion LIKE ?
                    OR notes LIKE ?
                ORDER BY id DESC
            """, (
                pattern,
                pattern,
                pattern,
                pattern,
                pattern
            ))

            rows = cur.fetchall()
            conn.close()

            self.display_results(rows)

        except Exception as e:
            self.show_message("خطأ", str(e))

    def show_all(self):

        try:
            conn = sqlite3.connect(self.get_db_path())
            cur = conn.cursor()

            cur.execute("""
                SELECT
                    id,
                    persons,
                    photo_date,
                    location,
                    occasion,
                    notes
                FROM photos
                ORDER BY id DESC
            """)

            rows = cur.fetchall()
            conn.close()

            self.display_results(rows)

        except Exception as e:
            self.show_message("خطأ", str(e))

    def display_results(self, rows):

        if not rows:
            self.results_text = "لم يتم العثور على صور."
            return

        text = ""

        for row in rows:

            photo_id = row[0]
            persons = row[1] or "-"
            photo_date = row[2] or "-"
            location = row[3] or "-"
            occasion = row[4] or "-"
            notes = row[5] or "-"

            text += (
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"رقم الصورة: {photo_id}\n"
                f"الأشخاص: {persons}\n"
                f"التاريخ: {photo_date}\n"
                f"المكان: {location}\n"
                f"المناسبة: {occasion}\n"
                f"ملاحظات: {notes}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
            )

        self.results_text = text

    def clear_form(self):

        self.ids.persons.text = ""
        self.ids.photo_date.text = ""
        self.ids.location.text = ""
        self.ids.occasion.text = ""
        self.ids.notes.text = ""

        self.selected_file = ""

    def show_message(self, title, message):

        content = Button(
            text="حسنًا",
            size_hint_y=None,
            height=50
        )

        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.85, 0.35),
            auto_dismiss=False
        )

        content.bind(
            on_release=popup.dismiss
        )

        popup.open()


class FamilyArchiveApp(App):

    title = APP_NAME

    def build(self):

        Window.softinput_mode = "below_target"

        Builder.load_string(KV)

        sm = ScreenManager()

        sm.add_widget(
            MainScreen(name="main")
        )

        return sm


if __name__ == "__main__":
    FamilyArchiveApp().run()
