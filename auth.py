from kivy.metrics import dp
from kivy.lang import Builder
from session import SessionManager
from kivy.uix.screenmanager import Screen, ScreenManager
from kivymd.app import MDApp
from pymongo import MongoClient
from kivymd.uix.snackbar.snackbar import MDSnackbar, MDSnackbarActionButton
from kivymd.uix.label import MDLabel
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.properties import StringProperty, ListProperty
from kivy.graphics import Color, RoundedRectangle
from homescreen import HomeScreen

client = MongoClient("mongodb://localhost:27017/")
db = client["appDB"]
users_collection = db["users"]

class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def login(self):
        username = self.ids.username.text
        password = self.ids.password.text
        # roletype = self.ids.roletype.text
        if username and password:
            user = users_collection.find_one({"username": username, "password": password})
            if user:
                self.show_snackbar(f"Login successful for {username}", "green")
                self.manager.get_screen("home_screen").welcome_user(username)
                self.go_to_home()
                app = MDApp.get_running_app()
                app.session_manager.create_session(username)
            else:
                self.show_snackbar("User not found. Redirecting to Signup.", "red")
                self.go_to_signup()
        else:
            self.show_snackbar("Please fill in all fields", "orange")

    def show_snackbar(self, message, color):
        snackbar = MDSnackbar(
            MDLabel(text=message),
            MDSnackbarActionButton(
                text="Done",
                theme_text_color="Custom",
                text_color=color,
            ),
            y=dp(24),
            pos_hint={"center_x": 0.5},
            size_hint_x=0.9,
            md_bg_color="#E8D8D7",
        )
        snackbar.open()

    def go_to_signup(self):
        self.manager.current = "signup_screen"
    
    def go_to_login(self):
        self.manager.current = "login_screen"
    
    def go_to_home(self):
        self.manager.current = "home_screen"


class SignupScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.role_menu = None

    def on_kv_post(self, *args):
        # This method is called after the KV rules have been applied
        self.create_role_dropdown()

    def create_role_dropdown(self):
        role_options = ["Client", "Freelancer"]
        menu_items = [
            {
                "text": role,
                "viewclass": "OneLineListItem",
                "on_release": lambda x=role: self.set_role(x),
            }
            for role in role_options
        ]

        self.role_menu = MDDropdownMenu(
            caller=self.ids.roletype,  # Now self.ids is available
            items=menu_items,
            width_mult=3
        )

    def open_role_dropdown(self):
        self.role_menu.open()

    def set_role(self, role):
        self.ids.roletype.text = role
        self.role_menu.dismiss()

    def signup(self):
        username = self.ids.username.text
        email = self.ids.email.text
        password = self.ids.password.text
        confirm_password = self.ids.confirm_password.text
        role = self.ids.roletype.text
        
        if username and email and role != "Select Role" and password and confirm_password:
            if password != confirm_password:
                self.show_snackbar("Passwords do not match!", "red")
                return

            existing_user = users_collection.find_one({"username": username})
            if existing_user:
                self.show_snackbar("Username already exists.", "red")
            else:
                users_collection.insert_one(
                    {"username": username, "email": email, "password": password, "roletype": role}
                )
                self.manager.current = "login_screen"
                self.show_snackbar(f"Signup successful for {username}", "green")
        else:
            self.show_snackbar("Please fill in all fields", "orange")

    def show_snackbar(self, message, color):
        snackbar = MDSnackbar(
            MDLabel(
                text=message,
            ),
            MDSnackbarActionButton(
                text="Done",
                theme_text_color="Custom",
                text_color=color,
            ),
            y=dp(24),
            pos_hint={"center_x": 0.5},
            size_hint_x=0.5,
            md_bg_color="#E8D8D7",
        )
        snackbar.open()
        

class PreAuthScreen(Screen):
    def get_started(self):
        self.manager.current = "login_screen"


class AuthApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.session_manager = SessionManager()

    def build(self):
        # Load KV files from UI folder
        Builder.load_file('UI/authapp.kv')
        Builder.load_file('UI/homepage.kv')

        self.theme_cls.primary_palette = "Teal"
        sm = ScreenManager()

        session = self.session_manager.get_session()
        if session:
            sm.add_widget(HomeScreen(name="home_screen"))
            sm.current = "home_screen"
            sm.get_screen("home_screen").home()
        else:
            sm.add_widget(PreAuthScreen(name="pre_auth_screen"))
            sm.current = "pre_auth_screen"

        sm.add_widget(LoginScreen(name="login_screen"))
        sm.add_widget(SignupScreen(name="signup_screen"))
        sm.add_widget(HomeScreen(name="home_screen"))

        return sm

    def go_back(self):
        login_screen = self.root.get_screen("login_screen")
        login_screen.ids.username.text = ""
        login_screen.ids.password.text = ""
        self.root.current = "login_screen"
