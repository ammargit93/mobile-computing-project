from kivy.uix.screenmanager import Screen
from kivy.uix.filechooser import FileChooserListView
from kivymd.uix.list import TwoLineAvatarListItem, IconLeftWidget
from kivy.properties import ListProperty, StringProperty
from kivymd.uix.button import MDFloatingActionButton, MDFlatButton, MDRaisedButton
from kivymd.uix.dialog import MDDialog
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.snackbar import MDSnackbar
from config import files_collection
from kivy.metrics import dp
from datetime import datetime
from kivy.clock import Clock
from kivymd.app import MDApp
import shutil
import uuid
import os


UPLOAD_FOLDER = "uploads"

def save_file_locally(file_path, user_id, original_filename):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    file_size = os.path.getsize(file_path)
    unique_filename = os.path.basename(file_path)
    file_type = os.path.splitext(unique_filename)[1][1:].lower() or "file"
    
    files_collection.insert_one({
        "user_id": user_id,
        "original_filename": original_filename,
        "unique_filename": unique_filename,
        "filepath": file_path,
        "size": file_size,
        "uploaded_at": datetime.now(),
        "type": file_type,
        "description": "" 
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
        self.screen = screen_instance
        self.orientation = "vertical"
        self.spacing = dp(10)
        self.padding = dp(10)
        self.size_hint_y = None
        self.height = dp(400)
        
        self.file_chooser = FileChooserListView(
            size_hint=(1, 1),
            path=os.path.expanduser("~"),
            filters=['*'],
        )
        
        self.file_chooser.background_color = get_color_from_hex("#333333")
        self.file_chooser.color = get_color_from_hex("#FFFFFF")
        self.file_chooser.selection_color = get_color_from_hex("#4CAF50")
        self.file_chooser.border = [10, 10, 10, 10]
        
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
        
        cancel_btn.bind(on_release=self.screen.dismiss_file_chooser)
        select_btn.bind(on_release=self.screen.use_selected_file)
        
        button_box.add_widget(cancel_btn)
        button_box.add_widget(select_btn)
        
        self.add_widget(self.file_chooser)
        self.add_widget(button_box)
        
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
        Clock.schedule_once(self._load_files)

    def _load_files(self, dt):
        if hasattr(self.ids, 'files_list'):
            self.ids.files_list.clear_widgets()
            session_data = MDApp.get_running_app().session_manager.get_session()
            user_id = session_data.get("user_id", None) if session_data else None
            
            if not user_id:
                self.show_snackbar("Not logged in")
                return
                
            user_files = files_collection.find({"user_id": user_id}).sort("uploaded_at", -1)
            self.files = []
            
            for file in user_files:
                file_size = self._format_size(file.get("size", 0))
                file_type = file.get("type", "file")
                description = file.get("description", "")
                
                secondary_text = f"Size: {file_size} | Type: {file_type}"
                if description:
                    secondary_text += f"\n{description}"
                
                item = TwoLineAvatarListItem(
                    text=file.get("original_filename", "Untitled"),
                    secondary_text=secondary_text,
                    on_release=lambda x, f=file: self.open_file(f)
                )
                icon = IconLeftWidget(
                    icon=self._get_file_icon(file_type),
                    theme_text_color="Custom",
                    text_color=MDApp.get_running_app().theme_cls.primary_color
                )
                item.add_widget(icon)
                self.ids.files_list.add_widget(item)
                self.files.append(file)

    def _format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f}{unit}"
            size /= 1024.0
        return f"{size:.1f}TB"

    def _get_file_icon(self, file_type):
        file_type = file_type.lower()
        if file_type == "pdf":
            return "file-pdf-box"
        elif file_type in ["jpg", "jpeg", "png", "gif", "bmp"]:
            return "file-image"
        elif file_type in ["doc", "docx"]:
            return "file-word"
        elif file_type in ["xls", "xlsx"]:
            return "file-excel"
        elif file_type in ["ppt", "pptx"]:
            return "file-powerpoint"
        elif file_type in ["mp4", "avi", "mov", "mkv"]:
            return "file-video"
        elif file_type in ["mp3", "wav", "ogg"]:
            return "file-music"
        else:
            return "file"

    def show_file_chooser(self):
        content = FileChooserContent(screen_instance=self)  
        self.file_dialog = MDDialog(
            title="[color=ffffff]Select File to Upload[/color]",
            type="custom",
            content_cls=content,
            size_hint=(0.9, 0.7),
            md_bg_color=get_color_from_hex("#333333"),
            radius=[20, 20, 20, 20]
        )
        self.file_dialog.open()

    def use_selected_file(self, *args):
        if self.selected_file:
            original_name = os.path.basename(self.selected_file)
            self.dismiss_file_chooser()
            self.show_upload_dialog(original_name)

    def dismiss_file_chooser(self, *args):
        if self.file_dialog:
            self.file_dialog.dismiss()

    def show_upload_dialog(self, file_name=""):
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
        content = self.upload_dialog.content_cls
        original_filename = content.file_name.text.strip()
        description = content.file_desc.text.strip()
        
        if not original_filename:
            self.show_snackbar("File name cannot be empty")
            return
            
        if not self.selected_file:
            self.show_snackbar("No file selected")
            return
            
        session_data = MDApp.get_running_app().session_manager.get_session()
        user_id = session_data.get("user_id", None) if session_data else None
        
        if not user_id:
            self.show_snackbar("Not logged in")
            return
            
        try:
            if not os.path.exists(UPLOAD_FOLDER):
                os.makedirs(UPLOAD_FOLDER)
                
            file_ext = os.path.splitext(self.selected_file)[1]
            unique_filename = f"{uuid.uuid4()}{file_ext}"
            dest_path = os.path.join(UPLOAD_FOLDER, unique_filename)
            
            shutil.copy2(self.selected_file, dest_path)
            
            # Update the document with description
            files_collection.insert_one({
                "user_id": user_id,
                "original_filename": original_filename,
                "unique_filename": unique_filename,
                "filepath": dest_path,
                "size": os.path.getsize(dest_path),
                "uploaded_at": datetime.now(),
                "type": file_ext[1:].lower() or "file",
                "description": description
            })
            
            self._load_files(0)
            self.show_snackbar(f"File '{original_filename}' uploaded successfully!")
            self.dismiss_upload_dialog()
        except Exception as e:
            self.show_snackbar(f"Upload failed: {str(e)}")

    def dismiss_upload_dialog(self, *args):
        if self.upload_dialog:
            self.upload_dialog.dismiss()
            self.upload_dialog = None
            self.selected_file = ""

    def open_file(self, file_data):
        file_size = self._format_size(file_data.get("size", 0))
        file_type = file_data.get("type", "file")
        description = file_data.get("description", "No description")
        
        text = [
            f"Original Name: {file_data.get('original_filename', 'Unknown')}",
            f"Stored As: {file_data.get('unique_filename', 'Unknown')}",
            f"Type: {file_type}",
            f"Size: {file_size}",
            f"Uploaded: {file_data.get('uploaded_at', 'Unknown')}",
            f"Path: {file_data.get('filepath', 'Unknown')}",
            f"\nDescription: {description}"
        ]
        
        dialog = MDDialog(
            title=file_data.get("original_filename", "File"),
            text="\n".join(text),
            buttons=[
                MDFlatButton(text="CLOSE", on_release=lambda x: dialog.dismiss()),
                MDFlatButton(text="OPEN", on_release=lambda x: self._open_file_externally(file_data))
            ],
            size_hint=(0.8, None),
        )
        dialog.open()

    def _open_file_externally(self, file_data):
        """Open file using system default application"""
        try:
            filepath = file_data.get("filepath")
            if filepath and os.path.exists(filepath):
                import platform
                if platform.system() == 'Windows':
                    os.startfile(filepath)
                elif platform.system() == 'Darwin':
                    os.system(f'open "{filepath}"')
                else:
                    os.system(f'xdg-open "{filepath}"')
            else:
                self.show_snackbar("File not found")
        except Exception as e:
            self.show_snackbar(f"Could not open file: {str(e)}")

    def refresh_files(self):
        self._load_files(0)
    def nav_to_ocr(self):
        """Navigate to OCR screen"""
        self.manager.current = "ocr_screen"
    def nav_to_chatbot(self):
        """Navigate to chatbot screen"""
        self.manager.current = "chatbot_screen"
    def nav_to_home(self):
        """Navigate to home screen"""
        self.manager.current = "home_screen"
    def show_snackbar(self, message):
        MDSnackbar(
            MDLabel(
                text=message,
                theme_text_color="Custom",
                text_color=get_color_from_hex("#FFFFFF")
            ),
            y=dp(24),
            pos_hint={"center_x": 0.5},
            size_hint_x=0.9,
            md_bg_color=get_color_from_hex("#333333"),
            radius=[10, 10, 10, 10]
        ).open()