from kivy.uix.screenmanager import Screen
from kivy.lang import Builder
from kivymd.app import MDApp
from kivy.properties import ListProperty
from kivymd.uix.list import OneLineListItem
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.textfield import MDTextField
from kivy.uix.boxlayout import BoxLayout
from kivy.metrics import dp
from config import notes_collection
from kivymd.app import MDApp  

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
            multiline=False,  # Single line for title
            size_hint_y=None,
            height=dp(48)
        )
        self.add_widget(self.title_field)

        # Description Field (Multiline)
        self.description_field = MDTextField(
            hint_text="Description",
            mode="rectangle",
            multiline=True,  # Enable multiline
            size_hint_y=None,
            height=dp(100)  # Initial height, will adjust dynamically
        )
        self.add_widget(self.description_field)

        # Bind to adjust height dynamically
        self.description_field.bind(height=self.adjust_height)

    def adjust_height(self, instance, value):
        """Adjust the height of the popup content based on the description field."""
        self.height = self.title_field.height + self.description_field.height + dp(20)
        
        
 
class GuestHomeScreen(Screen):
    notes = ListProperty([])

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
            height=dp(300) 
        )
        self.dialog.open()

    def add_note(self, *args):
        content = self.dialog.content_cls
        title = content.title_field.text.strip()
        description = content.description_field.text.strip()
        if title or description: 
            note_text = f"{title}\n{description}" 
            self.ids.notes_list.add_widget(OneLineListItem(text=note_text))
            self.notes.append(note_text)
            session_data = MDApp.get_running_app().session_manager.get_session()
            print(f"Session Data: {session_data}\n\n\n")
            if session_data:
                username = session_data.get("username", "Guest")
            else:
                username = "Guest"
            notes_collection.insert_one({"title": title, "description": description, "user": username})

        self.dismiss_popup()

    def dismiss_popup(self, *args):
        self.dialog.dismiss()

    def change_screen(self, screen_name):
        if screen_name == 'logout_screen':
            self.logout()
        self.manager.current = screen_name

    def logout(self):
        self.app.session_manager.clear_session()
        self.manager.current = "login_screen"


        
class AdminHomeScreen(Screen):
    def on_enter(self):
        users = [
            "User 1: John Doe - Student",
            "User 2: Alice Smith - Admin",
            "User 3: Bob Johnson - Student",
        ]
        self.ids.user_list.clear_widgets()
        for user in users:
            self.ids.user_list.add_widget(OneLineListItem(text=user))

    def go_back(self):
        MDApp.get_running_app().session_manager.clear_session()
        self.manager.current = "login_screen"
