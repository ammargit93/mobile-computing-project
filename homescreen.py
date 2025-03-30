from kivy.clock import Clock  # Missing import
from kivy.uix.screenmanager import Screen
from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.label import MDLabel
from kivy.properties import ListProperty
from kivymd.uix.list import OneLineListItem
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.textfield import MDTextField
from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivy.metrics import dp
from config import notes_collection
from filescreen import *

class NotePopupContent(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = dp(10)
        self.padding = dp(10)
        self.size_hint_y = None
        self.height = dp(200)  
        
        self.title_field = MDTextField(
            hint_text="Title",
            mode="rectangle",
            multiline=False,
            size_hint_y=None,
            height=dp(48)
        )
        self.add_widget(self.title_field)

        self.description_field = MDTextField(
            hint_text="Description",
            mode="rectangle",
            multiline=True,
            size_hint_y=None,
            height=dp(100))
        self.add_widget(self.description_field)
        self.description_field.bind(height=self.adjust_height)

    def adjust_height(self, instance, value):
        self.height = self.title_field.height + self.description_field.height + dp(20)
        
        
class GuestHomeScreen(Screen):
    notes = ListProperty([])
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.notes = []

    def on_enter(self):
        Clock.schedule_once(self._load_notes)
    
    def nav_to_chatbot(self):
        """Navigate to chatbot screen"""
        self.manager.current = "chatbot_screen"
    
    def nav_to_files(self):
        """Navigate to files screen"""
        self.manager.current = "files_screen"
    
    def nav_to_ocr(self):
        """Navigate to OCR screen"""
        self.manager.current = "ocr_screen"

    def _load_notes(self, dt):
        if hasattr(self.ids, 'notes_list'):
            self.ids.notes_list.clear_widgets()  
            session_data = MDApp.get_running_app().session_manager.get_session()
            user_id = session_data.get("user_id", None) if session_data else "Guest"
            user_notes = notes_collection.find({"user_id": user_id})
            for note in user_notes:
                title = note.get("title", "")
                description = note.get("description", "")
                note_item = OneLineListItem(
                    text=title,
                    on_release=lambda x, t=title, d=description: self.show_note_details(t, d)
                )
                self.ids.notes_list.add_widget(note_item)
                self.notes.append(f"{title}\n{description}")

    def show_add_note_popup(self):
        self.dialog = MDDialog(
            title="Add Note",
            type="custom",
            content_cls=NotePopupContent(),
            buttons=[
                MDFlatButton(text="CANCEL", on_release=self.dismiss_popup),
                MDRaisedButton(text="ADD", on_release=self.add_note),
            ],
            size_hint=(0.8, None),
            height=dp(300))
        self.dialog.open()

    def add_note(self, *args):
        content = self.dialog.content_cls
        title = content.title_field.text.strip()
        description = content.description_field.text.strip()
        if title or description:
            note_item = OneLineListItem(
                text=title,
                on_release=lambda x, t=title, d=description: self.show_note_details(t, d))
            self.ids.notes_list.add_widget(note_item)
            session_data = MDApp.get_running_app().session_manager.get_session()
            user_id = session_data.get("user_id", None) if session_data else "Guest"
            notes_collection.insert_one({
                "title": title, 
                "description": description, 
                "user_id": user_id})
        self.dismiss_popup()

    def show_note_details(self, title, description):
        scroll_view = MDScrollView()

        description_label = MDLabel(
            text=description,
            size_hint_y=None,
            height=dp(200),  # Set a height for the label
            valign="top",
            halign="left",
            padding=(dp(10), dp(10)),  # Add padding for better readability
        )
        description_label.bind(texture_size=description_label.setter("size"))  # Adjust size to fit text
        scroll_view.add_widget(description_label)

        # Create and open the dialog
        dialog = MDDialog(
            title=title,
            text=description,
            buttons=[
                MDFlatButton(text="CLOSE", on_release=lambda x: dialog.dismiss())
            ],
            size_hint=(0.8, None),
        )
        dialog.open()
    

    def dismiss_popup(self, *args):
        if hasattr(self, 'dialog'):
            self.dialog.dismiss()

    def logout(self):
        app = MDApp.get_running_app()
        if hasattr(app, 'session_manager'):
            app.session_manager.clear_session()
        self.manager.current = "login_screen"
        
class AdminHomeScreen(Screen):
    def on_enter(self):
        if hasattr(self.ids, 'user_list'):
            self.ids.user_list.clear_widgets()
            users = [
                "User 1: John Doe - Student",
                "User 2: Alice Smith - Admin",
                "User 3: Bob Johnson - Student",
            ]
            for user in users:
                self.ids.user_list.add_widget(OneLineListItem(text=user))

    def go_back(self):
        app = MDApp.get_running_app()
        if hasattr(app, 'session_manager'):
            app.session_manager.clear_session()
        self.manager.current = "login_screen"