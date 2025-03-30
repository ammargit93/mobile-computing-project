from kivy.uix.screenmanager import Screen
from kivy.uix.filechooser import FileChooserListView
from kivymd.uix.list import TwoLineAvatarListItem, IconLeftWidget
from kivymd.uix.button import MDFloatingActionButton, MDFlatButton, MDRaisedButton
from kivymd.uix.dialog import MDDialog
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.snackbar import MDSnackbar
from kivy.metrics import dp
from kivy.properties import ListProperty, StringProperty
from kivy.clock import Clock
from kivymd.app import MDApp
import uuid
from datetime import datetime
from config import files_collection
import os

UPLOAD_FOLDER = "uploads"

def save_file_locally(file_data, user_id):
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    file_ext = os.path.splitext(file_data.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
    file_data.save(file_path)
    files_collection.insert_one({
        "user_id": user_id,
        "filename": file_data.filename,
        "filepath": file_path,
        "size": os.path.getsize(file_path),
        "uploaded_at": datetime.now()
    })
    
    return file_path



class FileUploadContent(MDBoxLayout):
    """Content for file upload dialog"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = dp(10)
        self.padding = dp(10)
        self.size_hint_y = None
        self.height = dp(150)
        
        self.file_name = MDTextField(
            hint_text="File Name",
            mode="rectangle",
            size_hint_y=None,
            height=dp(48))
        self.add_widget(self.file_name)
        
        self.file_desc = MDTextField(
            hint_text="Description (Optional)",
            mode="rectangle",
            size_hint_y=None,
            height=dp(48))
        self.add_widget(self.file_desc)

class FileChooserContent(MDBoxLayout):
    """Content for file chooser dialog with proper styling"""
    def __init__(self, screen_instance, **kwargs):
        super().__init__(**kwargs)
        self.screen = screen_instance  # Store reference to parent screen
        self.orientation = "vertical"
        self.spacing = dp(10)
        self.padding = dp(10)
        self.size_hint_y = None
        self.height = dp(400)
        
        # Create styled file chooser
        self.file_chooser = FileChooserListView(
            size_hint=(1, 1),
            path=os.path.expanduser("~"),  # Start at user home directory
            filters=['*'],  # Show all files
        )
        
        # Apply styling to file chooser
        self.file_chooser.background_color = get_color_from_hex("#333333")  # Dark background
        self.file_chooser.color = get_color_from_hex("#FFFFFF")  # White text
        self.file_chooser.selection_color = get_color_from_hex("#4CAF50")  # Green selection
        self.file_chooser.border = [10, 10, 10, 10]
        
        # Button box
        button_box = MDBoxLayout(
            size_hint_y=None,
            height=dp(50),
            spacing=dp(10),
            padding=dp(10)
        )
        cancel_btn = MDFlatButton(
            text="CANCEL",
            theme_text_color="Custom",
            text_color=get_color_from_hex("#FFFFFF")
        )
        select_btn = MDRaisedButton(
            text="SELECT",
            md_bg_color=get_color_from_hex("#4CAF50")
        )
        
        # Bind buttons to screen methods directly
        cancel_btn.bind(on_release=self.screen.dismiss_file_chooser)
        select_btn.bind(on_release=self.screen.use_selected_file)
        
        button_box.add_widget(cancel_btn)
        button_box.add_widget(select_btn)
        
        self.add_widget(self.file_chooser)
        self.add_widget(button_box)
        
        # Bind selection to update screen's selected_file
        self.file_chooser.bind(selection=lambda instance, value: 
                             setattr(self.screen, 'selected_file', value[0] if value else ""))

class FilesScreen(Screen):
    files = ListProperty([])
    selected_file = StringProperty("")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.files = []
        self.upload_dialog = None
        self.file_dialog = None
        self.selected_file = ""

    def on_enter(self):
        """Load files when screen is entered"""
        Clock.schedule_once(self._load_files)

    def _load_files(self, dt):
        """Load files from database"""
        if hasattr(self.ids, 'files_list'):
            self.ids.files_list.clear_widgets()
            session_data = MDApp.get_running_app().session_manager.get_session()
            username = session_data.get("username", "Guest") if session_data else "Guest"
            
            user_files = files_collection.find({"user": username})
            
            for file in user_files:
                item = TwoLineAvatarListItem(
                    text=file.get("name", "Untitled"),
                    secondary_text=f"Size: {file.get('size', '0')} | Type: {file.get('type', 'file')}",
                    on_release=lambda x, f=file: self.open_file(f)
                )
                icon = IconLeftWidget(
                    icon=self._get_file_icon(file.get("type", "")),
                    theme_text_color="Custom",
                    text_color=MDApp.get_running_app().theme_cls.primary_color
                )
                item.add_widget(icon)
                self.ids.files_list.add_widget(item)
                self.files.append(file)

    def _get_file_icon(self, file_type):
        """Return appropriate icon based on file type"""
        file_type = file_type.lower()
        if "pdf" in file_type:
            return "file-pdf-box"
        elif "image" in file_type:
            return "file-image"
        elif "word" in file_type:
            return "file-word"
        elif "excel" in file_type:
            return "file-excel"
        elif "powerpoint" in file_type:
            return "file-powerpoint"
        elif "video" in file_type:
            return "file-video"
        elif "audio" in file_type:
            return "file-music"
        else:
            return "file"

    def show_file_chooser(self):
        """Show styled file chooser dialog"""
        content = FileChooserContent(screen_instance=self)  # Pass self as screen_instance
        
        self.file_dialog = MDDialog(
            title="[color=ffffff]Select File to Upload[/color]",
            type="custom",
            content_cls=content,
            size_hint=(0.9, 0.7),
            md_bg_color=get_color_from_hex("#333333"),  # Dark dialog background
            radius=[20, 20, 20, 20]
        )
        
        # Set text color for dialog title
        self.file_dialog.title_color = get_color_from_hex("#FFFFFF")
        self.file_dialog.open()

    def use_selected_file(self, *args):
        """Use the selected file"""
        if self.selected_file:
            file_name = os.path.basename(self.selected_file)
            self.show_snackbar(f"Selected file: {file_name}")
            self.dismiss_file_chooser()
            self.show_upload_dialog(file_name)

    def dismiss_file_chooser(self, *args):
        """Close file chooser dialog"""
        if self.file_dialog:
            self.file_dialog.dismiss()

    def show_upload_dialog(self, file_name=""):
        """Show dialog for uploading new file"""
        if not self.upload_dialog:
            content = FileUploadContent()
            if file_name:
                content.file_name.text = file_name
                
            self.upload_dialog = MDDialog(
                title="Upload File",
                type="custom",
                content_cls=content,
                buttons=[
                    MDFlatButton(text="CANCEL", on_release=self.dismiss_upload_dialog),
                    MDRaisedButton(text="UPLOAD", on_release=self.process_upload),
                ],
                size_hint=(0.8, None),
            )
        self.upload_dialog.open()

    def process_upload(self, *args):
        """Handle file upload process"""
        content = self.upload_dialog.content_cls
        file_name = content.file_name.text.strip()
        description = content.file_desc.text.strip()
        
        if file_name:
            session_data = MDApp.get_running_app().session_manager.get_session()
            username = session_data.get("username", "Guest") if session_data else "Guest"
            
            files_collection.insert_one({
                "name": file_name,
                "description": description,
                "user": username,
                "size": "0KB",
                "type": "file"
            })
            
            self._load_files(0)
            self.show_snackbar(f"File '{file_name}' added successfully!")
            
        self.dismiss_upload_dialog()

    def dismiss_upload_dialog(self, *args):
        """Close the upload dialog"""
        if self.upload_dialog:
            self.upload_dialog.dismiss()

    def open_file(self, file_data):
        """Handle opening/viewing a file"""
        dialog = MDDialog(
            title=file_data.get("name", "File"),
            text=f"Type: {file_data.get('type', 'Unknown')}\n"
                 f"Size: {file_data.get('size', '0')}\n"
                 f"Description: {file_data.get('description', 'None')}",
            buttons=[
                MDFlatButton(text="CLOSE", on_release=lambda x: dialog.dismiss())
            ],
            size_hint=(0.8, None),
        )
        dialog.open()

    def refresh_files(self):
        """Refresh the files list"""
        self._load_files(0)

    def show_snackbar(self, message):
        """Show visible snackbar notification"""
        snackbar = MDSnackbar(
            MDLabel(
                text=message,
                theme_text_color="Custom",
                text_color=get_color_from_hex("#FFFFFF")  # White text
            ),
            y=dp(24),
            pos_hint={"center_x": 0.5},
            size_hint_x=0.9,
            md_bg_color=get_color_from_hex("#333333"),  # Dark background
            radius=[10, 10, 10, 10]
        )
        snackbar.open()