from kivy.uix.screenmanager import Screen
from kivy.lang import Builder
from kivymd.app import MDApp
from kivy.properties import ListProperty
from kivymd.uix.list import OneLineListItem
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.textfield import MDTextField

class GuestHomeScreen(Screen):
    notes = ListProperty([])  # Stores notes

    def show_add_note_popup(self):
        """Displays a popup to add a note."""
        self.dialog = MDDialog(
            title="Add Note",
            type="custom",
            content_cls=MDTextField(hint_text="Type your note here"),
            buttons=[
                MDFlatButton(text="CANCEL", on_release=self.dismiss_popup),
                MDRaisedButton(text="ADD", on_release=self.add_note),
            ],
        )
        self.dialog.open()

    def add_note(self, *args):
        """Adds a new note to the list."""
        note_text = self.dialog.content_cls.text.strip()
        if note_text:
            self.ids.notes_list.add_widget(OneLineListItem(text=note_text))
            self.notes.append(note_text)
        self.dismiss_popup()

    def dismiss_popup(self, *args):
        """Closes the popup."""
        self.dialog.dismiss()

    def go_back(self):
        """Returns to the login screen."""
        self.manager.current = "login_screen"


class AdminHomeScreen(Screen):
    def on_enter(self):
        """Displays dummy user data when entering the Admin screen."""
        users = [
            "User 1: John Doe - Student",
            "User 2: Alice Smith - Admin",
            "User 3: Bob Johnson - Student",
        ]
        self.ids.user_list.clear_widgets()
        for user in users:
            self.ids.user_list.add_widget(OneLineListItem(text=user))

    def go_back(self):
        """Returns to the login screen."""
        self.manager.current = "login_screen"

