import json
from tkinter import filedialog

import customtkinter as ctk

import make_video_pdf_engine

ctk.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"




class CustomTkinterApp:
    def __init__(self, master):

        self.master = master
        self.master.title("PDF Video Maker")
        self.master.geometry("750x600")

        self.pdf_file = ""
        self.mp3_file = ""

        self.blur_val = ctk.IntVar(value=8)
        self.brightness_val = ctk.DoubleVar(value=0.5)
        self.fade_duration_val = ctk.DoubleVar(value=0.5)
        self.main_audio_volume_val = ctk.DoubleVar(value=1.7)
        self.bg_audio_volume_val = ctk.DoubleVar(value=0.04)

        self.aws_access_key_val = ctk.StringVar()
        self.aws_secret_access_key_val = ctk.StringVar()
        self.aws_server_options = ["eu-central-1", "eu-west-1", "eu-west-2", "eu-south-1", "eu-west-3", "eu-south-2",
                                   "eu-north-1", "eu-central-2", "us-east-2", "us-east-1", "us-west-1", "us-west-2",
                                   "af-south-1", "ap-east-1", "ap-south-2", "ap-southeast-3", "ap-southeast-4",
                                   "ap-south-1", "ap-northeast-3", "ap-northeast-2", "ap-southeast-1", "ap-southeast-2",
                                   "ap-northeast-1", "ca-central-1", "ca-west-1", "il-central-1", "me-south-1",
                                   "me-central-1", "sa-east-1", "us-gov-east-1", "us-gov-west-1"]

        self.license_code = ctk.StringVar()

        self.selected_aws_server = ctk.StringVar(value=self.aws_server_options[0])

        # Load saved values or set defaults
        try:
            self.load_saved_values()
        except:
            print()

        self.create_widgets()

    def create_widgets(self):
        # Labels
        ctk.CTkLabel(self.master, text="Select PDF File:").grid(row=0, column=0, sticky="w", pady=10, padx=10)
        ctk.CTkLabel(self.master, text="Select MP3 File:").grid(row=1, column=0, sticky="w", pady=10, padx=10)

        ctk.CTkLabel(self.master, text="Background Blur (0-100):").grid(row=2, column=0, sticky="w", pady=10, padx=10)
        ctk.CTkLabel(self.master, text="Background Brightness (0-1):").grid(row=3, column=0, sticky="w", pady=10,
                                                                            padx=10)
        ctk.CTkLabel(self.master, text="Fade duration (0-1):").grid(row=4, column=0, sticky="w", pady=10, padx=10)
        ctk.CTkLabel(self.master, text="Main Audio Volume (0-2):").grid(row=5, column=0, sticky="w", pady=10, padx=10)
        ctk.CTkLabel(self.master, text="Background Audio Volume (0-2):").grid(row=6, column=0, sticky="w", pady=10,
                                                                              padx=10)

        ctk.CTkLabel(self.master, text="AWS Access Key ID:").grid(row=7, column=0, sticky="w", pady=10, padx=10)
        ctk.CTkLabel(self.master, text="AWS Secret access key:").grid(row=8, column=0, sticky="w", pady=10, padx=10)
        ctk.CTkLabel(self.master, text="AWS Server:").grid(row=9, column=0, sticky="w", pady=10, padx=10)

        ctk.CTkLabel(self.master, text="License Code:").grid(row=10, column=0, sticky="w", pady=10, padx=10)

        # File Selectors
        self.pdf_button = ctk.CTkButton(self.master, text="Select PDF", command=self.select_pdf)
        self.pdf_button.grid(row=0, column=1, sticky="w", pady=10, padx=10)
        self.mp3_button = ctk.CTkButton(self.master, text="Select MP3", command=self.select_mp3)
        self.mp3_button.grid(row=1, column=1, sticky="w", pady=10, padx=10)

        # Sliders
        ctk.CTkSlider(self.master, variable=self.blur_val, from_=0, to=100, orientation=ctk.HORIZONTAL,
                      command=self.update_blur_label).grid(row=2, column=1, sticky="we", pady=10, padx=10)
        ctk.CTkSlider(self.master, variable=self.brightness_val, from_=0, to=1, orientation=ctk.HORIZONTAL,
                      command=self.update_brightness_label).grid(row=3, column=1, sticky="we", pady=10, padx=10)

        ctk.CTkSlider(self.master, variable=self.fade_duration_val, from_=0, to=1, orientation=ctk.HORIZONTAL,
                      command=self.update_fade_duration_lable).grid(row=4, column=1, sticky="we", pady=10, padx=10)

        ctk.CTkSlider(self.master, variable=self.main_audio_volume_val, from_=0, to=2, orientation=ctk.HORIZONTAL,
                      command=self.update_main_audio_volume_label).grid(row=5, column=1, sticky="we", pady=10, padx=10)
        ctk.CTkSlider(self.master, variable=self.bg_audio_volume_val, from_=0, to=2, orientation=ctk.HORIZONTAL,
                      command=self.update_bg_audio_volume_label).grid(row=6, column=1, sticky="we", pady=10, padx=10)

        # Text Inputs
        ctk.CTkEntry(self.master, textvariable=self.aws_access_key_val).grid(row=7, column=1, sticky="we", pady=10,
                                                                             padx=10)
        ctk.CTkEntry(self.master, textvariable=self.aws_secret_access_key_val).grid(row=8, column=1, sticky="we",
                                                                                    pady=10, padx=10)

        # Dropdown Menu
        (ctk.CTkOptionMenu(self.master, values=self.aws_server_options, variable=self.selected_aws_server).grid(row=9,
                                                                                                                column=1,
                                                                                                                sticky="we",
                                                                                                                pady=10,
                                                                                                                padx=10))

        ctk.CTkEntry(self.master, textvariable=self.license_code).grid(row=10, column=1, sticky="we",
                                                                                    pady=10, padx=10)

        # Generate Video Button
        default_button = ctk.CTkButton(self.master, text="Reset Values", command=self.load_default_values)
        default_button.grid(row=11, column=0, pady=10, padx=10)

        # Generate Video Button
        generate_button = ctk.CTkButton(self.master, text="Generate Video", command=self.generate_video)
        generate_button.grid(row=11, column=1, pady=10, padx=10)

        # Labels to display selected values
        self.pdf_label = ctk.CTkLabel(self.master, text="")
        self.pdf_label.grid(row=0, column=2, sticky="w", pady=10, padx=10)
        self.mp3_label = ctk.CTkLabel(self.master, text="")
        self.mp3_label.grid(row=1, column=2, sticky="w", pady=10, padx=10)

        self.pdf_label.configure(text=self.pdf_file.split('/')[-1])
        self.mp3_label.configure(text=self.mp3_file.split('/')[-1])

        self.blur_label = ctk.CTkLabel(self.master, text=str(self.blur_val.get()))
        self.blur_label.grid(row=2, column=2, sticky="w", pady=10, padx=10)
        self.brightness_label = ctk.CTkLabel(self.master, text="{:.2f}".format(self.brightness_val.get()))
        self.brightness_label.grid(row=3, column=2, sticky="w", pady=10, padx=10)

        self.fade_duration_lable = ctk.CTkLabel(self.master, text="{:.2f}".format(self.fade_duration_val.get()))
        self.fade_duration_lable.grid(row=4, column=2, sticky="w", pady=10, padx=10)

        self.main_audio_volume_label = ctk.CTkLabel(self.master, text="{:.2f}".format(self.main_audio_volume_val.get()))
        self.main_audio_volume_label.grid(row=5, column=2, sticky="w", pady=10, padx=10)
        self.bg_audio_volume_label = ctk.CTkLabel(self.master, text="{:.2f}".format(self.bg_audio_volume_val.get()))
        self.bg_audio_volume_label.grid(row=6, column=2, sticky="w", pady=10, padx=10)

    def load_saved_values(self):
        try:
            with open("config.json", "r") as f:
                data = json.load(f)
                self.pdf_file = data.get("pdf_file", "")
                self.mp3_file = data.get("mp3_file", "")
                self.blur_val.set(data.get("blur_val", 8))
                self.brightness_val.set(data.get("brightness_val", 0.5))
                self.fade_duration_val.set(data.get("fade_duration_val", 0.5))
                self.main_audio_volume_val.set(data.get("main_audio_volume_val", 1.7))
                self.bg_audio_volume_val.set(data.get("bg_audio_volume_val", 0.04))
                self.aws_access_key_val.set(data.get("aws_access_key_val", ""))
                self.aws_secret_access_key_val.set(data.get("aws_secret_access_key_val", ""))
                self.selected_aws_server.set(data.get("selected_aws_server", self.aws_server_options[0]))
        except FileNotFoundError:
            pass

    def load_default_values(self):
        try:
            with open("default-config.json", "r") as f:
                data = json.load(f)
                self.blur_val.set(data.get("blur_val", 8))
                self.brightness_val.set(data.get("brightness_val", 0.5))
                self.fade_duration_val.set(data.get("fade_duration_val", 0.5))
                self.main_audio_volume_val.set(data.get("main_audio_volume_val", 1.7))
                self.bg_audio_volume_val.set(data.get("bg_audio_volume_val", 0.04))
                self.blur_label.configure(text=str(self.blur_val.get()))
                self.brightness_label.configure(text="{:.2f}".format(self.brightness_val.get()))
                self.fade_duration_lable.configure(text="{:.2f}".format(self.fade_duration_val.get()))
                self.main_audio_volume_label.configure(text="{:.2f}".format(self.main_audio_volume_val.get()))
                self.bg_audio_volume_label.configure(text="{:.2f}".format(self.bg_audio_volume_val.get()))
        except FileNotFoundError:
            pass

    def save_current_values(self):
        data = {"pdf_file": self.pdf_file, "mp3_file": self.mp3_file, "blur_val": self.blur_val.get(),
                "brightness_val": self.brightness_val.get(), "fade_duration_val": self.fade_duration_val.get(),
                "main_audio_volume_val": self.main_audio_volume_val.get(),
                "bg_audio_volume_val": self.bg_audio_volume_val.get(),
                "aws_access_key_val": self.aws_access_key_val.get(),
                "aws_secret_access_key_val": self.aws_secret_access_key_val.get(),
                "selected_aws_server": self.selected_aws_server.get()}
        with open("config.json", "w") as f:
            json.dump(data, f)

    def update_blur_label(self, event):
        self.blur_label.configure(text=str(self.blur_val.get()))

    def update_brightness_label(self, event):
        self.brightness_label.configure(text="{:.2f}".format(self.brightness_val.get()))

    def update_fade_duration_lable(self, event):
        self.fade_duration_lable.configure(text="{:.2f}".format(self.fade_duration_val.get()))

    def update_main_audio_volume_label(self, event):
        self.main_audio_volume_label.configure(text="{:.2f}".format(self.main_audio_volume_val.get()))

    def update_bg_audio_volume_label(self, event):
        self.bg_audio_volume_label.configure(text="{:.2f}".format(self.bg_audio_volume_val.get()))

    def select_pdf(self):
        self.pdf_file = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        self.pdf_label.configure(text=self.pdf_file.split('/')[-1])

    def select_mp3(self):
        self.mp3_file = filedialog.askopenfilename(filetypes=[("MP3 Files", "*.mp3")])
        self.mp3_label.configure(text=self.mp3_file.split('/')[-1])

    def wrong_license_code_popup(self):
        popup = ctk.CTkToplevel(self.master)
        popup.title("Incorrect License")
        popup.geometry("200x100")
        popup.grab_set()

        label = ctk.CTkLabel(popup, text="The license code used is incorrect.")
        label.pack(pady=10)

        button = ctk.CTkButton(popup, text="Close", command=popup.destroy)
        button.pack()

    def generate_video(self):

        if "wKiL7DP7uc8x944gEFHpokM52hKWatSw45ZF7hT7GvxuTVu4ryvNvaTwnwKDs4zustGBNcJ2GoB7mw7G" == self.license_code.get():

            # Access selected values
            pdf_file = self.pdf_file
            mp3_file = self.mp3_file
            blur_val = self.blur_val.get()
            brightness_val = self.brightness_val.get()
            fade_duration_val = self.fade_duration_val.get()
            main_volume_val = self.main_audio_volume_val.get()
            bg_volume_val = self.bg_audio_volume_val.get()
            aws_access_key = self.aws_access_key_val.get()
            aws_secret_access_key = self.aws_secret_access_key_val.get()
            aws_server = self.selected_aws_server.get()

            # Call generate video function with selected values
            print("Generating video...")
            print("PDF File:", pdf_file)
            print("MP3 File:", mp3_file)
            print("Blur Value:", blur_val)
            print("Brightness Value:", brightness_val)
            print("Fade Duration:", fade_duration_val)
            print("Main Audio Volume:", main_volume_val)
            print("Background Audio Volume:", bg_volume_val)
            print("AWS Access key:", aws_access_key)
            print("AWS Secret Access_key:", aws_secret_access_key)
            print("AWS Server:", aws_server)

            make_video_pdf_engine.make_pdf_video(pdf_file, mp3_file, blur_val, brightness_val, fade_duration_val,
                                                 main_volume_val, bg_volume_val, aws_access_key, aws_secret_access_key,
                                                 aws_server)
        else:
            self.wrong_license_code_popup()


def main():
    root = ctk.CTk()
    app = CustomTkinterApp(root)

    def on_closing():
        app.save_current_values()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
