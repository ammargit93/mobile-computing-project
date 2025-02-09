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
        text = text.encode("utf-8").decode("utf-8")  # Fix encoding issues

        # Determine full width for messages
        max_width = self.width * 0.98  # 98% of screen width

        message_label = MDLabel(
            text=text,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],  # White text
            font_size="18sp",
            size_hint_x=1,  # Use full width
            markup=True,
            padding=[dp(1), dp(1)],  # Only 1mm padding
            text_size=(max_width, None),
        )

        message_label.texture_update()
        message_label.height = message_label.texture_size[1] + dp(2)  # Remove extra height
        message_label.md_bg_color = bg_color

        message_box = BoxLayout(
            size_hint_y=None,
            height=message_label.height,  # Auto height
            padding=[dp(1), dp(1)],  # 1mm padding
            spacing=dp(2),  # Small spacing
            size_hint_x=1,  # Full width
        )

        message_box.add_widget(message_label)

        self.ids.chat_container.add_widget(message_box)



    def logout(self):
        app = MDApp.get_running_app()
        app.session_manager.clear_session()
        self.manager.current = "login_screen"
