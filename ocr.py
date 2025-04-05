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
from config import images_collection  
import os
import shutil
import cv2
from pyzbar.pyzbar import decode
from kivy.uix.behaviors import ButtonBehavior
import webbrowser

UPLOAD_FOLDER = "uploads"

class ClickableMDLabel(ButtonBehavior, MDLabel):
    """A clickable MDLabel that can handle links"""
    pass

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
            hint_text="Image Name",
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
            filters=['*.png', '*.jpg', '*.jpeg', '*.pdf', '*.bmp'],
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

class QRScannerContent(MDBoxLayout):
    """Improved QR code scanner dialog content with proper spacing"""
    def __init__(self, qr_data, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = dp(15)
        self.padding = [dp(20), dp(10), dp(20), dp(20)]
        self.size_hint_y = None
        self.height = dp(180)
        
        # Title with proper spacing
        title_label = MDLabel(
            text="QR Code Content:",
            halign="center",
            font_style="H6",
            size_hint_y=None,
            height=dp(40),
            padding=[0, dp(10)]
        )
        self.add_widget(title_label)
        
        # Main content area with scrollable text if needed
        content_box = MDBoxLayout(
            orientation="vertical",
            spacing=dp(10),
            size_hint_y=None,
            height=dp(100)
        )
        
        # Create a properly styled clickable label
        self.link_label = ClickableMDLabel(
            text=qr_data,
            halign="center",
            markup=True,
            theme_text_color="Custom",
            text_color=get_color_from_hex("#2196F3"),
            font_style="Subtitle1",
            size_hint_y=None,
            height=dp(48),
            padding=[dp(10), 0]
        )
        self.link_label.bind(on_release=lambda x: self.open_link(qr_data))
        content_box.add_widget(self.link_label)
        
        self.add_widget(content_box)
        
    def open_link(self, url):
        try:
            if not url.startswith(('http://', 'https://')):
                url = 'http://' + url
            webbrowser.open(url)
        except Exception as e:
            MDApp.get_running_app().show_snackbar(f"Could not open link: {str(e)}")

class OCRScreen(Screen):
    files = ListProperty([])
    selected_file = StringProperty("")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.files = []
        self.upload_dialog = None
        self.file_dialog = None
        self.qr_dialog = None
        self.selected_file = ""
        self.qr_mode = False

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
                
            user_files = images_collection.find({"user_id": user_id}).sort("uploaded_at", -1)
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
        if file_type in ["jpg", "jpeg", "png", "gif", "bmp"]:
            return "file-image"
        elif file_type == "pdf":
            return "file-pdf"
        else:
            return "file"

    def show_file_chooser(self, qr_mode=False):
        self.qr_mode = qr_mode
        title = "Select QR Code Image" if qr_mode else "Select File to Upload"
        content = FileChooserContent(screen_instance=self)  
        self.file_dialog = MDDialog(
            title=f"[color=ffffff]{title}[/color]",
            type="custom",
            content_cls=content,
            size_hint=(0.9, 0.7),
            md_bg_color=get_color_from_hex("#333333"),
            radius=[20, 20, 20, 20]
        )
        self.file_dialog.open()

    def use_selected_file(self, *args):
        if self.selected_file:
            if self.qr_mode:
                self.scan_qr_code(self.selected_file)
                self.dismiss_file_chooser()
            else:
                original_name = os.path.basename(self.selected_file)
                self.dismiss_file_chooser()
                self.show_upload_dialog(original_name)

    def dismiss_file_chooser(self, *args):
        if self.file_dialog:
            self.file_dialog.dismiss()
            self.qr_mode = False

    def show_upload_dialog(self, file_name=""):
        content = FileUploadContent()
        if file_name:
            content.file_name.text = file_name
            
        self.upload_dialog = MDDialog(
            title="Upload Image",
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
            self.show_snackbar("Image name cannot be empty")
            return
            
        if not self.selected_file:
            self.show_snackbar("No Image selected")
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
            
            images_collection.insert_one({
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
                MDFlatButton(text="OPEN", on_release=lambda x: self._open_file_externally(file_data)),
                MDFlatButton(text="SCAN QR", on_release=lambda x: self.show_file_chooser(qr_mode=True))
            ],
            size_hint=(0.8, None),
        )
        dialog.open()

    def scan_qr_code(self, image_path):
        try:
            img = cv2.imread(image_path)
            
            if img is None:
                self.show_snackbar("Could not read the image file")
                return
                
            decoded_objects = decode(img)
            
            if not decoded_objects:
                self.show_snackbar("No QR code found in the image")
                return
                
            qr_data = decoded_objects[0].data.decode("utf-8")
            self.show_qr_result(qr_data)
            
        except Exception as e:
            self.show_snackbar(f"QR scanning failed: {str(e)}")

    def show_qr_result(self, qr_data):
        """Improved QR result dialog with proper spacing"""
        self.qr_dialog = MDDialog(
            title="[size=20]QR Code Scan Result[/size]",
            type="custom",
            content_cls=QRScannerContent(qr_data=qr_data),
            buttons=[
                MDFlatButton(
                    text="CLOSE", 
                    on_release=lambda x: self.qr_dialog.dismiss(),
                    theme_text_color="Custom",
                    text_color=get_color_from_hex("#FFFFFF")
                )
            ],
            size_hint=(0.85, None),
            height=dp(280),
            md_bg_color=get_color_from_hex("#333333"),
            radius=[20, 20, 20, 20],
            overlay_color=(0, 0, 0, 0.7)
        )
        self.qr_dialog.open()

    def _open_file_externally(self, file_data):
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

    def nav_to_chatbot(self):
        self.manager.current = "chatbot_screen"

    def nav_to_ocr(self):
        self.manager.current = "ocr_screen"

    def refresh_files(self):
        self._load_files(0)

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