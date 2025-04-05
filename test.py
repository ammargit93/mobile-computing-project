from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from pyzbar.pyzbar import decode
from PIL import Image

class QRFromFile(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        
        self.label = Label(text="Click to scan QR from image", size_hint_y=0.2)
        self.add_widget(self.label)

        self.button = Button(text="Scan QR Code from File")
        self.button.bind(on_press=self.scan_qr_from_file)
        self.add_widget(self.button)

    def scan_qr_from_file(self, instance):
        try:
            path = "dummy.png"
            image = Image.open(path)
            result = decode(image)

            if result:
                qr_data = result[0].data.decode('utf-8')
                self.label.text = f"Scanned Data:\n{qr_data}"
            else:
                self.label.text = "No QR code found in image."
        except Exception as e:
            self.label.text = f"Error: {e}"

class QRApp(App):
    def build(self):
        return QRFromFile()

if __name__ == '__main__':
    QRApp().run()
