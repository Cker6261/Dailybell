import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import datetime, timedelta
import threading
import json
from plyer import notification
import pygame
import os

# Initialize pygame mixer for sound notifications
pygame.mixer.init()

# Check files exist for sound and icon
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SOUND_FILE = os.path.join(BASE_DIR, "alarm.mp3")
ICON_FILE = os.path.join(BASE_DIR, "bell.ico")
if not os.path.isfile(SOUND_FILE):
    print(f"Warning: Sound file '{SOUND_FILE}' not found. Sound will not play.")
if not os.path.isfile(ICON_FILE):
    print(f"Warning: Icon file '{ICON_FILE}' not found. Window icon will not be set.")

# List to store reminders
reminders = []

# Load existing reminders from file
def load_reminders():
    try:
        with open("reminders.json", "r") as f:
            data = json.load(f)
            for r in data:
                reminders.append({
                    "desc": r["desc"],
                    "datetime": datetime.strptime(r["datetime"], "%Y-%m-%d %H:%M"),
                    "repeat": r["repeat"]
                })
    except FileNotFoundError:
        pass

# Save reminders to file
def save_reminders():
    with open("reminders.json", "w") as f:
        json.dump([
            {
                "desc": r["desc"],
                "datetime": r["datetime"].strftime("%Y-%m-%d %H:%M"),
                "repeat": r["repeat"]
            } for r in reminders
        ], f)

# Setup main window
root = tk.Tk()
root.title("DailyBell - Reminder App")
root.geometry("600x600")
root.configure(bg="#2C3E50")  # Dark blue-gray background

# Set app icon if available
if os.path.isfile(ICON_FILE):
    root.iconbitmap(ICON_FILE)

# Title
title_label = tk.Label(root, text="Set a Reminder", font=("Segoe UI", 28, "bold"), fg="#ECF0F1", bg="#2C3E50")
title_label.pack(pady=25)

# Frame for input fields with a lighter bg and rounded edges using padding
input_frame = tk.Frame(root, bg="#34495E", bd=0, relief="ridge")
input_frame.pack(pady=15, padx=20, fill="x")

# Label styling helper
def styled_label(master, text):
    return tk.Label(master, text=text, font=("Segoe UI", 13), fg="#ECF0F1", bg="#34495E")

# Description
styled_label(input_frame, "Reminder Description:").grid(row=0, column=0, sticky="w", pady=8, padx=10)
desc_entry = tk.Entry(input_frame, width=40, font=("Segoe UI", 13))
desc_entry.grid(row=1, column=0, columnspan=2, pady=8, padx=10)

# Date
styled_label(input_frame, "Select Date:").grid(row=2, column=0, sticky="w", pady=8, padx=10)
date_entry = DateEntry(input_frame, width=18, font=("Segoe UI", 13), background="#2980B9", foreground="white", borderwidth=2)
date_entry.grid(row=3, column=0, pady=8, padx=10, sticky="w")

# Time
styled_label(input_frame, "Time (24hr):").grid(row=2, column=1, sticky="w", pady=8, padx=10)
time_frame = tk.Frame(input_frame, bg="#34495E")
time_frame.grid(row=3, column=1, sticky="w", pady=8, padx=10)

hour_box = ttk.Combobox(time_frame, values=[f"{i:02}" for i in range(24)], width=5, font=("Segoe UI", 13))
hour_box.set("12")
hour_box.pack(side="left", padx=5)

min_box = ttk.Combobox(time_frame, values=[f"{i:02}" for i in range(60)], width=5, font=("Segoe UI", 13))
min_box.set("00")
min_box.pack(side="left", padx=5)

# Repeat options
styled_label(input_frame, "Repeat Reminder:").grid(row=4, column=0, sticky="w", pady=8, padx=10)
repeat_box = ttk.Combobox(input_frame, values=["None", "Daily", "Weekly"], state="readonly", width=18, font=("Segoe UI", 13))
repeat_box.set("None")
repeat_box.grid(row=5, column=0, pady=8, padx=10, sticky="w")

# Button styles (using ttk.Style)
style = ttk.Style()
style.theme_use('default')
style.configure('TButton', font=("Segoe UI", 14, "bold"), foreground="#ffffff", background="#2980B9", padding=10)
style.map('TButton',
          foreground=[('active', '#ffffff')],
          background=[('active', '#3498DB')])

# Set reminder function
def set_reminder():
    desc = desc_entry.get().strip()
    if not desc:
        messagebox.showwarning("Input Error", "Please enter a reminder description.")
        return

    date = date_entry.get_date()
    hour = hour_box.get()
    minute = min_box.get()
    repeat = repeat_box.get()

    try:
        reminder_datetime = datetime.combine(date, datetime.strptime(f"{hour}:{minute}", "%H:%M").time())
        if reminder_datetime < datetime.now():
            messagebox.showwarning("Input Error", "Please select a future date and time.")
            return

        reminder = {
            "desc": desc,
            "datetime": reminder_datetime,
            "repeat": repeat
        }
        reminders.append(reminder)
        save_reminders()
        messagebox.showinfo("Success", "Reminder set successfully!")

        # Clear inputs after setting reminder
        desc_entry.delete(0, tk.END)
        repeat_box.set("None")
        hour_box.set("12")
        min_box.set("00")
        date_entry.set_date(datetime.now())
    except Exception as e:
        messagebox.showerror("Error", str(e))

# Show reminders in new window
def show_reminders():
    view_win = tk.Toplevel(root)
    view_win.title("Your Reminders")
    view_win.geometry("540x360")
    view_win.configure(bg="#34495E")

    columns = ("Description", "Date & Time", "Repeat")
    tree = ttk.Treeview(view_win, columns=columns, show="headings", height=12)
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=160, anchor="center")
    tree.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

    btn_frame = tk.Frame(view_win, bg="#34495E")
    btn_frame.pack(pady=10)

    edit_btn = ttk.Button(btn_frame, text="Edit", command=lambda: edit_reminder(tree, view_win))
    edit_btn.pack(side="left", padx=15)

    delete_btn = ttk.Button(btn_frame, text="Delete", command=lambda: delete_reminder(tree))
    delete_btn.pack(side="left", padx=15)

    for rem in reminders:
        tree.insert("", tk.END, values=(rem["desc"], rem["datetime"].strftime("%Y-%m-%d %H:%M"), rem["repeat"]))

# Delete reminder
def delete_reminder(tree):
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("No selection", "Please select a reminder to delete.")
        return

    item = tree.item(selected[0])
    values = item["values"]

    for rem in reminders:
        if rem["desc"] == values[0] and rem["datetime"].strftime("%Y-%m-%d %H:%M") == values[1]:
            reminders.remove(rem)
            break
    save_reminders()
    tree.delete(selected[0])

# Edit reminder
def edit_reminder(tree, top):
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("No selection", "Please select a reminder to edit.")
        return

    values = tree.item(selected[0])["values"]

    for index, rem in enumerate(reminders):
        if rem["desc"] == values[0] and rem["datetime"].strftime("%Y-%m-%d %H:%M") == values[1]:
            reminder = reminders[index]
            break

    edit_win = tk.Toplevel(root)
    edit_win.title("Edit Reminder")
    edit_win.geometry("340x340")
    edit_win.configure(bg="#34495E")

    tk.Label(edit_win, text="Description", font=("Segoe UI", 13), fg="#ECF0F1", bg="#34495E").pack(pady=8)
    new_desc = tk.Entry(edit_win, font=("Segoe UI", 13))
    new_desc.insert(0, reminder["desc"])
    new_desc.pack(pady=5)

    tk.Label(edit_win, text="Date", font=("Segoe UI", 13), fg="#ECF0F1", bg="#34495E").pack(pady=8)
    new_date = DateEntry(edit_win, font=("Segoe UI", 13), background="#2980B9", foreground="white", borderwidth=2)
    new_date.set_date(reminder["datetime"].date())
    new_date.pack(pady=5)

    tk.Label(edit_win, text="Time (HH:MM)", font=("Segoe UI", 13), fg="#ECF0F1", bg="#34495E").pack(pady=8)
    time_frame = tk.Frame(edit_win, bg="#34495E")
    time_frame.pack(pady=5)

    hour_var = tk.StringVar(value=f"{reminder['datetime'].hour:02}")
    min_var = tk.StringVar(value=f"{reminder['datetime'].minute:02}")

    hour_entry = ttk.Combobox(time_frame, textvariable=hour_var, width=5, values=[f"{i:02}" for i in range(24)], font=("Segoe UI", 13))
    hour_entry.pack(side="left", padx=6)

    min_entry = ttk.Combobox(time_frame, textvariable=min_var, width=5, values=[f"{i:02}" for i in range(60)], font=("Segoe UI", 13))
    min_entry.pack(side="left", padx=6)

    tk.Label(edit_win, text="Repeat", font=("Segoe UI", 13), fg="#ECF0F1", bg="#34495E").pack(pady=8)
    repeat_var = tk.StringVar()
    repeat_entry = ttk.Combobox(edit_win, textvariable=repeat_var, values=["None", "Daily", "Weekly"], state="readonly", font=("Segoe UI", 13))
    repeat_entry.set(reminder["repeat"])
    repeat_entry.pack(pady=5)

    def save_edited():
        new_desc_val = new_desc.get().strip()
        if not new_desc_val:
            messagebox.showwarning("Input Error", "Description cannot be empty.")
            return

        new_datetime = datetime.combine(new_date.get_date(), datetime.strptime(f"{hour_var.get()}:{min_var.get()}", "%H:%M").time())
        if new_datetime < datetime.now():
            messagebox.showwarning("Input Error", "Please select a future date and time.")
            return

        reminder["desc"] = new_desc_val
        reminder["datetime"] = new_datetime
        reminder["repeat"] = repeat_var.get()
        save_reminders()
        edit_win.destroy()
        top.destroy()
        show_reminders()

    ttk.Button(edit_win, text="Save Changes", command=save_edited).pack(pady=15)

# Periodic reminder check
def check_reminders():
    global reminders
    now = datetime.now()
    remaining = []

    for reminder in reminders[:]:
        if now >= reminder["datetime"]:
            notification.notify(
                title="Reminder",
                message=reminder["desc"],
                timeout=10
            )
            try:
                if os.path.isfile(SOUND_FILE):
                    pygame.mixer.music.load(SOUND_FILE)
                    pygame.mixer.music.play()
            except Exception as e:
                print(f"Sound playback error: {e}")

            if reminder["repeat"] == "Daily":
                reminder["datetime"] += timedelta(days=1)
                remaining.append(reminder)
            elif reminder["repeat"] == "Weekly":
                reminder["datetime"] += timedelta(weeks=1)
                remaining.append(reminder)
        else:
            remaining.append(reminder)

    reminders[:] = remaining
    save_reminders()
    threading.Timer(60, check_reminders).start()

# Load old reminders and start checking
load_reminders()
check_reminders()

# Buttons frame for main window with padding and bg color
btn_frame = tk.Frame(root, bg="#2C3E50")
btn_frame.pack(pady=25)

set_btn = ttk.Button(btn_frame, text="Set Reminder", command=set_reminder)
set_btn.pack(side="left", padx=15)

show_btn = ttk.Button(btn_frame, text="Show Reminders", command=show_reminders)
show_btn.pack(side="left", padx=15)

root.mainloop()
