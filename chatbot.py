from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty, BooleanProperty, ObjectProperty, NumericProperty
from kivy.clock import Clock
from kivy.core.window import Window
from kivymd.uix.filemanager import MDFileManager
import os

class ChatMessage(Screen):
    message = StringProperty()
    sender = StringProperty()
    is_bot = BooleanProperty(False)
    minimum_height = NumericProperty(80)

class FileBubble(Screen):
    file_name = StringProperty()
    file_size = StringProperty()
    file_icon = StringProperty("file")
    file_path = StringProperty()

class ChatScreen(Screen):
    file_manager = ObjectProperty(None)
    selected_file = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Window.bind(on_keyboard=self.events)
        self.file_manager = MDFileManager(
            exit_manager=self.exit_manager,
            select_path=self.select_path,
            preview=True,
            ext=[".pdf", ".txt", ".docx", ".jpg", ".png", ".jpeg", ".csv"]
        )
        self.message_callback = None

    def set_message_callback(self, callback):
        """Set callback for outgoing messages"""
        self.message_callback = callback

    def add_message(self, message, sender, is_bot=False):
        """Add a message to the chat"""
        chat_list = self.ids.chat_list
        msg = ChatMessage(message=message, sender=sender, is_bot=is_bot)
        chat_list.add_widget(msg)
        Clock.schedule_once(lambda dt: self.scroll_to_bottom(), 0.1)

    def add_file_message(self, file_path):
        """Add a file message to the chat"""
        if not os.path.exists(file_path):
            return

        file_name = os.path.basename(file_path)
        file_size = self._get_file_size(file_path)
        file_ext = os.path.splitext(file_path)[1].lower()
        file_icon = self._get_file_icon(file_ext)

        chat_list = self.ids.chat_list
        file_bubble = FileBubble(
            file_name=file_name,
            file_size=file_size,
            file_icon=file_icon,
            file_path=file_path
        )
        chat_list.add_widget(file_bubble)
        Clock.schedule_once(lambda dt: self.scroll_to_bottom(), 0.1)

    def _get_file_size(self, file_path):
        """Return human-readable file size"""
        size = os.path.getsize(file_path)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def _get_file_icon(self, file_ext):
        """Return appropriate icon based on file extension"""
        icon_mapping = {
            '.pdf': 'file-pdf-box',
            '.txt': 'file-document',
            '.doc': 'file-word',
            '.docx': 'file-word',
            '.jpg': 'file-image',
            '.jpeg': 'file-image',
            '.png': 'file-image',
            '.xls': 'file-excel',
            '.xlsx': 'file-excel',
            '.csv': 'file-excel',
            '.ppt': 'file-powerpoint',
            '.pptx': 'file-powerpoint'
        }
        return icon_mapping.get(file_ext, 'file')

    def send_message(self):
        """Handle sending of messages"""
        message = self.ids.message_input.text.strip()
        if message:
            self.ids.message_input.text = ""
            if self.message_callback:
                self.message_callback(message, False)

    def scroll_to_bottom(self):
        """Scroll chat to the bottom"""
        self.ids.chat_scroll.scroll_y = 0

    def show_file_chooser(self):
        """Show file chooser dialog"""
        self.file_manager.show(os.path.expanduser("~"))

    def select_path(self, path):
        """Handle file selection"""
        self.exit_manager()
        self.add_file_message(path)

    def exit_manager(self, *args):
        """Close file manager"""
        self.file_manager.close()

    def events(self, instance, keyboard, keycode, text, modifiers):
        """Handle keyboard events"""
        if keyboard in (1001, 27):
            if self.file_manager.exit_manager is None:
                return False
            self.file_manager.back()
        return True