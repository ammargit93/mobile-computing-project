from kivy.lang import Builder
from kivy.uix.screenmanager import Screen, ScreenManager
from kivymd.app import MDApp
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")  
db = client["appDB"]  
users_collection = db["users"]
 
class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    def login(self):
        username = self.ids.username.text
        password = self.ids.password.text
        print(username, password)
        if username and password:
            user = users_collection.find_one({"username": username, "password": password})
            if user:
                print(f"Login successful for {username}")
                self.manager.get_screen("home_screen").welcome_user(username)  
                self.go_to_home()
            else:
                print("User not found. Redirecting to Signup.")
                self.go_to_signup()  
        else:
            print("Please fill in all fields")
    def go_to_signup(self):
        self.manager.current = "signup_screen"  
    def go_to_home(self):
        self.manager.current = "home_screen"



class SignupScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def signup(self):
        username = self.ids.username.text
        email = self.ids.email.text
        password = self.ids.password.text

        if username and email and password:
            existing_user = users_collection.find_one({"username": username})
            if existing_user:
                print("Username already exists.")
            else:
                users_collection.insert_one({"username": username, "email": email, "password": password})
                self.manager.current = "login_screen"
                print(f"Signup successful for {username}")
        else:
            print("Please fill in all fields")

class HomeScreen(Screen):
    def welcome_user(self, username):
        self.ids.welcome_label.text = f"Welcome {username}!"



class AuthApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Teal"
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name="login_screen"))
        sm.add_widget(SignupScreen(name="signup_screen"))
        sm.add_widget(HomeScreen(name="home_screen")) 
        return sm

    def go_back(self):
        login_screen = self.root.get_screen("login_screen")
        login_screen.ids.username.text = ""
        login_screen.ids.password.text = ""
        self.root.current = "login_screen"

    
    


if __name__ == '__main__':
    AuthApp().run()
