import subprocess
import tkinter as tk
from tkinter import ttk, filedialog
import sys
import os
import qrcode
from PIL import ImageTk, Image
from tkcolorpicker import askcolor  # Import the color picker

# Unicode support
subprocess.run('CHCP 65001', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def toggle_password_visibility():
    password_column = tree.heading("#3")
    if hide_password_var.get():
        tree.column("#4", width=0, stretch=tk.NO)
        password_column["text"] = ""  # Clear the column header text
    else:
        tree.column("#4", width=100, stretch=tk.YES)
        password_column["text"] = "Password"  # Restore the column header text


def generate_qr_code():
    global qr
    selected_item = tree.selection()
    if selected_item and len(selected_item) > 0:
        profile_name = tree.item(selected_item[0])["values"][1]
        try:
            index = profiles.index(profile_name)
            ssid = profiles[index]
            password = passwords[index]
            security_type = security_types[index]
            if security_type == "WPA2-Personal":
                security_type = "WPA"

            wifi_config = f"WIFI:T:{security_type};S:{ssid};P:{password};;"

            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(wifi_config)
            qr.make(fit=True)  # Automatically fit to the window size
            qr.foreground = foreground_color  # Set the foreground color
            qr.background = background_color  # Set the background color
            qr_img = qr.make_image(fill_color=qr.foreground, back_color=qr.background)
            qr_img = ImageTk.PhotoImage(qr_img)

            qr_label.config(image=qr_img)
            qr_label.image = qr_img

            # Show the "Save" button and pixel size box
            save_button.pack(side="top", pady=10)
            pixel_frame.pack(side="top")
            pixel_label.pack(side="left")
            pixel_entry.pack(side="left")
            x_label.pack(side="left")
            saved_label.pack_forget()
        except ValueError:
            pass
    else:
        qr_label.config(image=None)


def save_qr_code():
    global qr
    file_path = filedialog.asksaveasfilename(defaultextension=".png",
                                             filetypes=[("PNG files", "*.png"), ("JPG files", "*.jpg")],
                                             initialfile="export")
    if file_path and qr:
        pixel_size = int(pixel_var.get())
        qr_img = qr.make_image(fill_color=qr.foreground, back_color=qr.background)
        qr_img = qr_img.resize((pixel_size, pixel_size), Image.Resampling.LANCZOS)
        qr_img.save(file_path)
        saved_label.pack()  # Show the "Saved!" message


def change_foreground_color():
    global foreground_color
    color = askcolor(color=foreground_color, title="Foreground Color")
    if color[1] is not None:
        foreground_color = color[1]
        generate_qr_code()
        foreground_color_label.config(text=foreground_color)


def change_background_color():
    global background_color
    color = askcolor(color=background_color, title="Background Color")
    if color[1] is not None:
        background_color = color[1]
        generate_qr_code()
        background_color_label.config(text=background_color)

def get_icon_path():
    # Check if the script is bundled using PyInstaller
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, "icon", "icon.ico")
    else:
        return "icon/icon.ico"  # Relative path to the icon.ico file

window = tk.Tk()
window.title('Wi-Fi Profiles')
window.geometry('800x600')
icon_path = get_icon_path()
window.iconbitmap(default=icon_path)

data = subprocess.check_output('netsh wlan show profiles').decode('utf-8').split('\n')
profiles = [i.split(":")[1][1:-1] for i in data if "All User Profile" in i]
security_types = []
passwords = []

# Check for Wi-Fi Passwords and Security
for i in profiles:
    output = subprocess.check_output(['netsh', 'wlan', 'show', 'profile', i, 'key=clear']).decode('utf-8').split('\n')
    results = [b.split(":")[1][1:-1] for b in output if "Key Content" in b]
    auth = [c.split(":")[1][1:-1] for c in output if "Authentication" in c]
    security_types.append(auth[0])
    if results:
        passwords.append(results[0])
    else:
        passwords.append('<None>')

qr = None
foreground_color = "#000000"  # Default foreground color
background_color = "#FFFFFF"  # Default background color

# Create a PanedWindow with two sides (profile listing and QR code generation)
paned_window = ttk.PanedWindow(window, orient=tk.HORIZONTAL)
paned_window.pack(fill=tk.BOTH, expand=True)

profile_frame = tk.Frame(paned_window)
paned_window.add(profile_frame)

qr_frame = tk.Frame(paned_window)
paned_window.add(qr_frame)

hide_password_var = tk.BooleanVar(value=True)
hide_password_checkbox = ttk.Checkbutton(profile_frame, text="Hide Password", variable=hide_password_var,
                                         command=toggle_password_visibility)
hide_password_checkbox.pack()

# Spreadsheet initialize
tree = ttk.Treeview(profile_frame, columns=("Index", "Name", "Security", "Password"), show="headings")
tree.heading("Index", text="No.")
tree.heading("Name", text="Name")
tree.heading("Security", text="Security")
tree.heading("Password", text="Password")
tree.column("Index", width=40)
tree.column("Name", width=150)
tree.column("Security", width=120)
tree.column("Password", width=130)
# Odd even rows
for i, (profile, security, password) in enumerate(zip(profiles, security_types, passwords), start=1):
    bg_color = "white" if i % 2 == 0 else "lightgray"
    tree.insert("", "end", values=(i, profile, security, password), tags=("gray" if i % 2 == 0 else "white",))
    tree.tag_configure("gray", background="lightgray")
    tree.tag_configure("white", background="white")

# Hide password
toggle_password_visibility()

# Scrollbar
scrollbar_x_profile = ttk.Scrollbar(profile_frame, orient="horizontal", command=tree.xview)
scrollbar_y_profile = ttk.Scrollbar(profile_frame, orient="vertical", command=tree.yview)
tree.configure(xscrollcommand=scrollbar_x_profile.set, yscrollcommand=scrollbar_y_profile.set)

# Pack the Treeview and scrollbars for the profile frame
tree.pack(side="left", fill="both", expand=True)
scrollbar_y_profile.pack(side="right", fill="y")

# Generate button
generate_button = ttk.Button(qr_frame, text="Generate QR Code", command=generate_qr_code)
generate_button.pack()

# QR Label
qr_label = tk.Label(qr_frame)
qr_label.pack()

# Create buttons to change foreground and background colors
color_frame = tk.Frame(qr_frame)
color_frame.pack(side="top")

foreground_color_button = ttk.Button(color_frame, text="Foreground Color", command=change_foreground_color)
background_color_button = ttk.Button(color_frame, text="Background Color", command=change_background_color)
foreground_color_label = tk.Label(color_frame, text=foreground_color)
background_color_label = tk.Label(color_frame, text=background_color)

foreground_color_button.pack(side="left")
foreground_color_label.pack(side="left")
background_color_button.pack(side="left")
background_color_label.pack(side="left")

save_button = ttk.Button(qr_frame, text="Save QR Code", command=save_qr_code)
save_button.pack()
save_button.pack_forget()

# QR Frame
pixel_frame = tk.Frame(qr_frame)
pixel_frame.pack(side="top")
pixel_label = tk.Label(pixel_frame, text="Pixel Size")
pixel_label.pack(side="left")

x_label = tk.Label(pixel_frame)
x_label.pack(side="left")

pixel_var = tk.StringVar(value="200")
pixel_entry = ttk.Entry(pixel_frame, textvariable=pixel_var, width=5)
pixel_entry.pack(side="left")

saved_label = tk.Label(qr_frame, text="Saved!", fg="green")
saved_label.pack()
saved_label.pack_forget()

window.mainloop()
