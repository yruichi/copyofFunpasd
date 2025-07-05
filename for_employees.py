import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import sqlite3
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkcalendar import DateEntry
import pandas as pd
from shared import create_database, BaseWindow
import customtkinter as ctk
import tkinter.ttk as ttk
import time
import smtplib
from email.message import EmailMessage

# database setup
def create_database():
    conn = sqlite3.connect('funpass.db')
    cursor = conn.cursor()

    # To create admin table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    ''')

    # Insert default admin if not exists
    cursor.execute('INSERT OR IGNORE INTO admin (username, password) VALUES (?, ?)',
                  ('admin', 'admin123')) # Default admin credentials
    # You can change the password using sqlite studio

    # Ceate employees table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            express_pass INTEGER DEFAULT 0,
            junior_pass INTEGER DEFAULT 0,
            regular_pass INTEGER DEFAULT 0,
            student_pass INTEGER DEFAULT 0,
            pwd_pass INTEGER DEFAULT 0,
            senior_citizen_pass INTEGER DEFAULT 0
        )
    ''')

    # Create customers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            ticket_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            amount REAL NOT NULL,
            booked_date TEXT NOT NULL,
            purchased_date TEXT NOT NULL,
            pass_type TEXT NOT NULL,
            employee_id INTEGER,
            FOREIGN KEY (employee_id) REFERENCES employees (employee_id)
        )
    ''')

    # Create cancellations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cancellations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            reasons TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            amount REAL NOT NULL,
            booked_date TEXT NOT NULL,
            purchased_date TEXT NOT NULL,
            status TEXT DEFAULT 'Pending',
            FOREIGN KEY (ticket_id) REFERENCES customers (ticket_id)
        )
    ''')

    # Create pricing table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pricing (
            pass_type TEXT PRIMARY KEY,
            price REAL NOT NULL
        )
    ''')

    # To insert or update default prices
    default_prices = [
        ('Express Pass', 2300.00),
        ('Junior Pass', 900.00),
        ('Regular Pass', 1300.00),
        ('Student Pass', 1300.00),
        ('Senior Citizen Pass', 900.00),
        ('PWD Pass', 900.00)
    ]
    
    cursor.executemany('''
        INSERT OR REPLACE INTO pricing (pass_type, price)
        VALUES (?, ?)
    ''', default_prices)

    conn.commit()
    conn.close()

class EmployeeDashboard:
    def __init__(self, root, employee_id=1):
        self.root = root
        self.employee_id = employee_id
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.search_customers)
        self.current_price_frame = None

        # Initialize price cache
        self._price_cache = {}
        # Bind to price update event at root level, everytime na nagchachange si admin nag update ng prices
        print("Binding to price update event")  # Debug print
        self.root.bind('<<PriceUpdate>>', self.refresh_prices, add="+")
        
        self.setup_ui()

    def setup_ui(self):
        self.root.title("FunPass - Employee Dashboard")
        self.root.state('zoomed')
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        self.create_sidebar()
        self.content_frame = tk.Frame(self.root, bg='white')
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.show_dashboard()

    def create_sidebar(self):
        # Modern rounded sidebar with icons, matching main.py style
        sidebar_width = 280
        sidebar_height = 1000
        corner_radius = 40

        sidebar_container = tk.Frame(self.root, bg='white')
        sidebar_container.grid(row=0, column=0, sticky="n", padx=(20, 0), pady=(22, 0))
        sidebar_container.grid_rowconfigure(0, weight=1)
        sidebar_container.grid_columnconfigure(0, weight=1)

        sidebar_canvas = tk.Canvas(sidebar_container, width=sidebar_width, height=sidebar_height, bg='white', highlightthickness=0)
        sidebar_canvas.grid(row=0, column=0, sticky="n")
        self.draw_rounded_rect(sidebar_canvas, 0, 0, sidebar_width, sidebar_height, corner_radius, fill='#ECCD93')

        sidebar_frame = tk.Frame(sidebar_canvas, bg='#ECCD93', width=sidebar_width, height=sidebar_height)
        sidebar_canvas.create_window((sidebar_width//2, 0), window=sidebar_frame, anchor="n")

        # Logo 
        try:
            logo_path = "FunPass__1_-removebg-preview.png"
            logo_img = Image.open(logo_path)
            logo_width = 200
            aspect_ratio = logo_img.height / logo_img.width
            logo_height = int(logo_width * aspect_ratio)
            logo_img = logo_img.resize((logo_width, logo_height))
            self.sidebar_logo = ImageTk.PhotoImage(logo_img)
            logo_label = tk.Label(sidebar_frame, image=self.sidebar_logo, bg='#ECCD93')
            logo_label.pack(padx=(0), pady=(30, 10))
        except Exception as e:
            print(f"Error loading sidebar logo: {e}")

        # Sidebar buttons with icons 
        self.sidebar_buttons = {}
        self.sidebar_button_names = [
            ("🏠  Dashboard", self.show_dashboard),
            ("🎢  Rides", self.show_rides),
            ("👥  Customers", self.show_customers),
            ("❌  Cancellations & Refunds", self.show_cancellations),
            ("💳  Pricing", self.show_pricing),
            ("🚪  Logout", self.logout)
        ]
        for text, command in self.sidebar_button_names:
            btn_canvas = self.create_rounded_button(sidebar_frame, text, lambda c=command, n=text: self._sidebar_button_click(n, c), width=200, height=40, radius=20)
            btn_canvas.pack(pady=8)
            self.sidebar_buttons[text] = btn_canvas

    def _sidebar_button_click(self, name, command):
        self.set_active_sidebar(name)
        command()

    def set_active_sidebar(self, page_name):
        active_color = '#FFD966'  # Highlight color for active
        default_color = '#F0E7D9'  # Default button color
        logout_color = "#FFD966"
        for name, btn_canvas in self.sidebar_buttons.items():
            rect_id = 1
            if name == "🚪  Logout":
                btn_canvas.itemconfig(rect_id, fill=logout_color)
            elif name == page_name:
                btn_canvas.itemconfig(rect_id, fill=active_color)
            else:
                btn_canvas.itemconfig(rect_id, fill=default_color)

    def create_rounded_button(self, parent, text, command, width=200, height=38, radius=20, bg='#F0E7D9', fg='black', font=('Segoe UI', 10, 'normal')):
        is_logout = text.strip().startswith('🚪')
        if is_logout:
            btn_bg = '#FFD966'
            btn_fg = 'white'
            hover_bg = '#F6F6F6'
        else:
            btn_bg = bg
            btn_fg = fg
            hover_bg = '#F6F6F6'
        btn_canvas = tk.Canvas(parent, width=width, height=height, bg=parent['bg'], highlightthickness=0)
        rect = self.draw_rounded_rect(btn_canvas, 2, 2, width-2, height-2, radius, fill=btn_bg)
        label = btn_canvas.create_text(14, height//2, text=text, fill=btn_fg, font=font, anchor='w')
        btn_canvas.bind("<Button-1>", lambda e: command())
        def on_enter(e):
            if hasattr(self, 'sidebar_buttons') and self._is_sidebar_active(text): # hasattr checks if the sidebar_buttons exist
                return
            btn_canvas.itemconfig(rect, fill=hover_bg)
        def on_leave(e):
            if hasattr(self, 'sidebar_buttons') and self._is_sidebar_active(text):
                return
            btn_canvas.itemconfig(rect, fill=btn_bg)
        btn_canvas.bind("<Enter>", on_enter)
        btn_canvas.bind("<Leave>", on_leave)
        return btn_canvas

    def _is_sidebar_active(self, name):
        for n, btn_canvas in self.sidebar_buttons.items():
            rect_id = 1
            if n == name and btn_canvas.itemcget(rect_id, 'fill') == '#FFD966':
                return True
        return False

    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def show_dashboard(self):
        self.clear_content()
        # Dashboard Title and Subtitle 
        dashboard_title = tk.Label(
            self.content_frame, text="Dashboard", font=('Segoe UI', 22, 'bold'), bg='white', anchor='w', fg='#22223B')
        dashboard_title.pack(pady=(24, 0), padx=36, anchor='w')
        dashboard_subtitle = tk.Label(
            self.content_frame, text="Your Sales and Ticket Overview", font=('Segoe UI', 14), fg='#6b7280', bg='white', anchor='w')
        dashboard_subtitle.pack(pady=(0, 18), padx=36, anchor='w')

        # Centering Frame for all cards
        center_frame = tk.Frame(self.content_frame, bg='white')
        center_frame.pack(expand=True)

        # Top Bar Card (Date, Time, Status) 
        top_card_w, top_card_h, top_card_r = 1500, 70, 22
        top_card_canvas = tk.Canvas(center_frame, width=top_card_w, height=top_card_h, bg='white', highlightthickness=0)
        top_card_canvas.pack(padx=0, pady=(0, 18))
        self.draw_rounded_rect(top_card_canvas, 0, 0, top_card_w, top_card_h, top_card_r, fill='#F8F8FA', outline='#E0E0E0', width=1)
        top_inner = tk.Frame(top_card_canvas, bg='#F8F8FA')
        top_card_canvas.create_window((top_card_w//2, top_card_h//2), window=top_inner, anchor='center', width=top_card_w-10, height=top_card_h-10)
        status_label = tk.Label(top_inner, text="🟢 System Online", font=('Segoe UI', 14, 'bold'), bg='#F8F8FA', fg='#4CAF50')
        status_label.pack(side=tk.LEFT, padx=18)
        time_frame = tk.Frame(top_inner, bg='#F8F8FA')
        time_frame.pack(side=tk.RIGHT, padx=18)
        self.date_label = tk.Label(time_frame, font=('Segoe UI', 13), bg='#F8F8FA', fg='#6b7280')
        self.date_label.pack(side=tk.TOP, anchor='e')
        self.time_label = tk.Label(time_frame, font=('Segoe UI', 13, 'bold'), bg='#F8F8FA', fg='#22223B')
        self.time_label.pack(side=tk.TOP, anchor='e')
        self.update_time()

        # Overview Card
        overview_card_w, overview_card_h, overview_card_r = 1500, 270, 22  
        overview_card_canvas = tk.Canvas(center_frame, width=overview_card_w, height=overview_card_h, bg='white', highlightthickness=0)
        overview_card_canvas.pack(padx=0, pady=(0, 18))
        self.draw_rounded_rect(overview_card_canvas, 0, 0, overview_card_w, overview_card_h, overview_card_r, fill='#FFFFFF', outline='#E0E0E0', width=1)
        overview_inner = tk.Frame(overview_card_canvas, bg='#FFFFFF')
        overview_card_canvas.create_window((overview_card_w//2, overview_card_h//2), window=overview_inner, anchor='center', width=overview_card_w-10, height=overview_card_h-10)
        tk.Label(overview_inner, text='Overview', font=('Segoe UI', 15, 'bold'), bg='#FFFFFF', fg='#22223B', anchor='w').pack(anchor='w', pady=(10, 0), padx=20)
        stats_grid = tk.Frame(overview_inner, bg='#FFFFFF')
        stats_grid.pack(fill='both', expand=True, padx=20, pady=(10, 10))
        for i in range(2):
            stats_grid.grid_columnconfigure(i, weight=1)
        conn = sqlite3.connect('funpass.db')
        cursor = conn.cursor()
        cursor.execute('''SELECT IFNULL(SUM(amount), 0) FROM customers WHERE employee_id=?''', (self.employee_id,))
        total_sales = cursor.fetchone()[0] or 0
        cursor.execute('''SELECT IFNULL(SUM(amount), 0) FROM cancellations WHERE status='Approved' AND ticket_id IN (SELECT ticket_id FROM customers WHERE employee_id=?)''', (self.employee_id,))
        cancelled_sales = cursor.fetchone()[0] or 0
        net_sales = total_sales - cancelled_sales
        cursor.execute('''SELECT SUM(amount) FROM customers WHERE employee_id=? AND strftime('%Y-%m', purchased_date) = strftime('%Y-%m', 'now')''', (self.employee_id,))
        monthly_sales = cursor.fetchone()[0] or 0
        cursor.execute('SELECT SUM(quantity) FROM customers WHERE employee_id=?', (self.employee_id,))
        total_tickets = cursor.fetchone()[0] or 0
        cursor.execute('''SELECT pass_type, SUM(quantity) as total_qty FROM customers WHERE employee_id=? GROUP BY pass_type ORDER BY total_qty DESC''', (self.employee_id,))
        popular_passes = cursor.fetchall()
        if popular_passes and len(popular_passes) > 0:
            top_pass = popular_passes[0]
            popular_ticket_text = f"{top_pass[0]}\n({top_pass[1]} sold)"
        else:
            popular_ticket_text = "No passes\nsold yet"
        conn.close()
        stats_data = [
            ("💰 Total Sales", f"₱{total_sales:,.2f}", "#2196F3"),
            ("📅 This Month's Sales", f"₱{monthly_sales:,.2f}", "#009688"),
            ("🎟️ Total Tickets Sold", f"{int(total_tickets) if total_tickets else 0}", "#FF9800"),
            ("🏆 Most Popular Pass", popular_ticket_text, "#673AB7")
        ]
        for idx, (label, value, color) in enumerate(stats_data):
            stat_card_w, stat_card_h, stat_card_r = 500, 70, 18
            stat_card_canvas = tk.Canvas(stats_grid, width=stat_card_w, height=stat_card_h, bg='#FFFFFF', highlightthickness=0)
            stat_card_canvas.grid(row=idx//2, column=idx%2, padx=16, pady=8)
            self.draw_rounded_rect(stat_card_canvas, 0, 0, stat_card_w, stat_card_h, stat_card_r, fill='white', outline='#E0E0E0', width=1)
            stat_inner = tk.Frame(stat_card_canvas, bg='white')
            stat_card_canvas.create_window((stat_card_w//2, stat_card_h//2), window=stat_inner, anchor='center', width=stat_card_w-8, height=stat_card_h-8)
            tk.Label(stat_inner, text=label, font=('Segoe UI', 10, 'bold'), bg='white', fg=color).pack(anchor='w', pady=(6, 0), padx=12)
            if '\n' in str(value):
                value1, value2 = value.split('\n')
                tk.Label(stat_inner, text=value1, font=('Segoe UI', 15, 'bold'), fg=color, bg='white').pack(anchor='w', padx=12)
                tk.Label(stat_inner, text=value2, font=('Segoe UI', 11), fg=color, bg='white').pack(anchor='w', padx=12)
            else:
                tk.Label(stat_inner, text=value, font=('Segoe UI', 18, 'bold'), fg=color, bg='white').pack(anchor='w', padx=12)

        # Availability Card
        avail_card_w, avail_card_h, avail_card_r = 1500, 170, 22
        avail_card_canvas = tk.Canvas(center_frame, width=avail_card_w, height=avail_card_h, bg='white', highlightthickness=0)
        avail_card_canvas.pack(padx=0, pady=(0, 18))
        self.draw_rounded_rect(avail_card_canvas, 0, 0, avail_card_w, avail_card_h, avail_card_r, fill='#FFFFFF', outline='#E0E0E0', width=1)
        avail_inner = tk.Frame(avail_card_canvas, bg='#FFFFFF')
        avail_card_canvas.create_window((avail_card_w//2, avail_card_h//2), window=avail_inner, anchor='center', width=avail_card_w-10, height=avail_card_h-10)
        tk.Label(avail_inner, text="Total Availability", font=('Segoe UI', 14, 'bold'), bg='#FFFFFF', fg='#22223B').pack(anchor='w', pady=(10, 0), padx=20)
        # Scrollable Frame for Availability List 
        avail_scroll_canvas = tk.Canvas(avail_inner, bg='#FFFFFF', highlightthickness=0, height=80)
        avail_scroll_canvas.pack(fill=tk.X, padx=20, pady=8, expand=True)
        avail_scrollbar = tk.Scrollbar(avail_inner, orient=tk.HORIZONTAL, command=avail_scroll_canvas.xview)
        avail_scrollbar.pack(fill=tk.X, padx=20, pady=(0, 4))
        avail_scroll_canvas.configure(xscrollcommand=avail_scrollbar.set)
        avail_frame = tk.Frame(avail_scroll_canvas, bg='#FFFFFF')
        avail_scroll_canvas.create_window((0, 0), window=avail_frame, anchor='nw')
        def _on_avail_frame_configure(event):
            avail_scroll_canvas.configure(scrollregion=avail_scroll_canvas.bbox('all'))
        avail_frame.bind('<Configure>', _on_avail_frame_configure)
        conn = sqlite3.connect('funpass.db')
        cursor = conn.cursor()
        cursor.execute('''SELECT express_pass, junior_pass, regular_pass, student_pass, senior_citizen_pass, pwd_pass FROM employees WHERE employee_id = ?''', (self.employee_id,))
        allocated = cursor.fetchone()
        pass_types = ['Express Pass', 'Junior Pass', 'Regular Pass', 'Student Pass', 'Senior Citizen Pass', 'PWD Pass']
        sold_tickets = {}
        for pass_type in pass_types:
            cursor.execute('SELECT SUM(quantity) FROM customers WHERE pass_type=? AND employee_id=?', (pass_type, self.employee_id))
            sold = cursor.fetchone()[0] or 0
            sold_tickets[pass_type] = int(sold)
        pass_data = [
            ('A', 'Express Pass', int(allocated[0] if allocated and len(allocated) > 0 else 0), sold_tickets['Express Pass']),
            ('B', 'Junior Pass', int(allocated[1] if allocated and len(allocated) > 1 else 0), sold_tickets['Junior Pass']),
            ('C', 'Regular Pass', int(allocated[2] if allocated and len(allocated) > 2 else 0), sold_tickets['Regular Pass']),
            ('D', 'Student Pass', int(allocated[3] if allocated and len(allocated) > 3 else 0), sold_tickets['Student Pass']),
            ('E', 'Senior Citizen Pass', int(allocated[4] if allocated and len(allocated) > 4 else 0), sold_tickets['Senior Citizen Pass']),
            ('F', 'PWD Pass', int(allocated[5] if allocated and len(allocated) > 5 else 0), sold_tickets['PWD Pass'])
        ]
        for letter, pass_type, total_allocated, sold in pass_data:
            available = total_allocated - sold
            row_frame = tk.Frame(avail_frame, bg='#FFFFFF')
            row_frame.pack(side=tk.LEFT, padx=10, pady=2)
            label_text = f"{letter}. {pass_type}: {available}"
            tk.Label(row_frame, text=label_text, font=('Segoe UI', 12, 'bold'), bg='#FFFFFF', anchor='w', fg='#2196F3').pack(side=tk.LEFT, padx=15, pady=2)
        conn.close()

        # Recent Sales Card
        recent_card_w, recent_card_h, recent_card_r = 1500, 250, 22
        recent_card_canvas = tk.Canvas(center_frame, width=recent_card_w, height=recent_card_h, bg='white', highlightthickness=0)
        recent_card_canvas.pack(padx=0, pady=(0, 18))
        self.draw_rounded_rect(recent_card_canvas, 0, 0, recent_card_w, recent_card_h, recent_card_r, fill='#FFFFFF', outline='#E0E0E0', width=1)
        recent_inner = tk.Frame(recent_card_canvas, bg='#FFFFFF')
        recent_card_canvas.create_window((recent_card_w//2, recent_card_h//2), window=recent_inner, anchor='center', width=recent_card_w-10, height=recent_card_h-10)
        tk.Label(recent_inner, text="Recent Sales", font=('Segoe UI', 14, 'bold'), bg='#FFFFFF', fg='#22223B').pack(anchor='w', pady=(10, 0), padx=20)
        conn = sqlite3.connect('funpass.db')
        cursor = conn.cursor()
        cursor.execute('''SELECT ticket_id, name, pass_type, quantity, amount, purchased_date FROM customers WHERE employee_id=? ORDER BY purchased_date DESC, rowid DESC LIMIT 5''', (self.employee_id,))
        recents = cursor.fetchall()
        conn.close()
        header_row = tk.Frame(recent_inner, bg='#F5F6FA')
        header_row.pack(fill=tk.X, pady=(8, 2))
        tk.Label(header_row, text="Customer Name", font=('Segoe UI', 11, 'bold'), bg='#F5F6FA', width=18, anchor='w', fg='#22223B').pack(side=tk.LEFT, padx=5)
        tk.Label(header_row, text="Pass Type", font=('Segoe UI', 11, 'bold'), bg='#F5F6FA', width=12, anchor='w', fg='#22223B').pack(side=tk.LEFT, padx=5)
        tk.Label(header_row, text="Qty", font=('Segoe UI', 11, 'bold'), bg='#F5F6FA', width=5, anchor='w', fg='#22223B').pack(side=tk.LEFT, padx=5)
        tk.Label(header_row, text="Amount", font=('Segoe UI', 11, 'bold'), bg='#F5F6FA', width=10, anchor='w', fg='#22223B').pack(side=tk.LEFT, padx=5)
        tk.Label(header_row, text="Date", font=('Segoe UI', 11, 'bold'), bg='#F5F6FA', width=12, anchor='w', fg='#22223B').pack(side=tk.LEFT, padx=5)
        if recents:
            for ticket_id, name, pass_type, quantity, amount, purchased_date in recents:
                row = tk.Frame(recent_inner, bg='#FFFFFF')
                row.pack(fill=tk.X, pady=1)
                tk.Label(row, text=name, font=('Segoe UI', 11), bg='#FFFFFF', width=18, anchor='w').pack(side=tk.LEFT, padx=5)
                tk.Label(row, text=pass_type, font=('Segoe UI', 11), bg='#FFFFFF', width=12, anchor='w').pack(side=tk.LEFT, padx=5)
                tk.Label(row, text=quantity, font=('Segoe UI', 11), bg='#FFFFFF', width=5, anchor='w').pack(side=tk.LEFT, padx=5)
                tk.Label(row, text=f"₱{amount:,.2f}", font=('Segoe UI', 11), bg='#FFFFFF', width=10, anchor='w').pack(side=tk.LEFT, padx=5)
                tk.Label(row, text=purchased_date, font=('Segoe UI', 11), bg='#FFFFFF', width=12, anchor='w').pack(side=tk.LEFT, padx=5)
        else:
            tk.Label(recent_inner, text="No sales yet.", font=('Segoe UI', 11, 'italic'), fg='#6b7280', bg='#FFFFFF', anchor='w').pack(anchor='w', padx=10, pady=2)

    def update_time(self):
        try:
            current = datetime.now()
            current_time = current.strftime("%Y-%m-%d %H:%M:%S")
            if hasattr(self, 'time_label') and self.time_label.winfo_exists():
                self.time_label.config(text=current_time)
            if hasattr(self, 'date_label') and self.date_label.winfo_exists():
                self.date_label.config(text=current.strftime("%A, %B %d, %Y"))
            self.root.after(1000, self.update_time)
        except Exception as e:
            print(f"Error updating time: {e}")

    def show_rides(self):
        self.clear_content()
        # Section background frame 
        rides_frame = tk.Frame(self.content_frame, bg='#F0E7D9')
        rides_frame.pack(fill=tk.BOTH, expand=True)
        # Centering frame for all content
        center_frame = tk.Frame(rides_frame, bg='#F0E7D9')
        center_frame.pack(expand=True)
        # Header row
        header_row = tk.Frame(center_frame, bg='#F0E7D9')
        header_row.pack(fill=tk.X, pady=(20, 0), padx=30)
        title = tk.Label(header_row, text="Pass Types and Inclusions", font=('Segoe UI', 20, 'bold'), bg='#F0E7D9', fg='black', anchor='w')
        title.pack(side=tk.LEFT, anchor='w')
        # Subtitle
        subtitle = tk.Label(center_frame, text="View rides descriptions and inclusions", font=('Segoe UI', 15), fg='#6b7280', bg='#F0E7D9', anchor='w')
        subtitle.pack(fill=tk.X, padx=30, anchor='w')
        # Pass type cards grid (centered)
        grid_frame = tk.Frame(center_frame, bg='#F0E7D9')
        grid_frame.pack(pady=(10, 10), padx=(0, 0), fill='both', expand=True)
        card_w2, card_h2, card_r2 = 400, 350, 35
        card_bg = 'white'
        card_fg = 'black'
        card_padx = 20
        card_pady = 20
        pass_descriptions = [
            ("Express Pass", """• Priority access to all rides and attractions\n• Skip regular lines\n• Access to exclusive Express Pass lanes\n• Unlimited rides all day\n• Special discounts at food stalls\n• Free locker usage\n• Free parking\n• Exclusive souvenir"""),
            ("Junior Pass", """• Access to all kid-friendly rides\n• Special access to children's play areas\n• Meet and greet with mascots\n• Free snack pack\n• Age requirement: 4-12 years old\n• Free kids meal\n• Free face painting\n• Access to kids' workshops"""),
            ("Regular Pass", """• Standard access to all rides and attractions\n• Regular queue lines\n• Full day access\n• Basic amenities access\n• Suitable for all ages\n• Free water bottle\n• Access to rest areas\n• Standard locker rental rates"""),
            ("Student Pass", """• Access to all rides and attractions\n• Special student discount\n• Valid student ID required\n• Available on weekdays only\n• Includes free locker use\n• Free study area access\n• Student meal discount\n• Free WiFi access"""),
            ("Senior Citizen Pass", """• Access to all rides and attractions\n• Priority queuing at selected rides\n• Special assistance available\n• Senior citizen ID required\n• Includes free refreshments\n• Access to senior's lounge\n• Free health monitoring\n• Special meal options"""),
            ("PWD Pass", """• Access to all rides and attractions\n• Priority queuing at all rides\n• Special assistance available\n• PWD ID required\n• Companion gets 50% discount\n• Free wheelchair service\n• Dedicated assistance staff\n• Special facilities access""")
        ]
        for idx, (pass_type, description) in enumerate(pass_descriptions):
            row = idx // 3
            col = idx % 3
            card_canvas2 = tk.Canvas(grid_frame, width=card_w2, height=card_h2, bg='#F0E7D9', highlightthickness=0)
            card_canvas2.grid(row=row, column=col, padx=card_padx, pady=card_pady, sticky='n')
            rect_id = self.draw_rounded_rect(card_canvas2, 0, 0, card_w2, card_h2, card_r2, fill=card_bg, outline='#E0E0E0', width=2)
            card_frame2 = tk.Frame(card_canvas2, bg=card_bg)
            card_canvas2.create_window((card_w2//2, card_h2//2), window=card_frame2, anchor='center')
            # Stat icon area
            stat_icon_frame = tk.Frame(card_frame2, bg='#F7F7FA', width=48, height=48)
            stat_icon_frame.pack(anchor='w', padx=14, pady=(12, 0))
            stat_icon_frame.pack_propagate(False)
            icon_map = {
                'Express Pass': '⚡',
                'Junior Pass': '🧒',
                'Regular Pass': '🎟️',
                'Student Pass': '🎓',
                'Senior Citizen Pass': '👴',
                'PWD Pass': '♿',
            }
            icon = icon_map.get(pass_type, '🎟️')
            tk.Label(stat_icon_frame, text=icon, font=('Segoe UI', 22), bg='#F7F7FA', fg='#9A4E62').pack(expand=True)
            tk.Label(card_frame2, text=pass_type, font=('Segoe UI', 15, 'bold'), bg=card_bg, fg='#9A4E62').pack(anchor='w', padx=14, pady=(4, 0))
            tk.Label(card_frame2, text=description, font=('Segoe UI', 10), bg=card_bg, fg=card_fg, justify=tk.LEFT, anchor='w', wraplength=card_w2-28).pack(anchor='w', padx=15, pady=(0, 15))
            

    # Utility for rounded rect 
    def draw_rounded_rect(self, canvas, x1, y1, x2, y2, r, **kwargs):
        points = [
            x1+r, y1,
            x2-r, y1,
            x2, y1,
            x2, y1+r,
            x2, y2-r,
            x2, y2,
            x2-r, y2,
            x1+r, y2,
            x1, y2,
            x1, y2-r,
            x1, y1+r,
            x1, y1
        ]
        return canvas.create_polygon(points, smooth=True, **kwargs)

    def show_customers(self):
        import customtkinter as ctk
        import tkinter.ttk as ttk
        self.clear_content()
        self.set_active_sidebar('👥  Customers')

        # Main Card Container
        card_frame = ctk.CTkFrame(self.content_frame, fg_color="#FFFFFF", corner_radius=25)
        card_frame.pack(fill="both", expand=True, padx=30, pady=30)

        # Header Block
        header_row = ctk.CTkFrame(card_frame, fg_color="#FFFFFF")
        header_row.pack(fill="x", pady=(10, 0), anchor="w")
        header_row.grid_columnconfigure(0, weight=1)
        customer_title = ctk.CTkLabel(header_row, text="Customers", font=("Segoe UI", 22, "bold"), text_color="#22223B")
        customer_title.grid(row=0, column=0, padx=15, sticky="w")
        customer_subtitle = ctk.CTkLabel(header_row, text="View, Add, Edit, and Delete Customers", font=("Segoe UI", 15), text_color="#6b7280")
        customer_subtitle.grid(row=1, column=0, padx=15, pady=10, sticky="w")

        # Controls Bar 
        controls_bar = ctk.CTkFrame(card_frame, fg_color="#F0E7D9", corner_radius=0, height=50)
        controls_bar.pack(fill="x", padx=10, pady=(0, 15))
        controls_bar.grid_columnconfigure(0, weight=1)
        controls_bar.grid_columnconfigure(1, weight=0)
        controls_bar.grid_columnconfigure(2, weight=0)
        controls_bar.grid_columnconfigure(3, weight=0)
        controls_bar.grid_columnconfigure(4, weight=0)
        controls_bar.grid_columnconfigure(5, weight=0)

        # Search Entry
        self.search_var = ctk.StringVar()
        self.search_var.trace('w', self.search_customers)
        search_entry = ctk.CTkEntry(
            controls_bar,
            textvariable=self.search_var,
            placeholder_text="Search customer...",
            width=220,
            height=36,
            font=("Segoe UI", 12),
            fg_color="#fff",
            border_color="#cccccc",
            border_width=2
        )
        search_entry.grid(row=0, column=0, padx=(16, 8), pady=10, sticky="w")

        # Sort Combobox (all columns)
        sort_options_list = [
            ("Ticket ID (A-Z)", 0, False), ("Ticket ID (Z-A)", 0, True),
            ("Name (A-Z)", 1, False), ("Name (Z-A)", 1, True),
            ("Email (A-Z)", 2, False), ("Email (Z-A)", 2, True),
            ("Quantity (Lowest)", 3, False), ("Quantity (Highest)", 3, True),
            ("Amount (Lowest)", 4, False), ("Amount (Highest)", 4, True),
            ("Booked Date (Newest)", 5, True), ("Booked Date (Oldest)", 5, False),
            ("Purchased Date (Newest)", 6, True), ("Purchased Date (Oldest)", 6, False),
            ("Pass Type (A-Z)", 7, False), ("Pass Type (Z-A)", 7, True)
        ]
        sort_options = ctk.CTkComboBox(
            controls_bar,
            values=[opt[0] for opt in sort_options_list],
            width=200,
            font=("Segoe UI", 12),
            dropdown_font=("Segoe UI", 12),
            state="readonly",
            fg_color="#fff",
            border_color="#cccccc",
            border_width=2
        )
        sort_options.set("Name (A-Z)")
        sort_options.grid(row=0, column=1, padx=(0, 8), pady=10)
        sort_options.configure(command=lambda value: self.sort_customers(value))
        self._customer_sort_options = sort_options_list

        # Add, Edit, Delete, View Receipt Buttons
        add_btn = ctk.CTkButton(
            controls_bar, text="Add Customer", width=110, height=36, fg_color="#E0E0E0", text_color="#4CAF50", hover_color="#C8E6C9",
            font=("Segoe UI", 12, "bold"), corner_radius=10, command=self.add_customer_dialog
        )
        add_btn.grid(row=0, column=2, padx=(0, 8), pady=10)
        edit_btn = ctk.CTkButton(
            controls_bar, text="Edit Customer", width=110, height=36, fg_color="#E0E0E0", text_color="#2196F3", hover_color="#BBDEFB",
            font=("Segoe UI", 12, "bold"), corner_radius=10, command=self.edit_customer_dialog
        )
        edit_btn.grid(row=0, column=3, padx=(0, 8), pady=10)
        delete_btn = ctk.CTkButton(
            controls_bar, text="Delete", width=90, height=36, fg_color="#E0E0E0", text_color="#f44336", hover_color="#FFCDD2",
            font=("Segoe UI", 12, "bold"), corner_radius=10, command=self.delete_customer
        )
        delete_btn.grid(row=0, column=4, padx=(0, 8), pady=10)
        receipt_btn = ctk.CTkButton(
            controls_bar, text="View Receipt", width=110, height=36, fg_color="#E0E0E0", text_color="#D0A011", hover_color="#FFF9C4",
            font=("Segoe UI", 12, "bold"), corner_radius=10, command=self.view_receipt
        )
        receipt_btn.grid(row=0, column=5, padx=(0, 12), pady=10)

        # Table Frame 
        table_card = ctk.CTkFrame(card_frame, fg_color="#fff", corner_radius=18)
        table_card.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        table_card.grid_rowconfigure(0, weight=1)
        table_card.grid_columnconfigure(0, weight=1)

        # Scrollbars
        yscroll = ctk.CTkScrollbar(table_card, orientation="vertical")
        xscroll = ctk.CTkScrollbar(table_card, orientation="horizontal")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")

        # Table (ttk.Treeview inside CTkFrame)
        columns = ('Ticket ID', 'Name', 'Email', 'Quantity', 'Amount', 'Booked Date', 'Purchased Date', 'Pass Type')
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Treeview', font=('Segoe UI', 11), rowheight=32, background='#FFFFFF', fieldbackground='#FFFFFF', borderwidth=0)
        style.configure('Treeview.Heading', font=('Segoe UI', 11, 'bold'), background='#E0E0E0', foreground='#9A4E62', borderwidth=0)
        style.layout('Treeview', [('Treeview.treearea', {'sticky': 'nswe'})])
        self.customers_tree = ttk.Treeview(
            table_card, columns=columns, show='headings', style='Treeview',
            yscrollcommand=yscroll.set, xscrollcommand=xscroll.set
        )
        self.customers_tree.grid(row=0, column=0, sticky='nsew')
        yscroll.configure(command=self.customers_tree.yview)
        xscroll.configure(command=self.customers_tree.xview)
        column_widths = {
            'Ticket ID': 100,
            'Name': 150,
            'Email': 200,
            'Quantity': 80,
            'Amount': 100,
            'Booked Date': 120,
            'Purchased Date': 120,
            'Pass Type': 120
        }
        for col in columns:
            self.customers_tree.heading(col, text=col)
            width = column_widths.get(col, 120)
            self.customers_tree.column(col, width=width, anchor='w')
        def clear_selection_on_click(event):
            region = self.customers_tree.identify("region", event.x, event.y)
            if region == "nothing":
                self.customers_tree.selection_remove(self.customers_tree.selection())
        self.customers_tree.bind("<Button-1>", clear_selection_on_click, add="+")
        self.load_customers_data()

    def search_customers(self, *args):
        search_text = self.search_var.get().lower()
        for item in self.customers_tree.get_children():
            self.customers_tree.delete(item)
        conn = sqlite3.connect('funpass.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT ticket_id, name, email, quantity, amount, 
                   strftime('%Y-%m-%d', booked_date) as booked_date,
                   strftime('%Y-%m-%d', purchased_date) as purchased_date,
                   pass_type 
            FROM customers 
            WHERE employee_id=?
        ''', (self.employee_id,))
        customers = cursor.fetchall()
        conn.close()

        for customer in customers:
            # Convert tuple to list for modification
            # We convert tuple to a list for modification because tuples in Python are immutable, you cannot change their contents after creation. Lists, on the other hand, are mutable and allow you to modify, assign, or update their elements.
            data = list(customer)
            
            # Format dates
            try:
                if data[5]:  # booked_date
                    date_obj = datetime.strptime(data[5], '%Y-%m-%d')
                    data[5] = date_obj.strftime('%m-%d-%Y')
                if data[6]:  # purchased_date
                    date_obj = datetime.strptime(data[6], '%Y-%m-%d')
                    data[6] = date_obj.strftime('%m-%d-%Y')
            except ValueError:
                pass

            if any(search_text in str(value).lower() for value in data):
                self.customers_tree.insert('', tk.END, values=data)

    def sort_customers(self, sort_option):
        items = []
        for item in self.customers_tree.get_children():
            values = self.customers_tree.item(item)['values']
            items.append(values)
        for label, idx, reverse in self._customer_sort_options:
            if label == sort_option:
            # Quantity, Amount
                if idx in [4, 5]:
                    items.sort(key=lambda x: float(str(x[idx]).replace('₱','').replace(',','')), reverse=reverse)
            # Booked Date, Purchased Date
                elif idx in [6, 7]:
                    from datetime import datetime
                    def parse_date(val):
                        try:
                            return datetime.strptime(val, '%m/%d/%Y')
                        except Exception:
                            return datetime.min
                    items.sort(key=lambda x: parse_date(x[idx]), reverse=reverse)
                else:
                    items.sort(key=lambda x: str(x[idx]).lower(), reverse=reverse)
                break
        for item in self.customers_tree.get_children():
            self.customers_tree.delete(item)
        for item in items:
            self.customers_tree.insert('', tk.END, values=item)

    def load_customers_data(self):
        for item in self.customers_tree.get_children():
            self.customers_tree.delete(item)
        conn = sqlite3.connect('funpass.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT ticket_id, name, email, quantity, amount, 
                   strftime('%Y-%m-%d', booked_date) as booked_date,
                   strftime('%Y-%m-%d', purchased_date) as purchased_date,
                   pass_type 
            FROM customers 
            WHERE employee_id=?
        ''', (self.employee_id,))
        customers = cursor.fetchall()
        conn.close()

        for customer in customers:
            # Convert tuple to list for modification
            data = list(customer)
            
            # Format booked_date (index 5)
            try:
                if data[5]:
                    date_obj = datetime.strptime(data[5], '%Y-%m-%d')
                    data[5] = date_obj.strftime('%m-%d-%Y')
            except ValueError:
                pass

            # Format purchased_date (index 6)
            try:
                if data[6]:
                    date_obj = datetime.strptime(data[6], '%Y-%m-%d')
                    data[6] = date_obj.strftime('%m-%d-%Y')
            except ValueError:
                pass

            self.customers_tree.insert('', tk.END, values=data)

    def get_availability_for_pass(self, pass_type):
        conn = sqlite3.connect('funpass.db')
        cursor = conn.cursor()
        
        # Get total tickets sold
        cursor.execute('SELECT SUM(quantity) FROM customers WHERE pass_type=?', (pass_type,))
        sold = cursor.fetchone()[0] or 0
        total_available = 1000 - sold
        
        # Get employee's allocation
        cursor.execute('''
            SELECT 
                CASE 
                    WHEN pass_type = 'Express Pass' THEN express_pass
                    WHEN pass_type = 'Junior Pass' THEN junior_pass
                    WHEN pass_type = 'Regular Pass' THEN regular_pass
                    WHEN pass_type = 'Student Pass' THEN student_pass
                    WHEN pass_type = 'PWD Pass' THEN pwd_pass
                    WHEN pass_type = 'Senior Citizen Pass' THEN senior_citizen_pass
                END
            FROM employees 
            WHERE employee_id = ?
        ''', (self.employee_id,))
        allocation = cursor.fetchone()[0] or 0
        
        # Get tickets already sold by this employee for this pass type
        cursor.execute('''
            SELECT SUM(quantity) 
            FROM customers 
            WHERE pass_type = ? AND employee_id = ?
        ''', (pass_type, self.employee_id))
        employee_sold = cursor.fetchone()[0] or 0
        
        # Employee's remaining allocation
        employee_available = allocation - employee_sold
        
        conn.close()
        
        # Return the lower of total availability and employee's remaining allocation
        return min(total_available, employee_available)

    def compute_amount(self, pass_type_combo, quantity_entry, amount_var):
        try:
            pass_type = pass_type_combo.get()
            quantity = int(quantity_entry.get() or 0)
            if pass_type and quantity > 0:
                # Get price from database
                price = self.get_price_for_pass(pass_type)
                amount = price * quantity
                amount_var.set(f"{amount:.2f}")
            else:
                amount_var.set("")
        except ValueError:
            amount_var.set("")

    def add_customer_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Customer")
        dialog.geometry("500x600")
        dialog.configure(bg='white')
        main_frame = tk.Frame(dialog, bg='white', padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        ticket_id = self.generate_ticket_id()
        tk.Label(main_frame, text=f"Ticket ID: {ticket_id}", font=('Arial', 11, 'bold'), bg='white').pack(anchor='w', pady=(0, 10))
        
        # Name
        tk.Label(main_frame, text="Name:", font=('Arial', 11), bg='white').pack(anchor='w')
        name_entry = tk.Entry(main_frame, font=('Arial', 11))
        name_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Email
        tk.Label(main_frame, text="Email:", font=('Arial', 11), bg='white').pack(anchor='w')
        email_entry = tk.Entry(main_frame, font=('Arial', 11))
        email_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Pass Type 
        tk.Label(main_frame, text="Pass Type:", font=('Arial', 11), bg='white').pack(anchor='w')
        pass_types = self.get_pass_types()
        pass_type_combo = ttk.Combobox(main_frame, values=pass_types, font=('Arial', 11), state="readonly")
        pass_type_combo.pack(fill=tk.X, pady=(0, 10))
        if pass_types:
            pass_type_combo.set(pass_types[0])  # Set default to "Express Pass"

        # Quantity
        tk.Label(main_frame, text="Quantity:", font=('Arial', 11), bg='white').pack(anchor='w')
        quantity_entry = tk.Entry(main_frame, font=('Arial', 11))
        quantity_entry.pack(fill=tk.X, pady=(0, 10))

        # Amount (read-only)
        tk.Label(main_frame, text="Amount:", font=('Arial', 11), bg='white').pack(anchor='w')
        amount_var = tk.StringVar(value="₱0.00")
        amount_entry = tk.Entry(main_frame, textvariable=amount_var, font=('Arial', 11), state='readonly')
        amount_entry.pack(fill=tk.X, pady=(0, 10))

        def update_amount(*args):
            try:
                pass_type = pass_type_combo.get()
                quantity = int(quantity_entry.get() if quantity_entry.get() else 0)
                if pass_type and quantity > 0:
                    price = self.get_price_for_pass(pass_type)
                    total = price * quantity
                    amount_var.set(f"₱{total:,.2f}")
                else:
                    amount_var.set("₱0.00")
            except ValueError:
                amount_var.set("₱0.00")

        # Bind the update function to both pass type and quantity changes
        pass_type_combo.bind('<<ComboboxSelected>>', update_amount)
        quantity_entry.bind('<KeyRelease>', update_amount)
        
        tk.Label(main_frame, text="Booked Date:", font=('Arial', 11), bg='white').pack(anchor='w')
        booked_date_entry = DateEntry(main_frame, font=('Arial', 11), width=18, date_pattern='yyyy-MM-dd')
        booked_date_entry.pack(fill=tk.X, pady=(0, 10))
        purchased_date = datetime.now().strftime('%Y-%m-%d')
        
        tk.Label(main_frame, text="Purchased Date:", font=('Arial', 11), bg='white').pack(anchor='w')
        purchased_date_label = tk.Label(main_frame, text=purchased_date, font=('Arial', 11), bg='white')
        purchased_date_label.pack(fill=tk.X, pady=(0, 10))

        def save_customer():
            name = name_entry.get().strip()
            email = email_entry.get().strip()
            quantity = quantity_entry.get().strip()
            pass_type = pass_type_combo.get().strip()
            amount = amount_var.get().replace('₱', '').replace(',', '')
            booked_date = booked_date_entry.get()

            if not (name and quantity and pass_type and amount and booked_date):
                messagebox.showerror("Error", "Name, Quantity, Pass Type, Amount, and Booked Date are required!")
                return

            try:
                quantity = int(quantity)
                if quantity <= 0:
                    messagebox.showerror("Error", "Quantity must be greater than 0!")
                    return

                # Check ticket availability
                conn = sqlite3.connect('funpass.db')
                cursor = conn.cursor()
                
                # Get employee's allocation
                cursor.execute('''

                    SELECT 
                        CASE 
                            WHEN ? = 'Express Pass' THEN express_pass
                            WHEN ? = 'Junior Pass' THEN junior_pass
                            WHEN ? = 'Regular Pass' THEN regular_pass
                            WHEN ? = 'Student Pass' THEN student_pass
                            WHEN ? = 'PWD Pass' THEN pwd_pass
                            WHEN ? = 'Senior Citizen Pass' THEN senior_citizen_pass
                        END
                    FROM employees 
                    WHERE employee_id = ?
                ''', (pass_type, pass_type, pass_type, pass_type, pass_type, pass_type, self.employee_id))
                
                allocation = cursor.fetchone()[0] or 0

                # Get tickets already sold by this employee
                cursor.execute('''

                    SELECT SUM(quantity) 
                    FROM customers 
                    WHERE pass_type = ? AND employee_id = ?
                ''', (pass_type, self.employee_id))
                
                sold = cursor.fetchone()[0] or 0
                available = allocation - sold

                if quantity > available:
                    messagebox.showerror("Error", 
                        f"Not enough tickets available!\nYou can only sell {available} more {pass_type} tickets.")
                    conn.close()
                    return

                # If validation passes, proceed with saving
                cursor.execute('''INSERT INTO customers 
                                (ticket_id, name, email, quantity, amount, booked_date, purchased_date, pass_type, employee_id) 
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                             (ticket_id, name, email, quantity, float(amount), booked_date, purchased_date, 
                              pass_type, self.employee_id))
                conn.commit()
                conn.close()
                dialog.destroy()
                self.load_customers_data()
                self.print_ticket(ticket_id, name, email, quantity, amount, booked_date, purchased_date, pass_type)
                self.send_ticket_email(email, ticket_id, name, email, quantity, amount, booked_date, purchased_date, pass_type)
                messagebox.showinfo("Success", "Customer added and ticket printed!")
            except ValueError:
                messagebox.showerror("Error", "Invalid quantity or amount!")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {str(e)}")

        tk.Button(main_frame, text="Save", command=save_customer, bg='#4CAF50', fg='white').pack(pady=10)
        tk.Button(main_frame, text="Cancel", command=dialog.destroy, bg='#f44336', fg='white').pack()

    def edit_customer_dialog(self):
        selected = self.customers_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a customer to edit.")
            return

        values = self.customers_tree.item(selected[0])['values']
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Customer")
        dialog.geometry("500x650")
        dialog.configure(bg='white')
        
        main_frame = tk.Frame(dialog, bg='white', padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Ticket ID (read-only)
        tk.Label(main_frame, text="Ticket ID:", font=('Arial', 11), bg='white').pack(anchor='w')
        ticket_id_var = tk.StringVar(value=values[0])
        ticket_id_entry = tk.Entry(main_frame, textvariable=ticket_id_var, font=('Arial', 11), state='readonly')
        ticket_id_entry.pack(fill=tk.X, pady=(0, 10))

        # Name
        tk.Label(main_frame, text="Name:", font=('Arial', 11), bg='white').pack(anchor='w')
        name_var = tk.StringVar(value=values[1])
        name_entry = tk.Entry(main_frame, textvariable=name_var, font=('Arial', 11))
        name_entry.pack(fill=tk.X, pady=(0, 10))

        # Email
        tk.Label(main_frame, text="Email:", font=('Arial', 11), bg='white').pack(anchor='w')
        email_var = tk.StringVar(value=values[2])
        email_entry = tk.Entry(main_frame, textvariable=email_var, font=('Arial', 11))
        email_entry.pack(fill=tk.X, pady=(0, 10))

        # Quantity
        tk.Label(main_frame, text="Quantity:", font=('Arial', 11), bg='white').pack(anchor='w')
        quantity_var = tk.StringVar(value=values[3])
        quantity_entry = tk.Entry(main_frame, textvariable=quantity_var, font=('Arial', 11))
        quantity_entry.pack(fill=tk.X, pady=(0, 10))

        # Pass Type
        tk.Label(main_frame, text="Pass Type:", font=('Arial', 11), bg='white').pack(anchor='w')
        pass_type_var = tk.StringVar(value=values[7])
        pass_type_combo = ttk.Combobox(main_frame, textvariable=pass_type_var, values=self.get_pass_types(), font=('Arial', 11))
        pass_type_combo.pack(fill=tk.X, pady=(0, 10))

        # Amount
        tk.Label(main_frame, text="Amount:", font=('Arial', 11), bg='white').pack(anchor='w')
        amount_var = tk.StringVar(value=values[4])
        amount_entry = tk.Entry(main_frame, textvariable=amount_var, font=('Arial', 11))
        amount_entry.pack(fill=tk.X, pady=(0, 10))

        # Booked Date
        tk.Label(main_frame, text="Booked Date:", font=('Arial', 11), bg='white').pack(anchor='w')
        booked_date_entry = DateEntry(main_frame, font=('Arial', 11), width=18, date_pattern='MM/dd/yyyy')
        try:
            date_obj = datetime.strptime(values[5], '%m/%d/%Y')
            booked_date_entry.set_date(date_obj)
        except ValueError:
            pass
        booked_date_entry.pack(fill=tk.X, pady=(0, 10))

        # Purchased Date
        tk.Label(main_frame, text="Purchased Date:", font=('Arial', 11), bg='white').pack(anchor='w')
        purchased_date_entry = DateEntry(main_frame, font=('Arial', 11), width=18, date_pattern='MM/dd/yyyy')
        try:
            date_obj = datetime.strptime(values[6], '%m/%d/%Y')
            purchased_date_entry.set_date(date_obj)
        except ValueError:
            pass
        purchased_date_entry.pack(fill=tk.X, pady=(0, 10))

        def update_amount(*args):
            try:
                pass_type = pass_type_var.get()
                quantity = int(quantity_var.get())
                if pass_type and quantity > 0:
                    price = self.get_price_for_pass(pass_type)
                    total = price * quantity
                    amount_var.set(f"{total:.2f}")
            except ValueError:
                amount_var.set("")

        # Bind the update function to both pass type and quantity changes
        pass_type_combo.bind('<<ComboboxSelected>>', update_amount)
        quantity_entry.bind('<KeyRelease>', update_amount)

        def save_edit():
            # Get values from the entries
            name = name_var.get().strip()
            email = email_var.get().strip()
            quantity = quantity_var.get().strip()
            amount = amount_var.get().strip()
            pass_type = pass_type_var.get().strip()
            
            try:
                booked_date = booked_date_entry.get_date().strftime('%Y-%m-%d')
                purchased_date = purchased_date_entry.get_date().strftime('%Y-%m-%d')
            except AttributeError:
                messagebox.showerror("Error", "Invalid date format!")
                return

            # Validate fields
            if not all([name, quantity, amount, pass_type, booked_date, purchased_date]):
                messagebox.showerror("Error", "Name, Quantity, Amount, Pass Type, Booked Date, and Purchased Date are required!")
                return

            try:
                conn = sqlite3.connect('funpass.db')
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE customers 
                    SET name=?, email=?, quantity=?, amount=?, 
                        booked_date=?, purchased_date=?, pass_type=?
                    WHERE ticket_id=?
                ''', (name, email, int(quantity), float(amount), 
                     booked_date, purchased_date, pass_type, ticket_id_var.get()))
                conn.commit()
                conn.close()
                dialog.destroy()
                self.load_customers_data()
                messagebox.showinfo("Success", "Customer updated successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {str(e)}")

        # Button frame for Save and Cancel
        button_frame = tk.Frame(main_frame, bg='white')
        button_frame.pack(pady=20)

        # Save button 
        save_btn = tk.Button(button_frame, text="Save", command=save_edit, 
                            bg='#4CAF50', fg='white', width=10)
        save_btn.pack(side=tk.LEFT, padx=5)

        # Cancel button
        cancel_btn = tk.Button(button_frame, text="Cancel", command=dialog.destroy,
                              bg='#f44336', fg='white', width=10) 
        cancel_btn.pack(side=tk.LEFT, padx=5)

    def delete_customer(self):
        selected = self.customers_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a customer to delete.")
            return
        values = self.customers_tree.item(selected[0])['values']
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this customer?"):
            try:
                conn = sqlite3.connect('funpass.db')
                cursor = conn.cursor()
                cursor.execute('DELETE FROM customers WHERE ticket_id=? AND employee_id=?', (values[0], self.employee_id))
                conn.commit()
                conn.close()
                self.load_customers_data()
                messagebox.showinfo("Success", "Customer deleted!")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def view_receipt(self):
        selected = self.customers_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a customer to view the receipt.")
            return
        values = self.customers_tree.item(selected[0])['values']
        if len(values) >= 8:
            ticket_id, name, email, quantity, amount, booked_date, purchased_date, pass_type = values[:8]
            self.print_ticket(ticket_id, name, email, quantity, amount, booked_date, purchased_date, pass_type)

    def generate_ticket_id(self):
        import random, string
        return 'F' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

    def get_pass_types(self):
        conn = sqlite3.connect('funpass.db')
        cursor = conn.cursor()
        cursor.execute('SELECT pass_type FROM pricing')
        pass_types = [row[0] for row in cursor.fetchall()]
        conn.close()
        return pass_types

    def get_price_for_pass(self, pass_type):
        conn = sqlite3.connect('funpass.db')
        cursor = conn.cursor()
        cursor.execute('SELECT price FROM pricing WHERE pass_type=?', (pass_type,))
        row = cursor.fetchone()
        conn.close()
        return float(row[0]) if row else 0.0

    def print_ticket(self, ticket_id, name, email, quantity, amount, booked_date, purchased_date, pass_type):
        print_win = tk.Toplevel(self.root)
        print_win.title("Booking Receipt")
        print_win.geometry("400x600")
        print_win.configure(bg='white')
        print_win.transient(self.root)
        print_win.lift()

        # Center the window on the screen
        print_win.update_idletasks()
        w = 400
        h = 600
        x = (print_win.winfo_screenwidth() // 2) - (w // 2)
        y = (print_win.winfo_screenheight() // 2) - (h // 2)
        print_win.geometry(f"{w}x{h}+{x}+{y}")

        # Main frame for centering
        main_frame = tk.Frame(print_win, bg='white')
        main_frame.pack(expand=True, fill=tk.BOTH)

        # Logo
        try:
            logo_path = "FunPass__1_-removebg-preview.png"
            logo_img = Image.open(logo_path)
            logo_width = 90
            aspect_ratio = logo_img.height / logo_img.width
            logo_height = int(logo_width * aspect_ratio)
            logo_img = logo_img.resize((logo_width, logo_height))
            self.logo_image = ImageTk.PhotoImage(logo_img)
            logo_label = tk.Label(main_frame, image=self.logo_image, bg='white')
            logo_label.pack(pady=(18, 4))
        except Exception:
            tk.Label(main_frame, text="FunPass", font=('Arial', 18, 'bold'), bg='white', fg='#4CAF50').pack(pady=(18, 4))

        tk.Label(main_frame, text="FunPass: Amusement Park Ticketing System", font=('Arial', 10, 'italic'), fg='#6b7280', bg='white', anchor='center', justify='center').pack(pady=(0, 4))
        tk.Label(main_frame, text="FunPass Booking Receipt", font=('Arial', 15, 'bold'), bg='white', anchor='center', justify='center').pack(pady=(0, 10))

        # Booking Details
        details_frame = tk.LabelFrame(
            main_frame, text="Booking Details",
            font=('Arial', 10, 'bold'), bg='white', fg='black',
            padx=10, pady=10, relief='solid', bd=1, labelanchor='n'
        )
        details_frame.pack(padx=30, pady=(0, 12), anchor='n')  

        fields = [
            ("Ticket ID:", ticket_id),
            ("Customer Name:", name),
            ("Email:", email),
            ("Ticket Type:", pass_type),
            ("Quantity:", quantity),
            ("Unit Price:", f"₱{float(amount)/int(quantity):,.2f}" if quantity else f"₱{amount}"),
            ("Total Amount:", f"₱{float(amount):,.2f}"),
            ("Booked Date:", booked_date),
            ("Purchased Date:", purchased_date)
        ]
        for i, (label, value) in enumerate(fields):
            row = tk.Frame(details_frame, bg='white')
            row.pack(fill=tk.X, pady=2, anchor='w')  
            tk.Label(row, text=label, font=('Arial', 10, 'bold'), bg='white', anchor='w', width=14, justify='left').pack(side=tk.LEFT)
            tk.Label(row, text=str(value), font=('Arial', 10), bg='white', anchor='w', justify='left').pack(side=tk.LEFT, padx=(8, 0))

        # Terms & Conditions
        terms_frame = tk.LabelFrame(
            main_frame, text="Terms & Conditions",
            font=('Arial', 10, 'bold'), bg='white', fg='black',
            padx=10, pady=6, relief='solid', bd=1, labelanchor='n'
        )
        terms_frame.pack(padx=30, pady=(0, 12), anchor='center')
        terms = [
            "Tickets are valid only for the booked date",
            "No refunds for unused tickets",
            "Please present this receipt at the entrance",
            "Subject to park rules and regulations"
        ]
        for term in terms:
            tk.Label(terms_frame, text=f"• {term}", font=('Arial', 9), bg='white', anchor='w', justify='left').pack(anchor='w', pady=0)

        tk.Button(main_frame, text="Close", command=print_win.destroy, bg='white', font=('Arial', 10), relief='groove').pack(pady=8)
    
    def send_ticket_email(self, to_email, ticket_id, name, email, quantity, amount, booked_date, purchased_date, pass_type):
        # Configure your SMTP server details here
        SMTP_SERVER = 'smtp.gmail.com'
        SMTP_PORT = 587
        SMTP_USER = 'funpasstothemagicalpark@gmail.com'  
        SMTP_PASS = 'qauf qaub sexo hefs'   # google app password

        subject = f"Your FunPass Booking Receipt (Ticket ID: {ticket_id})"
        body = f"""\
Hello {name},

Thank you for your purchase! Here are your ticket details:

Ticket ID: {ticket_id}
Customer Name: {name}
Email: {email}
Ticket Type: {pass_type}
Quantity: {quantity}
Unit Price: ₱{float(amount)/int(quantity):,.2f}
Total Amount: ₱{float(amount):,.2f}
Booked Date: {booked_date}
Purchased Date: {purchased_date}

Please present this receipt at the entrance.
Enjoy your visit!

Best regards,
FunPass: Amusement Park Ticketing System
"""

        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = SMTP_USER
        msg['To'] = to_email
        msg.set_content(body)

        try:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASS)
                server.send_message(msg)
            print(f"Ticket sent to {to_email}")
        except Exception as e:
            print(f"Failed to send email: {e}")

    def send_cancellation_pending_email(self, to_email, name, ticket_id):
        SMTP_SERVER = 'smtp.gmail.com'
        SMTP_PORT = 587
        SMTP_USER = 'funpasstothemagicalpark@gmail.com'
        SMTP_PASS = 'qauf qaub sexo hefs'

        subject = f"FunPass Cancellation Request Received (Ticket ID: {ticket_id})"
        body = f"""\
Hello {name},

We have received your cancellation request for Ticket ID {ticket_id}.
Your request is now pending and being reviewed by our team.

You will receive another email once your request is approved or rejected.
Thank you for using FunPass!

Best regards,
FunPass: Amusement Park Ticketing System
"""

        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = SMTP_USER
        msg['To'] = to_email
        msg.set_content(body)

        try:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASS)
                server.send_message(msg)
            print(f"Pending cancellation email sent to {to_email}")
        except Exception as e:
            print(f"Failed to send pending cancellation email: {e}")

    def show_cancellations(self):
        import customtkinter as ctk
        self.clear_content()
        self.set_active_sidebar('❌  Cancellations & Refunds')

        # --- Main Card Container ---
        card_frame = ctk.CTkFrame(self.content_frame, fg_color="#FFFFFF", corner_radius=0)
        card_frame.pack(fill="both", expand=True, padx=30, pady=30)

        # --- Header Block ---
        header_row = ctk.CTkFrame(card_frame, fg_color="#FFFFFF")
        header_row.pack(fill="x", pady=(10, 0), anchor="w")
        header_row.grid_columnconfigure(0, weight=1)
        cancel_title = ctk.CTkLabel(header_row, text="Cancellations and Refunds", font=("Segoe UI", 22, "bold"), text_color="#22223B")
        cancel_title.grid(row=0, column=0, padx=15, sticky="w")
        cancel_subtitle = ctk.CTkLabel(header_row, text="View and Manage Customers Submitted Refund Requests", font=("Segoe UI", 15), text_color="#6b7280")
        cancel_subtitle.grid(row=1, column=0, padx=15, pady=10, sticky="w")

        # --- Controls Bar ---
        controls_bar = ctk.CTkFrame(card_frame, fg_color="#F0E7D9", corner_radius=0, height=50)
        controls_bar.pack(fill="x", padx=10, pady=(0, 15))
        controls_bar.grid_columnconfigure(0, weight=1)
        controls_bar.grid_columnconfigure(1, weight=0)
        controls_bar.grid_columnconfigure(2, weight=0)
        controls_bar.grid_columnconfigure(3, weight=0)

        # Search Entry
        self.cancel_search_var = ctk.StringVar()
        self.cancel_search_var.trace('w', self.search_cancellations)
        search_entry = ctk.CTkEntry(
            controls_bar,
            textvariable=self.cancel_search_var,
            placeholder_text="Search cancellation...",
            width=220,
            height=36,
            font=("Segoe UI", 12),
            fg_color="#fff",
            border_color="#cccccc",
            border_width=2
        )
        search_entry.grid(row=0, column=0, padx=(16, 8), pady=10, sticky="w")

        # Sort Combobox (all columns)
        cancel_sort_options_list = [
            ("Ticket ID (A-Z)", 0, False), ("Ticket ID (Z-A)", 0, True),
            ("Name (A-Z)", 1, False), ("Name (Z-A)", 1, True),
            ("Email (A-Z)", 2, False), ("Email (Z-A)", 2, True),
            ("Pass Type (A-Z)", 3, False), ("Pass Type (Z-A)", 3, True),
            ("Reason (A-Z)", 4, False), ("Reason (Z-A)", 4, True),
            ("Quantity (Lowest)", 5, False), ("Quantity (Highest)", 5, True),
            ("Amount (Lowest)", 6, False), ("Amount (Highest)", 6, True),
            ("Booked Date (Newest)", 7, True), ("Booked Date (Oldest)", 7, False),
            ("Purchased Date (Newest)", 8, True), ("Purchased Date (Oldest)", 8, False),
            ("Status (A-Z)", 9, False), ("Status (Z-A)", 9, True)
        ]
        sort_options = ctk.CTkComboBox(
            controls_bar,
            values=[opt[0] for opt in cancel_sort_options_list],
            width=200,
            font=("Segoe UI", 12),
            dropdown_font=("Segoe UI", 12),
            state="readonly",
            fg_color="#fff",
            border_color="#cccccc",
            border_width=2
        )
        sort_options.set("Name (A-Z)")
        sort_options.grid(row=0, column=1, padx=(0, 8), pady=10)
        sort_options.configure(command=lambda value: self.sort_cancellations(value))
        self._cancel_sort_options = cancel_sort_options_list

        # Add Cancellation Button 
        add_btn = ctk.CTkButton(
            controls_bar, text="Add Cancellation", width=140, height=36, fg_color="#E0E0E0", text_color="#4CAF50", hover_color="#C8E6C9",
            font=("Segoe UI", 12, "bold"), corner_radius=10, command=self.add_cancellation_dialog
        )
        add_btn.grid(row=0, column=2, padx=(0, 8), pady=10)

        # Delete Button
        delete_btn = ctk.CTkButton(
            controls_bar, text="Delete", width=90, height=36, fg_color="#E0E0E0", text_color="#f44336", hover_color="#FFCDD2",
            font=("Segoe UI", 12, "bold"), corner_radius=10, command=self.delete_cancellation
        )
        delete_btn.grid(row=0, column=3, padx=(0, 12), pady=10)

        # Table Frame
        table_card = ctk.CTkFrame(card_frame, fg_color="#fff", corner_radius=18)
        table_card.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        table_card.grid_rowconfigure(0, weight=1)
        table_card.grid_columnconfigure(0, weight=1)

        # Scrollbars
        yscroll = ctk.CTkScrollbar(table_card, orientation="vertical")
        xscroll = ctk.CTkScrollbar(table_card, orientation="horizontal")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")

        # Table (ttk.Treeview inside CTkFrame)
        import tkinter.ttk as ttk
        columns = ('Ticket ID', 'Name', 'Email', 'Pass Type', 'Reason', 'Quantity', 'Amount', 'Booked Date', 'Purchased Date', 'Status')
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Treeview', font=('Segoe UI', 11), rowheight=32, background='#FFFFFF', fieldbackground='#FFFFFF', borderwidth=0)
        style.configure('Treeview.Heading', font=('Segoe UI', 11, 'bold'), background='#E0E0E0', foreground='#9A4E62', borderwidth=0)
        style.layout('Treeview', [('Treeview.treearea', {'sticky': 'nswe'})])
        self.cancellations_tree = ttk.Treeview(
            table_card, columns=columns, show='headings', style='Treeview',
            yscrollcommand=yscroll.set, xscrollcommand=xscroll.set
        )
        self.cancellations_tree.grid(row=0, column=0, sticky='nsew')
        yscroll.configure(command=self.cancellations_tree.yview)
        xscroll.configure(command=self.cancellations_tree.xview)
        column_widths = {
            'Ticket ID': 100,
            'Name': 150,
            'Email': 200,
            'Pass Type': 120,
            'Reason': 200,
            'Quantity': 80,
            'Amount': 100,
            'Booked Date': 120,
            'Purchased Date': 120,
            'Status': 100
        }
        for col in columns:
            self.cancellations_tree.heading(col, text=col)
            width = column_widths.get(col, 120)
            self.cancellations_tree.column(col, width=width, anchor='w')
        def clear_selection_on_click(event):
            region = self.cancellations_tree.identify("region", event.x, event.y)
            if region == "nothing":
                self.cancellations_tree.selection_remove(self.cancellations_tree.selection())
        self.cancellations_tree.bind("<Button-1>", clear_selection_on_click, add="+")
        self.load_cancellations_data()

    def add_cancellation_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Cancellation Request")
        dialog.geometry("500x650")
        dialog.configure(bg='white')
        main_frame = tk.Frame(dialog, bg='white', padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        # Ticket ID
        tk.Label(main_frame, text="Ticket ID:", font=('Arial', 11), bg='white').pack(anchor='w')
        ticket_id_entry = tk.Entry(main_frame, font=('Arial', 11))
        ticket_id_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Name
        tk.Label(main_frame, text="Name:", font=('Arial', 11), bg='white').pack(anchor='w')
        name_entry = tk.Entry(main_frame, font=('Arial', 11))
        name_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Email (optional)
        tk.Label(main_frame, text="Email:", font=('Arial', 11), bg='white').pack(anchor='w')
        email_entry = tk.Entry(main_frame, font=('Arial', 11))
        email_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Reasons
        tk.Label(main_frame, text="Reasons:", font=('Arial', 11), bg='white').pack(anchor='w')
        reasons_entry = tk.Entry(main_frame, font=('Arial', 11))
        reasons_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Quantity
        tk.Label(main_frame, text="Quantity:", font=('Arial', 11), bg='white').pack(anchor='w')
        quantity_entry = tk.Entry(main_frame, font=('Arial', 11))
        quantity_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Amount
        tk.Label(main_frame, text="Amount:", font=('Arial', 11), bg='white').pack(anchor='w')
        amount_entry = tk.Entry(main_frame, font=('Arial', 11))
        amount_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Booked Date
        tk.Label(main_frame, text="Booked Date:", font=('Arial', 11), bg='white').pack(anchor='w')
        booked_date_entry = DateEntry(main_frame, font=('Arial', 11), width=18, date_pattern='MM/dd/yyyy')
        booked_date_entry.pack(fill=tk.X, pady=(0, 10))
       
        # Purchased Date
        tk.Label(main_frame, text="Purchased Date:", font=('Arial', 11), bg='white').pack(anchor='w')
        purchased_date_entry = DateEntry(main_frame, font=('Arial', 11), width=18, date_pattern='MM/dd/yyyy')
        purchased_date_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Pass Type 
        tk.Label(main_frame, text="Pass Type:", font=('Arial', 11), bg='white').pack(anchor='w')
        pass_types = self.get_pass_types()
        pass_type_combo = ttk.Combobox(main_frame, values=pass_types, font=('Arial', 11), state="readonly")
        pass_type_combo.pack(fill=tk.X, pady=(0, 10))
        if pass_types:
            pass_type_combo.set(pass_types[0])  # Set default to "Express Pass"
            
        def save_cancellation():
            ticket_id = ticket_id_entry.get().strip()
            name = name_entry.get().strip()
            email = email_entry.get().strip()
            reasons = reasons_entry.get().strip()
            quantity = quantity_entry.get().strip()
            amount = amount_entry.get().strip()
            pass_type = pass_type_combo.get().strip()

            # 1. Check ticket exists
            conn = sqlite3.connect('funpass.db')
            cursor = conn.cursor()
            cursor.execute('SELECT name, email, quantity, amount, pass_type FROM customers WHERE ticket_id=?', (ticket_id,))
            customer = cursor.fetchone()
            if not customer:
                messagebox.showerror("Error", "Ticket ID does not exist!")
                conn.close()
                return

            # 2. Check for duplicate cancellation
            cursor.execute('SELECT 1 FROM cancellations WHERE ticket_id=?', (ticket_id,))
            if cursor.fetchone():
                messagebox.showerror("Error", "A cancellation for this Ticket ID already exists!")
                conn.close()
                return

            # 3. Validate details match
            if (name != customer[0] or email != customer[1] or int(quantity) != customer[2] or float(amount) != customer[3] or pass_type != customer[4]):
                messagebox.showerror("Error", "Cancellation details do not match the original purchase!")
                conn.close()
                return
            
            # Format dates correctly
            try:
                booked_date = booked_date_entry.get_date().strftime('%Y-%m-%d')
                purchased_date = purchased_date_entry.get_date().strftime('%Y-%m-%d')
            except AttributeError:
                messagebox.showerror("Error", "Invalid date format!")
                return

            pass_type = pass_type_combo.get().strip()

            # Email is optional now
            if not (ticket_id and name and reasons and quantity and amount and booked_date and purchased_date and pass_type):
                messagebox.showerror("Error", "All fields except Email are required!")
                return

            try:
                conn = sqlite3.connect('funpass.db')
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO cancellations 
                    (ticket_id, name, email, reasons, quantity, amount, booked_date, purchased_date, pass_type, status) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    ticket_id, name, email, reasons, 
                    int(quantity), float(amount), 
                    booked_date, purchased_date,
                    pass_type, 'Pending'
                ))
                conn.commit()
                conn.close()
                # Send Email
                if email:
                    self.send_cancellation_pending_email(email, name, ticket_id)
                
                dialog.destroy() # Close the dialog after saving
                self.load_cancellations_data()
                messagebox.showinfo("Success", "Cancellation request added!")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {str(e)}")

        tk.Button(main_frame, text="Save", command=save_cancellation, bg='#4CAF50', fg='white').pack(pady=10)
        tk.Button(main_frame, text="Cancel", command=dialog.destroy, bg='#f44336', fg='white').pack()

    def show_pricing(self):
        import customtkinter as ctk
        self.clear_content()
        self.set_active_sidebar('💳  Pricing')

        # Main Card Container 
        card_frame = ctk.CTkFrame(self.content_frame, fg_color="#F0E7D9", corner_radius=0, border_width=0, border_color="#e0e0e0")
        card_frame.pack(fill="both", expand=True, padx=0, pady=0)

        # Header Block 
        header_row = ctk.CTkFrame(card_frame, fg_color="#F0E7D9")
        header_row.pack(fill="x", pady=(18, 0), anchor="w")
        header_row.grid_columnconfigure(0, weight=1)
        pricing_title = ctk.CTkLabel(header_row, text="Pass Type Pricing", font=("Segoe UI", 26, "bold"), text_color="#22223B")
        pricing_title.grid(row=0, column=0, padx=18, sticky="w")
        pricing_subtitle = ctk.CTkLabel(header_row, text="View Only - Pricing is managed by Admin", font=("Segoe UI", 15), text_color="#8a8a8a")
        pricing_subtitle.grid(row=1, column=0, padx=18, pady=(8, 18), sticky="w")
        # Divider line
        divider = ctk.CTkFrame(card_frame, fg_color="#F0E7D9", height=2)
        divider.pack(fill="x", padx=18, pady=(0, 18))

        # Last Updated Label 
        import time
        last_updated = time.strftime('%m/%d/%Y %H:%M:%S')
        price_update_label = ctk.CTkLabel(header_row, text=f"Last updated: {last_updated}", font=("Arial", 10), text_color="#4CAF50")
        price_update_label.grid(row=2, column=0, padx=18, sticky="w")

        # Pricing Table Card 
        table_card = ctk.CTkFrame(card_frame, fg_color="#fff", corner_radius=18, border_width=1, border_color="#e0e0e0", width=1200, height=600)
        table_card.pack(pady=(0, 20))

        # Non-scrollable area for pricing rows
        pricing_rows_container = ctk.CTkFrame(table_card, fg_color="#fff", width=1200, height=600)
        pricing_rows_container.pack(expand=True, pady=10)

        # Load pricing data from the database
        conn = sqlite3.connect('funpass.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM pricing')
        prices = cursor.fetchall()
        conn.close()

        # Arrange price frames in a grid (2 per row)
        num_cols = 2
        for idx, (pass_type, current_price) in enumerate(prices):
            row_idx = idx // num_cols
            col_idx = idx % num_cols
            price_frame_card = ctk.CTkFrame(pricing_rows_container, fg_color="#f7f7fa", corner_radius=18, border_width=2, border_color="#e0e0e0", width=400, height=120)
            price_frame_card.grid(row=row_idx, column=col_idx, padx=48, pady=32, sticky="n")
            price_frame_card.pack_propagate(False)
            # Centered horizontal row inside the card
            row_inner = ctk.CTkFrame(price_frame_card, fg_color="#f7f7fa")
            row_inner.pack(expand=True)
            row_inner.pack_propagate(False)
            label = ctk.CTkLabel(row_inner, text=pass_type, font=("Arial", 20, "bold"), text_color="#22223B", anchor="center")
            currency_label = ctk.CTkLabel(row_inner, text="₱", font=("Arial", 20, "bold"), text_color="#22223B")
            price_value_label = ctk.CTkLabel(row_inner, text=f"{float(current_price):,.2f}", font=("Arial", 20), text_color="#22223B", anchor="center")
            label.grid(row=0, column=0, padx=(0, 12), pady=20, sticky="ew")
            currency_label.grid(row=0, column=1, padx=(0, 8), pady=20)
            price_value_label.grid(row=0, column=2, pady=20)
            row_inner.grid_columnconfigure(0, weight=1)
            row_inner.grid_columnconfigure(1, weight=0)
            row_inner.grid_columnconfigure(2, weight=1)
        if len(prices) % num_cols == 1:
            pricing_rows_container.grid_columnconfigure(1, weight=1)


    def get_all_prices(self):
        # Get all prices from database
        conn = sqlite3.connect('funpass.db')
        cursor = conn.cursor()
        cursor.execute('SELECT pass_type, price FROM pricing')
        prices = cursor.fetchall()
        conn.close()
        return prices

    def refresh_prices(self, event=None):
        print("Price update event received")  # Debug print
        
        # Clear price cache to force fresh data
        self._price_cache.clear()

        # Refresh pricing display if it's currently shown
        if hasattr(self, 'current_price_frame') and self.current_price_frame and self.current_price_frame.winfo_exists():
            self.show_pricing()

        # Update any open dialogs that show prices
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Toplevel):
                try:
                    self.update_dialog_prices(widget)
                except Exception as e:
                    print(f"Error updating dialog prices: {e}")  # Debug print
                    continue

        # Update main displays
        self.update_displayed_prices()
        print("Price refresh completed")  # Debug print

    def update_dialog_prices(self, dialog):
        """Update prices in an open dialog"""
        quantity_entry = None
        pass_type_combo = None
        amount_var = None

        # Find the relevant widgets in the dialog
        for child in dialog.winfo_children():
            if isinstance(child, tk.Frame):
                for subchild in child.winfo_children():
                    if isinstance(subchild, tk.Entry) and subchild.winfo_name() == 'quantity_entry':
                        quantity_entry = subchild
                    elif isinstance(subchild, ttk.Combobox) and subchild.winfo_name() == 'pass_type_combo':
                        pass_type_combo = subchild
                    elif isinstance(subchild, tk.Entry) and subchild.winfo_name() == 'amount_entry':
                        amount_var = subchild.cget('textvariable')

        # Update amount if we have all necessary widgets
        if quantity_entry and pass_type_combo and amount_var:
            try:
                quantity = int(quantity_entry.get())
                pass_type = pass_type_combo.get()
                price = self.get_price_for_pass(pass_type)
                amount = price * quantity
                self.root.globalgetvar(amount_var).set(f"{amount:.2f}")
                print(f"Updated price in dialog for {pass_type}: {amount:.2f}")  # Debug print
            except (ValueError, AttributeError) as e:
                print(f"Error updating dialog amount: {e}")  # Debug print
                pass

    def update_displayed_prices(self):
        """Update all price displays in the interface"""
        # Update dashboard if it exists
        if hasattr(self, 'content_frame'):
            self.show_dashboard()
            print("Dashboard prices updated")  # Debug print

        # Update customer view if it exists
        if hasattr(self, 'customers_tree'):
            self.load_customers_data()
            print("Customer view prices updated")  # Debug print

        # Update pricing view if it exists
        if hasattr(self, 'current_price_frame') and self.current_price_frame and self.current_price_frame.winfo_exists():
            self.show_pricing()
            print("Pricing view updated")  # Debug print

    def logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.root.destroy()
            from login import show_login
            show_login()

    def search_cancellations(self, *args):
        search_text = self.cancel_search_var.get().lower()
        for item in self.cancellations_tree.get_children():
            self.cancellations_tree.delete(item)
        conn = sqlite3.connect('funpass.db')
        cursor = conn.cursor()
        # Only show cancellations for tickets sold by this employee
        cursor.execute('''
            SELECT c.ticket_id, c.name, c.email, c.pass_type, c.reasons, c.quantity, c.amount,
                   strftime('%m/%d/%Y', c.booked_date) as booked_date,
                   strftime('%m/%d/%Y', c.purchased_date) as purchased_date,
                   c.status
            FROM cancellations c
            INNER JOIN customers cu ON c.ticket_id = cu.ticket_id
            WHERE cu.employee_id = ?
        ''', (self.employee_id,))
        cancellations = cursor.fetchall()
        conn.close()
        for cancellation in cancellations:
            searchable_fields = [
                str(cancellation[0]),  # ticket_id
                str(cancellation[1]),  # name
                str(cancellation[2]),  # email
                str(cancellation[9])   # status
            ]
            if any(search_text in field.lower() for field in searchable_fields):
                self.cancellations_tree.insert('', tk.END, values=cancellation)

    def delete_cancellation(self):
        selected_item = self.cancellations_tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a cancellation to delete.")
            return
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this cancellation record?"):
            ticket_id = self.cancellations_tree.item(selected_item[0])['values'][0]
            conn = sqlite3.connect('funpass.db')
            cursor = conn.cursor()
            cursor.execute('DELETE FROM cancellations WHERE ticket_id = ?', (ticket_id,))
            conn.commit()
            conn.close()
            self.cancellations_tree.delete(selected_item[0])
            messagebox.showinfo("Success", "Cancellation record deleted successfully!")

    def sort_cancellations(self, sort_option):
        items = []
        for item in self.cancellations_tree.get_children():
            values = self.cancellations_tree.item(item)['values']
            items.append(values)
        for label, idx, reverse in self._cancel_sort_options:
            if label == sort_option:
            # Quantity, Amount
                if idx in [5, 6]:
                    items.sort(key=lambda x: float(str(x[idx]).replace('₱','').replace(',','')), reverse=reverse)
            # Booked Date, Purchased Date
                elif idx in [7, 8]:
                    from datetime import datetime
                    def parse_date(val):
                        try:
                            return datetime.strptime(val, '%m/%d/%Y')
                        except Exception:
                            return datetime.min
                    items.sort(key=lambda x: parse_date(x[idx]), reverse=reverse)
                else:
                    items.sort(key=lambda x: str(x[idx]).lower(), reverse=reverse)
                break
        for item in self.cancellations_tree.get_children():
            self.cancellations_tree.delete(item)
        for item in items:
            self.cancellations_tree.insert('', tk.END, values=item)

    def load_cancellations_data(self):
        for item in self.cancellations_tree.get_children():
            self.cancellations_tree.delete(item)
        conn = sqlite3.connect('funpass.db')
        cursor = conn.cursor()
        # Only show cancellations for tickets sold by this employee
        cursor.execute('''
            SELECT c.ticket_id, c.name, c.email, c.pass_type, c.reasons, c.quantity, c.amount,
                   strftime('%m/%d/%Y', c.booked_date) as booked_date,
                   strftime('%m/%d/%Y', c.purchased_date) as purchased_date,
                   c.status
            FROM cancellations c
            INNER JOIN customers cu ON c.ticket_id = cu.ticket_id
            WHERE cu.employee_id = ?
            ORDER BY c.id DESC
        ''', (self.employee_id,))
        cancellations = cursor.fetchall()
        conn.close()
        for cancellation in cancellations:
            self.cancellations_tree.insert('', tk.END, values=cancellation)

if __name__ == "__main__":
    root = tk.Tk()
    create_database()
    EmployeeDashboard(root)
    root.mainloop()