from kivy.app import App
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.menu import MDDropdownMenu
from kivy.core.window import Window
from kivy.properties import StringProperty
from kivy.metrics import dp
from model import *
from PIL import Image, ImageDraw, ImageFont
from kivy.graphics.texture import Texture

from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.utils import platform


class HomeScreen(Screen):
    def home(self):
        self.ids.chat_container.clear_widgets()  # Clear previous messages

    def send_message(self):
        user_input = self.ids.message_input.text.strip()
        print(user_input)

        if user_input:
            self.add_message(user_input, [0.2, 0.2, 0.6, 1], align="right")  # Blue background
            self.ids.message_input.text = ""
            response = chat_with_bot(user_input=user_input)
            self.add_message(response, [0.2, 0.2, 0.2, 1], align="full")  # Gray background

    def add_message(self, text, bg_color, align="left"):
        text = text.encode("utf-8").decode("utf-8")
        max_width = self.width * 0.98

        message_label = MDLabel(
            text=text,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            font_size="18sp",
            size_hint_x=1,
            markup=True,
            padding=[dp(1), dp(1)],
            text_size=(max_width, None),
        )

        message_label.texture_update()
        message_label.height = message_label.texture_size[1] + dp(2)
        message_label.md_bg_color = bg_color

        message_box = BoxLayout(
            size_hint_y=None,
            height=message_label.height,
            padding=[dp(1), dp(1)],
            spacing=dp(2),
            size_hint_x=1,
        )

        message_box.add_widget(message_label)
        self.ids.chat_container.add_widget(message_box)

    def logout(self):
        app = MDApp.get_running_app()
        app.session_manager.clear_session()
        self.manager.current = "login_screen"

    def open_file_chooser(self):
        file_chooser = FileChooserListView()
        file_chooser.filters = ["*.txt", "*.pdf", "*.docx"]  # Add supported file types
        file_chooser.bind(on_submit=self.handle_file_selection)
        popup = Popup(title="Upload a Document", content=file_chooser, size_hint=(0.9, 0.9))
        popup.open()

    def handle_file_selection(self, instance, selection, *args):
        if selection:
            selected_file = selection[0]
            print(f"Selected file: {selected_file}")
            self.add_message(f"Uploaded file: {selected_file}", [0.2, 0.6, 0.2, 1], align="right")
            try:
                with open(selected_file, "r", encoding="utf-8") as file:
                    content = file.read()
                    self.add_message(f"File content:\n{content}", [0.2, 0.2, 0.2, 1], align="full")
            except UnicodeDecodeError:
                self.add_message("File is not readable (binary or unsupported format).", [0.6, 0.2, 0.2, 1], align="full")
            except Exception as e:
                self.add_message(f"Error reading file: {e}", [0.6, 0.2, 0.2, 1], align="full")
    
    def toggle_nav_drawer(self):
        nav_drawer = self.ids.nav_drawer
        if nav_drawer.state == "open":
            self.ids.nav_drawer.set_state("close")
        else:
            nav_drawer.set_state("open")

    def menu_callback(self, text):
        print(f"Selected: {text}")
        self.toggle_nav_drawer()
        
    def open_menu(self):
        if hasattr(self, "menu") and self.menu:  # Close any existing menu first
            self.menu.dismiss()

        menu_items = [
            {
                "text": "Biometric",
                "viewclass": "OneLineListItem",
                "on_release": lambda x="Biometric": self.menu_callback(x),
            },
            {
                "text": "History",
                "viewclass": "OneLineListItem",
                "on_release": lambda x="History": self.menu_callback(x),
            },
            {
                "text": "Help",
                "viewclass": "OneLineListItem",
                "on_release": lambda x="Help": self.menu_callback(x),
            },
        ]

        self.menu = MDDropdownMenu(
            caller=self.ids.top_app_bar,
            items=menu_items,
            width_mult=4,
        )
        self.menu.open()

    def menu_callback(self, option):
        print(f"Selected: {option}")  # Debugging print
        if hasattr(self, "menu") and self.menu:
            self.menu.dismiss()
        
        self.ids.nav_drawer.set_state("close")  # Ensure the nav drawer also closes

