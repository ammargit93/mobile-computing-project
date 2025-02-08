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


class HomeScreen(Screen):
    def home(self):
        self.ids.chat_container.clear_widgets()  # Clear previous messages
    def send_message(self):
        user_input = self.ids.message_input.text.strip()
        print(user_input)
        if user_input:
            self.add_message(user_input, [0.2, 0.2, 0.6, 1])  # Blue user message
            self.ids.message_input.text = ""
    
    
    def add_message(self, text, bg_color, align_right=True):
        message_box = BoxLayout(
            size_hint_y=None,
            height=dp(40),
            padding=[dp(10), dp(5)],
            spacing=dp(5),
            size_hint_x=1  # Full width
        )

        message_label = MDLabel(
            text=text,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],  # White text
            size_hint_x=None,
            width=self.width * 0.6,  # Limit width
            font_size="16sp",
            halign="right" if align_right else "left"
        )

        message_label.md_bg_color = bg_color  # Set background color

        # Fix: Use BoxLayout to push message to the correct side
        if align_right:
            message_box.add_widget(BoxLayout(size_hint_x=0.4))  # Empty space on left
            message_box.add_widget(message_label)
        else:
            message_box.add_widget(message_label)
            message_box.add_widget(BoxLayout(size_hint_x=0.4))  # Empty space on right

        self.ids.chat_container.add_widget(message_box)


    def logout(self):
        """Handles logout and clears session data."""
        app = MDApp.get_running_app()
        app.session_manager.clear_session()
        self.manager.current = "login_screen"
