import tkinter as tk
from PIL import Image, ImageTk, ImageSequence
import pygame
import os
import sys
import pystray
import threading
import json

NUM_CUPS = 10
NUM_LEVELS = (NUM_CUPS // 2) + 1
BUTTON_WIDTH, BUTTON_HEIGHT = 180, 80
RESET_WIDTH, RESET_HEIGHT = 140, 50

count = 0
coins = 0
pet_count = 0
owned_items = set()   # Start with no cosmetics
active_cosmetic = None  # Start with no active cosmetic
purchase_state = {}

SAVE_FILE = "cosmetic_state.json"

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, "assets", relative_path)

def save_cosmetic_choice():
    with open(SAVE_FILE, "w") as f:
        json.dump({"active_cosmetic": active_cosmetic}, f)

def load_cosmetic_choice():
    global active_cosmetic
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            data = json.load(f)
            active_cosmetic = data.get("active_cosmetic")
load_cosmetic_choice()

pygame.mixer.init()
click_sound = pygame.mixer.Sound(resource_path("click.wav"))
remind_sound = pygame.mixer.Sound(resource_path("remind.wav"))
happy_sound = pygame.mixer.Sound(resource_path("happy.wav"))
bubble_sound = pygame.mixer.Sound(resource_path("bubble.wav"))
for sound in [click_sound, remind_sound, happy_sound, bubble_sound]:
    sound.set_volume(0.3)

root = tk.Tk()
root.title("Drink Water with Kitty!")
root.geometry("400x650") 
root.configure(bg="#f0f8ff")
root.iconbitmap(resource_path("pawicon.ico"))

# Tray icon handling
icon = None
def quit_app(icon, item): icon.stop(); root.after(0, root.destroy)
def show_window(icon, item): root.after(0, root.deiconify)
def hide_window(): root.withdraw()
def setup_tray():
    global icon
    image = Image.open(resource_path("pawicon.ico"))
    menu = pystray.Menu(
        pystray.MenuItem("Show", show_window),
        pystray.MenuItem("Quit", quit_app)
    )
    icon = pystray.Icon("kitty_reminder", image, "Drink Water with Kitty!", menu)
    icon.run()
def on_close():
    hide_window()
    threading.Thread(target=setup_tray, daemon=True).start()
root.protocol("WM_DELETE_WINDOW", on_close)

# UI Labels and layout
coin_icon = ImageTk.PhotoImage(Image.open(resource_path("coin.png")).resize((30, 30)))
coin_frame = tk.Frame(root, bg="#f0f8ff")
coin_frame.place(x=280, y=10)
coin_label = tk.Label(coin_frame, text="0", font=("Helvetica", 14), bg="#f0f8ff")
coin_icon_label = tk.Label(coin_frame, image=coin_icon, bg="#f0f8ff")
coin_icon_label.pack(side=tk.LEFT, padx=5)
coin_label.pack(side=tk.LEFT)

menu_img = ImageTk.PhotoImage(Image.open(resource_path("menu.png")).resize((40, 40)))
menu_btn = tk.Button(root, image=menu_img, bg="#f0f8ff", borderwidth=0, command=lambda: open_menu())
menu_btn.place(x=10, y=10)

def update_coin_display():
    coin_label.config(text=str(coins))

# Cat animation
cat_label = tk.Label(root, bg="#f0f8ff", cursor="arrow")
cat_label.pack(pady=(70, 20)) 
cat_images = []
def load_cat_images():
    global cat_images
    cat_images = []
    cosmetic_prefix = active_cosmetic + "_" if active_cosmetic else ""
    for i in range(1, NUM_LEVELS + 1):
        gif_path = resource_path(f"{cosmetic_prefix}cat{i}.gif")
        gif = Image.open(gif_path)
        frames = [ImageTk.PhotoImage(frame.copy().convert("RGBA")) for frame in ImageSequence.Iterator(gif)]
        cat_images.append(frames)

cat_animation_frames = []
cat_animation_index = 0
def animate_cat():
    global cat_animation_index
    if not cat_animation_frames:
        return
    frame = cat_animation_frames[cat_animation_index]
    cat_label.config(image=frame)
    cat_label.image = frame
    cat_animation_index = (cat_animation_index + 1) % len(cat_animation_frames)
    root.after(120, animate_cat)

def update_cat_image():
    global cat_animation_frames, cat_animation_index
    if count == 0: level = 0
    else: level = ((count - 1) // 2) + 1
    level = min(level, NUM_LEVELS - 1)
    cat_animation_frames = cat_images[level]
    cat_animation_index = 0

progress_label = tk.Label(root, text="You have drunk 0 cups today", font=("Helvetica", 14), bg="#f0f8ff")
progress_label.pack(pady=10)

def update_progress():
    progress_label.config(text=f"You have drunk {count} cup{'s' if count != 1 else ''} today")
    update_cat_image()

def show_custom_popup(title, message):
    popup = tk.Toplevel(root)
    popup.title(title)
    popup.configure(bg="#f0f8ff")
    popup.transient(root)
    popup.grab_set()
    popup.geometry("320x180")

    label = tk.Label(popup, text=message, font=("Helvetica", 14), bg="#f0f8ff")
    label.pack(pady=20)

    try:
        ok_img_path = resource_path("ok.png")
        ok_img = Image.open(ok_img_path).resize((100, 40))
        ok_img_tk = ImageTk.PhotoImage(ok_img)
        ok_button = tk.Button(popup, image=ok_img_tk, borderwidth=0, bg="#f0f8ff",
                              activebackground="#f0f8ff", command=popup.destroy)
        ok_button.image = ok_img_tk
    except:
        ok_button = tk.Button(popup, text="OK", font=("Helvetica", 12), command=popup.destroy)
    ok_button.pack(pady=10)
    popup.wait_window()

def drink_water():
    global count, coins
    if count < NUM_CUPS:
        count += 1
        update_progress()
        if count == NUM_CUPS:
            coins += 1
            update_coin_display()
            show_custom_popup("Great job!", "You reached your goal! You earned 1 coin!")
    else:
        show_custom_popup("Already Done!", "You already reached your daily goal.")

def reset_day():
    global count
    count = 0
    update_progress()
    show_custom_popup("Reset", "Daily tracker reset!")

def on_button_click(event): drink_water(); bubble_sound.play()
def on_reset_click(event): reset_day(); bubble_sound.play()

# Drink button
button_img = ImageTk.PhotoImage(Image.open(resource_path("button.png")).resize((BUTTON_WIDTH, BUTTON_HEIGHT)))
drink_canvas = tk.Canvas(root, width=BUTTON_WIDTH, height=BUTTON_HEIGHT, bg="#f0f8ff", highlightthickness=0)
drink_canvas.pack(pady=20)
button_image_id = drink_canvas.create_image(BUTTON_WIDTH//2, BUTTON_HEIGHT//2, image=button_img)
drink_canvas.bind("<Button-1>", on_button_click)

# Reset button
reset_img = ImageTk.PhotoImage(Image.open(resource_path("resetday.png")).resize((RESET_WIDTH, RESET_HEIGHT)))
reset_canvas = tk.Canvas(root, width=RESET_WIDTH, height=RESET_HEIGHT, bg="#f0f8ff", highlightthickness=0)
reset_canvas.pack(pady=10)
reset_image_id = reset_canvas.create_image(RESET_WIDTH//2, RESET_HEIGHT//2, image=reset_img)
reset_canvas.bind("<Button-1>", on_reset_click)

def on_cat_enter(event): cat_label.config(cursor="hand2")
def on_cat_leave(event): cat_label.config(cursor="arrow")
def cat_clicked(event):
    global pet_count
    pet_count += 1
    (click_sound if pet_count <= 15 else happy_sound).play()
cat_label.bind("<Enter>", on_cat_enter)
cat_label.bind("<Leave>", on_cat_leave)
cat_label.bind("<Button-1>", cat_clicked)

# Reminder
reminder_popup = None
def show_reminder_popup():
    global reminder_popup
    if reminder_popup is not None: return
    reminder_popup = tk.Toplevel(root)
    reminder_popup.overrideredirect(True)
    reminder_popup.attributes("-topmost", True)
    transparent_color = "#ff00ff"
    reminder_popup.configure(bg=transparent_color)
    reminder_popup.wm_attributes('-transparentcolor', transparent_color)

    remind_img = ImageTk.PhotoImage(Image.open(resource_path("remindcat.png")))
    reminder_label = tk.Label(reminder_popup, image=remind_img, borderwidth=0, bg=transparent_color)
    reminder_label.image = remind_img
    reminder_label.pack()
    reminder_popup.update_idletasks()
    x = reminder_popup.winfo_screenwidth() - reminder_popup.winfo_width() - 20
    y = reminder_popup.winfo_screenheight() - reminder_popup.winfo_height() - 50
    reminder_popup.geometry(f"+{x}+{y}")
    def on_reminder_click(event):
        global count, reminder_popup
        if count < NUM_CUPS:
            count += 1
            update_progress()
        click_sound.play()
        reminder_popup.destroy()
        reminder_popup = None
    reminder_label.bind("<Button-1>", on_reminder_click)

def reminder_task():
    remind_sound.play()
    show_reminder_popup()
    root.after(3600000, reminder_task)  # 1 minute for testing 60000

# Menu & Cosmetics
def open_menu():
    menu_win = tk.Toplevel(root)
    menu_win.title("Menu")
    menu_win.configure(bg="#f0f8ff")
    menu_win.geometry("300x250")
    menu_win.transient(root)
    menu_win.grab_set()

    cosmetics_img = ImageTk.PhotoImage(Image.open(resource_path("cosmetics.png")).resize((140, 50)))
    shop_img = ImageTk.PhotoImage(Image.open(resource_path("shop.png")).resize((140, 50)))

    tk.Button(menu_win, image=cosmetics_img, command=open_cosmetics, borderwidth=0,
              bg="#f0f8ff", activebackground="#f0f8ff").pack(pady=10)
    tk.Button(menu_win, image=shop_img, command=open_shop, borderwidth=0,
              bg="#f0f8ff", activebackground="#f0f8ff").pack(pady=10)

    menu_win.mainloop()

def open_cosmetics():
    cosmetics_win = tk.Toplevel(root)
    cosmetics_win.title("Cosmetics")
    cosmetics_win.configure(bg="#f0f8ff")
    cosmetics_win.geometry("300x250")
    cosmetics_win.transient(root)
    cosmetics_win.grab_set()

    if "tiara" in owned_items:
        img = Image.open(resource_path("tiara.png")).resize((80, 80))
        img_tk = ImageTk.PhotoImage(img)
        btn = tk.Button(cosmetics_win, image=img_tk, bg="#f0f8ff", borderwidth=0,
                        command=lambda: apply_cosmetic("tiara"))
        btn.image = img_tk
        btn.pack(pady=10)

# OFF button
    off_img = Image.open(resource_path("off.png")).resize((80, 80))
    off_img_tk = ImageTk.PhotoImage(off_img)
    off_btn = tk.Button(cosmetics_win, image=off_img_tk, bg="#f0f8ff", borderwidth=0,
                        command=lambda: apply_cosmetic(None))
    off_btn.image = off_img_tk
    off_btn.pack(pady=10)

def open_shop():
    shop_win = tk.Toplevel(root)
    shop_win.title("Shop")
    shop_win.configure(bg="#f0f8ff")
    shop_win.geometry("300x200")
    shop_win.transient(root)
    shop_win.grab_set()

    def buy_item(item):
        global coins
        if item in owned_items:
            show_custom_popup("Owned", f"You already own {item}!")
            return
        if purchase_state.get(item, 0) == 0:
            purchase_state[item] = 1
            show_custom_popup("Confirm", f"Click again to confirm purchase of {item} for 10 coins.")
            return
        if coins >= 10:
            coins -= 10
            owned_items.add(item)
            update_coin_display()
            show_custom_popup("Yay!", f"You bought {item}!")
        else:
            show_custom_popup("Oops!", "Not enough coins!")

    item = "tiara"
    img = Image.open(resource_path(f"{item}.png")).resize((80, 80))
    img_tk = ImageTk.PhotoImage(img)
    btn = tk.Button(shop_win, image=img_tk, bg="#f0f8ff", borderwidth=0,
                    command=lambda: buy_item(item))
    btn.image = img_tk
    btn.pack(pady=20)

def apply_cosmetic(item):
    global active_cosmetic
    active_cosmetic = item
    save_cosmetic_choice()
    load_cat_images()
    update_cat_image()

# Final setup
load_cat_images()
update_cat_image()
animate_cat()
root.after(3600000, reminder_task)
root.mainloop()

# Next time notes: 
# - Fix buttons to have more SHLABANG (or well blup) effect
# - Add more cosmetics (duck, cool shades etc.)
# - Fix when buying cosmetics without enough coins to say "not enough coins" right away instead of after asking if you wanna buy it for 10 coins
# - Figure out "Lucky wheel" mechanics?
# - Happy song to not be spam:able? Also add a cool confetti effect yippee shenanigans
# - Change popup from window to in-app 
# - Make coin stay in top right regardless of window size 
# - Decals for cosmetics? maybe..
# - Fix reminder timer to set if "Drink!" is pressed before 1h mark