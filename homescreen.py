from kivy.uix.screenmanager import Screen  # Import the Screen class
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
from kivymd.uix.selectioncontrol import MDCheckbox
from kivy.metrics import dp
from model import *
from PIL import Image, ImageDraw, ImageFont
from kivy.graphics.texture import Texture
from kivymd.uix.selectioncontrol import MDSwitch
from pymongo import MongoClient
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.utils import platform
from kivy.network.urlrequest import UrlRequest
import requests
# from auth import history_collection
from dotenv import load_dotenv

client = MongoClient("mongodb://localhost:27017/")
db = client["appDB"]
history_collection = db['history']

load_dotenv()
class HomeScreen(Screen):  # Now Screen is properly imported
    def __init__(self, **kwargs):
        super(HomeScreen, self).__init__(**kwargs)
        self.rag_chain = None 
        
    def home(self):
        self.ids.chat_container.clear_widgets()  # Clear previous messages
        
    def send_message(self):
        user_input = self.ids.message_input.text.strip()
        if not user_input:
            return
        self.add_message(user_input, [0.2, 0.2, 0.6, 1], align="right")
        self.ids.message_input.text = ""
        resp = requests.get('http://localhost:5000/query')
        try:
            if self.rag_chain:
                response = self.rag_chain.run(user_input)
            else:response = chat_with_llama(prompt=user_input)
            history_collection.insert_one({"user":user_input,"bot":response})
            self.add_message(response, [0.2, 0.2, 0.2, 1], align="full")
        except Exception as e:
            self.add_message(f"Error: {e}", [0.6, 0.2, 0.2, 1], align="full")

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
        self.file_chooser = FileChooserListView(filters=["*.txt", "*.pdf", "*.docx"])
        self.file_chooser.bind(on_submit=self.handle_file_selection)
        
        self.popup = Popup(
            title="Upload a Document",
            content=self.file_chooser,
            size_hint=(0.9, 0.9)
        )
        self.popup.open()


    def handle_file_selection(self, instance, selection, *args):
        if selection and len(selection) > 0:
            selected_file = selection[0]
            print(f"Selected file: {selected_file}")
            if hasattr(self, "popup") and self.popup:
                self.popup.dismiss()

            self.add_message(f"📄 Uploaded file: {selected_file}", [0.2, 0.6, 0.2, 1], align="right")

            try:
                os.environ["OPENAI_API_KEY"] = os.getenv("GROQ_TOKEN")  
                os.environ["OPENAI_API_BASE"] = "https://api.groq.com/openai/v1"

                llm = ChatOpenAI(model_name="llama3-8b-8192", temperature=0.3)
                loader = PyMuPDFLoader(selected_file)
                documents = loader.load()

                text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
                docs = text_splitter.split_documents(documents)

                embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
                vectorstore = FAISS.from_documents(docs, embedding)

                retriever = vectorstore.as_retriever()
                self.rag_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever, chain_type="stuff")
                self.add_message("Document processed. You can now ask questions about it.", [0.2, 0.6, 0.2, 1], align="right")

            except Exception as e:
                self.add_message(f"❌ Error processing file: {e}", [0.6, 0.2, 0.2, 1], align="full")
                                
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
        
    def toggle_biometric(self, is_active):
        if is_active:
            print("✅ Biometric Authentication Enabled")
            self.add_message("Biometric Authentication Enabled", [0.2, 0.6, 0.2, 1], align="right")
        else:
            print("❌ Biometric Authentication Disabled")
            self.add_message("Biometric Authentication Disabled", [0.6, 0.2, 0.2, 1], align="right")

    def menu_callback(self, option):
        print(f"Selected: {option}")  # Debugging print
        if hasattr(self, "menu") and self.menu:
            self.menu.dismiss()
        self.ids.nav_drawer.set_state("close")