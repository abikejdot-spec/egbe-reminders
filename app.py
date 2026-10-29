from datetime import datetime
import os
import sqlite3
import threading
import time
from flask import Flask, redirect, render_template_string, request, url_for

# Optional: Try to import winsound for Windows users
try:
  import winsound
except ImportError:
  winsound = None

app = Flask(__name__)

# Initialize SQLite Database with a fresh table name (reminders_v3) to avoid any cache conflicts


def init_db():
  conn = sqlite3.connect("database.db", check_same_thread=False)
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminders_v3 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            timing TEXT NOT NULL,
            message TEXT NOT NULL
        )
    """)
  conn.commit()
  conn.close()


# Function to display alarm with pinned stop button and scrollable message box
def launch_persistent_alarm(name, message):
  try:
    import tkinter as tk
    from tkinter import scrolledtext

    alarm_window = tk.Tk()
    alarm_window.title("🚨 REMINDER ALERT! 🚨")
    alarm_window.attributes("-topmost", True)
    alarm_window.geometry("500x380")
    alarm_window.configure(bg="#1e1e1e")

    tk.Label(
        alarm_window,
        text="🚨 TIME FOR: " + name + " 🚨",
        font=("Arial", 14, "bold"),
        fg="#d4af37",
        bg="#1e1e1e",
    ).pack(pady=15)

    alarm_active = [True]

    def sound_loop():
      if not alarm_active[0]:
        return
      if winsound:
        try:
          winsound.Beep(1500, 500)
        except Exception:
          pass
      alarm_window.after(700, sound_loop)

    def stop_alarm():
      alarm_active[0] = False
      alarm_window.destroy()

    stop_btn = tk.Button(
        alarm_window,
        text="🛑 STOP ALARM",
        bg="#e74c3c",
        fg="white",
        font=("Arial", 14, "bold"),
        command=stop_alarm,
        height=2,
    )
    stop_btn.pack(side="bottom", fill="x", padx=20, pady=20)

    msg_box = scrolledtext.ScrolledText(
        alarm_window,
        wrap=tk.WORD,
        font=("Arial", 11),
        bg="#2d2d2d",
        fg="#ffffff",
        height=6,
    )
    msg_box.pack(fill="both", expand=True, padx=20, pady=5)
    msg_box.insert(tk.INSERT, "Message:\n\n" + message)
    msg_box.config(state=tk.DISABLED)

    alarm_window.protocol("WM_DELETE_WINDOW", stop_alarm)

    sound_loop()
    alarm_window.mainloop()
  except Exception as e:
    print(f"Alarm window error: {e}")


# Background Alarm Engine using reminders_v3
def background_alarm_checker():
  print("🚀 Python Clean Alarm Engine Started...")
  triggered_cache = set()

  while True:
    try:
      now = datetime.now()
      current_date = now.strftime("%Y-%m-%d")
      current_time = now.strftime("%H:%M")

      conn = sqlite3.connect("database.db", check_same_thread=False)
      cursor = conn.cursor()
      cursor.execute(
          "SELECT id, name, date, time, message FROM reminders_v3 WHERE date ="
          " ? AND time = ?",
          (current_date, current_time),
      )
      matches = cursor.fetchall()
      conn.close()

      for reminder in matches:
        r_id, name, r_date, r_time, message = reminder
        unique_key = f"{r_id}_{r_date}_{r_time}"

        if unique_key not in triggered_cache:
          triggered_cache.add(unique_key)
          print(f"\n🚨 TRIGGERING SINGLE ALARM FOR: {name}")

          alarm_ui_thread = threading.Thread(
              target=launch_persistent_alarm, args=(name, message), daemon=True
          )
          alarm_ui_thread.start()

      if len(triggered_cache) > 50:
        triggered_cache.clear()

      time.sleep(10)
    except Exception as e:
      print(f"Alarm engine error: {e}")
      time.sleep(10)


# Single-file HTML layout with Search, Sort, and Clean Form
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Egbe Omo Eko Reminder System</title>
    <style>
        body {
            background-color: #121212;
            color: #e0e0e0;
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 700px;
            margin: 0 auto;
            background: #1e1e1e;
            padding: 30px;
            border-radius: 10px;
            border: 2px solid #d4af37;
        }
        h1 {
            color: #d4af37;
            text-align: center;
            margin-bottom: 25px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            color: #d4af37;
            margin-bottom: 8px;
            font-weight: bold;
        }
        input[type="text"], input[type="date"], input[type="time"], select, textarea {
            width: 100%;
            padding: 12px;
            background: #2d2d2d;
            border: 1px solid #444;
            border-radius: 5px;
            color: #fff;
            box-sizing: border-box;
        }
        textarea {
            resize: vertical;
            height: 100px;
        }
        button {
            background-color: #d4af37;
            color: #121212;
            padding: 12px 20px;
            border: none;
            border-radius: 5px;
            font-weight: bold;
            cursor: pointer;
            width: 100%;
            font-size: 16px;
        }
        button:hover {
            background-color: #f3c653;
        }
        .reminder-list {
            margin-top: 40px;
        }
        .reminder-card {
            background: #2d2d2d;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 15px;
            border-left: 5px solid #d4af37;
        }
        .search-box {
            margin-bottom: 25px;
        }
        .btn-row {
            margin-top: 10px;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        .whatsapp-btn {
            background-color: #25d366;
            color: white;
            padding: 8px 12px;
            border-radius: 4px;
            text-decoration: none;
            font-weight: bold;
            font-size: 14px;
        }
        .edit-btn {
            background-color: #3498db;
            color: white;
            padding: 8px 12px;
            border-radius: 4px;
            text-decoration: none;
            font-weight: bold;
            font-size: 14px;
        }
        .delete-btn {
            background-color: #e74c3c;
            color: white;
            padding: 8px 12px;
            border-radius: 4px;
            text-decoration: none;
            font-weight: bold;
            font-size: 14px;
        }
        .status-badge {
            background: #1a4d2e;
            color: #6fcf97;
            padding: 8px;
            text-align: center;
            border-radius: 5px;
            font-weight: bold;
            margin-bottom: 20px;
            font-size: 13px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Egbe Omo Eko Reminder System</h1>
        
        <div class="status-badge">
            ✅ Clean Form, Search Bar & Date Sorting Active!
        </div>

        <form method="POST" action="{% if edit_reminder %}/edit/{{ edit_reminder[0] }}{% else %}/{% endif %}">
            <h3 style="color: #d4af37; margin-top: 0;">{% if edit_reminder %}Edit Reminder{% else %}Add New Reminder{% endif %}</h3>
            
            <div class="form-group">
                <label>Person's Name:</label>
                <input type="text" name="name" value="{% if edit_reminder %}{{ edit_reminder[1] }}{% endif %}" placeholder="e.g. Alhaji Rauf Abiodun Saba" required>
            </div>
            
            <div class="form-group">
                <label>Birthday Date (YYYY-MM-DD):</label>
                <input type="date" name="date" value="{% if edit_reminder %}{{ edit_reminder[2] }}{% endif %}" required>
            </div>
            
            <div class="form-group">
                <label>Birthday Time:</label>
                <input type="time" name="time" value="{% if edit_reminder %}{{ edit_reminder[3] }}{% endif %}" required>
            </div>
            
            <div class="form-group">
                <label>Alarm & Notification Timing:</label>
                <select name="timing">
                    <option value="Midnight (12:00 AM of birthday)">Midnight (12:00 AM of birthday)</option>
                    <option value="Exact Time">Exact Time</option>
                    <option value="1 Hour Before">1 Hour Before</option>
                </select>
            </div>
            
            <div class="form-group">
                <label>Message Content:</label>
                <textarea name="message" placeholder="Type the message here..." required>{% if edit_reminder %}{{ edit_reminder[5] }}{% endif %}</textarea>
            </div>
            
            <button type="submit">{% if edit_reminder %}Update Reminder{% else %}Save Reminder{% endif %}</button>
            {% if edit_reminder %}
                <a href="/" style="display:block; text-align:center; margin-top:10px; color:#aaa; text-decoration:none;">Cancel Edit</a>
            {% endif %}
        </form>

        <div class="reminder-list">
            <h2 style="color: #d4af37;">Saved Reminders</h2>
            
            <!-- Live Search Bar -->
            <div class="search-box">
                <input type="text" id="searchInput" placeholder="🔍 Search by person's name..." onkeyup="filterReminders()">
            </div>

            <div id="cardsContainer">
                {% for r in reminders %}
                    <div class="reminder-card" data-name="{{ r[1]|lower }}">
                        <h3>{{ r[1] }}</h3>
                        <p><strong>Date:</strong> {{ r[2] }} at {{ r[3] }}</p>
                        <p><strong>Timing:</strong> {{ r[4] }}</p>
                        <p><strong>Message:</strong> {{ r[5] }}</p>
                        
                        <div class="btn-row">
                            <!-- Locked permanently to your WhatsApp number -->
                            <a class="whatsapp-btn" href="https://wa.me/2349122840685?text={{ r[5]|urlencode }}" target="_blank">
                                Open in WhatsApp 📱
                            </a>
                            <a class="edit-btn" href="/edit/{{ r[0] }}">Edit ✏️</a>
                            <a class="delete-btn" href="/delete/{{ r[0] }}" onclick="return confirm('Are you sure you want to delete this reminder?');">Delete 🗑️</a>
                        </div>
                    </div>
                {% else %}
                    <p style="color: #777;" id="noRemindersText">No reminders saved yet.</p>
                {% endfor %}
            </div>
        </div>
    </div>

    <script>
        function filterReminders() {
            let input = document.getElementById('searchInput').value.toLowerCase();
            let cards = document.getElementsByClassName('reminder-card');
            
            for (let i = 0; i < cards.length; i++) {
                let name = cards[i].getAttribute('data-name');
                if (name.includes(input)) {
                    cards[i].style.display = "";
                } else {
                    cards[i].style.display = "none";
                }
            }
        }
    </script>
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def index():
  conn = sqlite3.connect("database.db")
  cursor = conn.cursor()

  if request.method == "POST":
    name = request.form.get("name", "")
    date = request.form.get("date", "")
    time = request.form.get("time", "")
    timing = request.form.get("timing", "")
    message = request.form.get("message", "")

    cursor.execute(
        "INSERT INTO reminders_v3 (name, date, time, timing, message) VALUES"
        " (?, ?, ?, ?, ?)",
        (name, date, time, timing, message),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("index"))

  cursor.execute("SELECT * FROM reminders_v3 ORDER BY date ASC, time ASC")
  reminders = cursor.fetchall()
  conn.close()

  return render_template_string(HTML_TEMPLATE, reminders=reminders, edit_reminder=None)


@app.route("/delete/<int:id>")
def delete_reminder(id):
  conn = sqlite3.connect("database.db")
  cursor = conn.cursor()
  cursor.execute("DELETE FROM reminders_v3 WHERE id = ?", (id,))
  conn.commit()
  conn.close()
  return redirect(url_for("index"))


@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_reminder(id):
  conn = sqlite3.connect("database.db")
  cursor = conn.cursor()

  if request.method == "POST":
    name = request.form.get("name", "")
    date = request.form.get("date", "")
    time = request.form.get("time", "")
    timing = request.form.get("timing", "")
    message = request.form.get("message", "")

    cursor.execute(
        """UPDATE reminders_v3 SET name=?, date=?, time=?, timing=?, message=? WHERE id=?""",
        (name, date, time, timing, message, id),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("index"))

  cursor.execute("SELECT * FROM reminders_v3 WHERE id = ?", (id,))
  target = cursor.fetchone()

  cursor.execute("SELECT * FROM reminders_v3 ORDER BY date ASC, time ASC")
  reminders = cursor.fetchall()
  conn.close()

  return render_template_string(
      HTML_TEMPLATE, reminders=reminders, edit_reminder=target
  )


if __name__ == "__main__":
  init_db()

  alarm_thread = threading.Thread(target=background_alarm_checker, daemon=True)
  alarm_thread.start()

  app.run(debug=True, use_reloader=False)