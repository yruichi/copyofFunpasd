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
import smtplib
from email.message import EmailMessage

# database setup
def create_database():
    conn = sqlite3.connect('funpass.db')
    cursor = conn.cursor()

    # to create admin table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    ''')

    # to insert default admin if not exists
    cursor.execute('INSERT OR IGNORE INTO admin (username, password) VALUES (?, ?)',
                  ('admin', 'admin123'))

    # to create employees table
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

    # to create customers table
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

    # to create cancellations table
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

    # to create pricing table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pricing (
            pass_type TEXT PRIMARY KEY,
            price REAL NOT NULL
        )
    ''')

    # to insert or update default prices
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
        # Bind to price update event at root level
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
        sidebar = tk.Frame(self.root, bg='#ECCD93', width=350)
        sidebar.grid(row=0, column=0, sticky="ns")
        sidebar.grid_propagate(False)
        try:
            logo_path = "FunPass__1_-removebg-preview.png"
            logo_img = Image.open(logo_path)
            logo_width = 200
            aspect_ratio = logo_img.height / logo_img.width
            logo_height = int(logo_width * aspect_ratio)
            logo_img = logo_img.resize((logo_width, logo_height))
            self.sidebar_logo = ImageTk.PhotoImage(logo_img)
            logo_label = tk.Label(sidebar, image=self.sidebar_logo, bg='#ECCD93')
            logo_label.pack(pady=20)
        except Exception as e:
            print(f"Error loading sidebar logo: {e}")
        buttons = [
            ("Dashboard", self.show_dashboard),
            ("Rides", self.show_rides),
            ("Customers", self.show_customers),
            ("Cancellations & Refunds", self.show_cancellations),
            ("Pricing", self.show_pricing),
            ("Logout", self.logout)
        ]
        for text, command in buttons:
            btn = tk.Button(sidebar, text=text, command=command,
                          bg='#ECCD93', fg='black', font=('Arial', 10, 'bold'),
                          bd=0, pady=15, width=20)
            btn.pack(pady=2)
            btn.bind('<Enter>', lambda e, btn=btn: btn.configure(bg='#ECCD93'))
            btn.bind('<Leave>', lambda e, btn=btn: btn.configure(bg='#ECCD93'))

    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def show_dashboard(self):
        self.clear_content()
        # Title: Dashboard, styled to match AdminDashboard (font size 20, bold, maroon, with padding)
        dashboard_title = tk.Label(self.content_frame, text="Dashboard", font=('Segoe UI', 20, 'bold'), bg='white', anchor='w', fg='#22223B')
        dashboard_title.pack(pady=(20, 0), padx=30, anchor='w')
        # Subtitle: font size 15, gray, with left padding
        dashboard_subtitle = tk.Label(self.content_frame, text="Your Sales and Ticket Overview", font=('Segoe UI', 15), fg='#6b7280', bg='white', anchor='w')
        dashboard_subtitle.pack(pady=(0, 10), padx=30, anchor='w')

        # Top bar with date and time, inside a modern card (white background, rounded look)
        top_bar_card = tk.Frame(self.content_frame, bg='#FFFFFF', bd=0, highlightthickness=0)
        top_bar_card.pack(fill=tk.X, padx=30, pady=(20, 0))
        # Time/date on the right
        time_frame = tk.Frame(top_bar_card, bg='#FFFFFF')
        time_frame.pack(side=tk.RIGHT, padx=25, pady=20)
        # Date label: font size 15, gray
        self.date_label = tk.Label(time_frame, font=('Segoe UI', 15, 'normal'), bg='#FFFFFF', fg='#6b7280')
        self.date_label.pack(side=tk.TOP, anchor='e')
        # Time label: font size 15, bold, maroon
        self.time_label = tk.Label(time_frame, font=('Segoe UI', 15, 'bold'), bg='#FFFFFF', fg='#22223B')
        self.time_label.pack(side=tk.TOP, anchor='e', pady=0)
        # Status label: green, left side
        status_label = tk.Label(top_bar_card, text="🟢 System Online", font=('Segoe UI', 15, 'normal'), bg='#FFFFFF', fg='#4CAF50')
        status_label.pack(side=tk.LEFT, padx=20, pady=20, anchor='w')
        self.update_time()

        # Overview Card: white background, rounded look, modern padding
        overview_card = tk.Frame(self.content_frame, bg='#FFFFFF', bd=0, highlightthickness=0)
        overview_card.pack(fill=tk.X, padx=30, pady=20)
        # Overview title: font size 15, bold
        tk.Label(overview_card, text='Overview', font=('Segoe UI', 15, 'bold'), bg='#FFFFFF', fg='#22223B', anchor='w').pack(anchor='w', pady=(10, 0), padx=20)
        # Stats grid: 2 columns, modern padding
        stats_grid = tk.Frame(overview_card, bg='#FFFFFF')
        stats_grid.pack(fill='x', padx=20, pady=(10, 10))
        for i in range(2):
            stats_grid.grid_columnconfigure(i, weight=1)

        conn = sqlite3.connect('funpass.db')
        cursor = conn.cursor()
        
        # Total all-time sales for this employee
        cursor.execute('''
            SELECT IFNULL(SUM(amount), 0)
            FROM customers
            WHERE employee_id=?
        ''', (self.employee_id,))
        total_sales = cursor.fetchone()[0] or 0

        cursor.execute('''
            SELECT IFNULL(SUM(amount), 0)
            FROM cancellations
            WHERE status='Approved'
            AND ticket_id IN (
                SELECT ticket_id FROM customers WHERE employee_id=?
            )
        ''', (self.employee_id,))
        cancelled_sales = cursor.fetchone()[0] or 0

        net_sales = total_sales - cancelled_sales
        
        # Total this month's sales for this employee
        cursor.execute('''
            SELECT SUM(amount) 
            FROM customers 
            WHERE employee_id=? 
            AND strftime('%Y-%m', purchased_date) = strftime('%Y-%m', 'now')
        ''', (self.employee_id,))
        monthly_sales = cursor.fetchone()[0] or 0
        
        # Total tickets sold for this employee
        cursor.execute('SELECT SUM(quantity) FROM customers WHERE employee_id=?', (self.employee_id,))
        total_tickets = cursor.fetchone()[0] or 0
        
        # Get most popular passes (all-time)
        cursor.execute('''
            SELECT 
                pass_type, 
                SUM(quantity) as total_qty
            FROM customers 
            WHERE employee_id=? 
            GROUP BY pass_type
            ORDER BY total_qty DESC
        ''', (self.employee_id,))
        popular_passes = cursor.fetchall()
        
        if popular_passes and len(popular_passes) > 0:
            # Get the top pass
            top_pass = popular_passes[0]
            popular_ticket_text = f"{top_pass[0]}\n({top_pass[1]} sold)"
        else:
            popular_ticket_text = "No passes\nsold yet"
        
        conn.close()

        stats_data = [
            ("Total Sales", f"₱{total_sales:,.2f}", "#2196F3"),
            ("This Month's Sales", f"₱{monthly_sales:,.2f}", "#009688"),
            ("Total Tickets Sold", f"{int(total_tickets) if total_tickets else 0}", "#FF9800"),
            ("Most Popular Pass", popular_ticket_text, "#673AB7")
        ]

        for idx, (label, value, color) in enumerate(stats_data):
            stat_card = tk.Frame(stats_grid, bg='white', relief='solid', bd=1)
            stat_card.grid(row=idx//2, column=idx%2, padx=10, pady=5, sticky='ew')
            
            tk.Label(stat_card, text=label, font=('Arial', 10), 
                    bg='white').pack(pady=2)
            if '\n' in str(value):  # For popular ticket that has two lines
                value1, value2 = value.split('\n')
                tk.Label(stat_card, text=value1, font=('Arial', 14, 'bold'), 
                        fg=color, bg='white').pack(pady=(2,0))
                tk.Label(stat_card, text=value2, font=('Arial', 12), 
                        fg=color, bg='white').pack(pady=(0,2))
            else:
                tk.Label(stat_card, text=value, font=('Arial', 16, 'bold'), 
                        fg=color, bg='white').pack(pady=2)

        # Styled Total Availability
        availability_frame = tk.LabelFrame(self.content_frame, text="Total Availability", bg='white', font=('Arial', 12, 'bold'))
        availability_frame.pack(fill=tk.X, pady=10, padx=5)

        # Create frame for availability list
        avail_frame = tk.Frame(availability_frame, bg='white', relief='solid', bd=1)
        avail_frame.pack(fill=tk.X, padx=10, pady=5)

        conn = sqlite3.connect('funpass.db')
        cursor = conn.cursor()

        # Initialize total availability for all pass types to 0
        total_availability = {
            'Express Pass': 0,
            'Junior Pass': 0,
            'Regular Pass': 0,
            'Student Pass': 0,
            'Senior Citizen Pass': 0,
            'PWD Pass': 0
        }

        # Get total allocated tickets for all employees
        cursor.execute('''
            SELECT 
                SUM(express_pass) as express_total,
                SUM(junior_pass) as junior_total,
                SUM(regular_pass) as regular_total,
                SUM(student_pass) as student_total,
                SUM(senior_citizen_pass) as senior_total,
                SUM(pwd_pass) as pwd_total
            FROM employees
        ''')
        allocated = cursor.fetchone()

        # Get employee's allocation and sold tickets
        cursor.execute('''
            SELECT 
                express_pass, junior_pass, regular_pass, 
                student_pass, senior_citizen_pass, pwd_pass
            FROM employees 
            WHERE employee_id = ?
        ''', (self.employee_id,))
        allocated = cursor.fetchone()

        # Define pass types
        pass_types = ['Express Pass', 'Junior Pass', 'Regular Pass', 'Student Pass', 'Senior Citizen Pass', 'PWD Pass']
        
        # Get sold tickets for this employee
        sold_tickets = {}
        for pass_type in pass_types:
            cursor.execute('SELECT SUM(quantity) FROM customers WHERE pass_type=? AND employee_id=?', 
                         (pass_type, self.employee_id))
            sold = cursor.fetchone()[0] or 0
            sold_tickets[pass_type] = int(sold)

        # Map pass types to their allocations
        pass_data = [
            ('A', 'Express Pass', int(allocated[0] or 0), sold_tickets['Express Pass']),
            ('B', 'Junior Pass', int(allocated[1] or 0), sold_tickets['Junior Pass']),
            ('C', 'Regular Pass', int(allocated[2] or 0), sold_tickets['Regular Pass']),
            ('D', 'Student Pass', int(allocated[3] or 0), sold_tickets['Student Pass']),
            ('E', 'Senior Citizen Pass', int(allocated[4] or 0), sold_tickets['Senior Citizen Pass']),
            ('F', 'PWD Pass', int(allocated[5] or 0), sold_tickets['PWD Pass'])
        ]
        
        for letter, pass_type, total_allocated, sold in pass_data:
            # Calculate available tickets (allocated minus sold)
            available = total_allocated - sold

            # Create row for this pass type
            row_frame = tk.Frame(avail_frame, bg='white')
            row_frame.pack(fill=tk.X, pady=2)
            
            # Display in simple format: A. Express Pass: [available]
            label_text = f"{letter}. {pass_type}: {available}"
            tk.Label(
                row_frame, 
                text=label_text, 
                font=('Arial', 11), 
                bg='white', 
                anchor='w',
                fg='#2196F3'
            ).pack(side=tk.LEFT, padx=15, pady=2)

        conn.close()

        # Recent Sales Table section
        recent_frame = tk.LabelFrame(self.content_frame, text="Recent Sales", bg='white', font=('Arial', 12, 'bold'))
        recent_frame.pack(fill=tk.X, pady=10, padx=5)
        conn = sqlite3.connect('funpass.db')
        cursor = conn.cursor()
        cursor.execute('''SELECT ticket_id, name, pass_type, quantity, amount, purchased_date FROM customers WHERE employee_id=? ORDER BY purchased_date DESC, rowid DESC LIMIT 5''', (self.employee_id,))
        recents = cursor.fetchall()
        conn.close()
        # Table headers
        header_row = tk.Frame(recent_frame, bg='white')
        header_row.pack(fill=tk.X, pady=(0, 2))
        tk.Label(header_row, text="Customer Name", font=('Arial', 11, 'bold'), bg='white', width=18, anchor='w').pack(side=tk.LEFT, padx=5)
        tk.Label(header_row, text="Pass Type", font=('Arial', 11, 'bold'), bg='white', width=12, anchor='w').pack(side=tk.LEFT, padx=5)
        tk.Label(header_row, text="Qty", font=('Arial', 11, 'bold'), bg='white', width=5, anchor='w').pack(side=tk.LEFT, padx=5)
        tk.Label(header_row, text="Amount", font=('Arial', 11, 'bold'), bg='white', width=10, anchor='w').pack(side=tk.LEFT, padx=5)
        tk.Label(header_row, text="Date", font=('Arial', 11, 'bold'), bg='white', width=12, anchor='w').pack(side=tk.LEFT, padx=5)
        if recents:
            for ticket_id, name, pass_type, quantity, amount, purchased_date in recents:
                row = tk.Frame(recent_frame, bg='white')
                row.pack(fill=tk.X, pady=1)
                tk.Label(row, text=name, font=('Arial', 11), bg='white', width=18, anchor='w').pack(side=tk.LEFT, padx=5)
                tk.Label(row, text=pass_type, font=('Arial', 11), bg='white', width=12, anchor='w').pack(side=tk.LEFT, padx=5)
                tk.Label(row, text=quantity, font=('Arial', 11), bg='white', width=5, anchor='w').pack(side=tk.LEFT, padx=5)
                tk.Label(row, text=f"₱{amount:,.2f}", font=('Arial', 11), bg='white', width=10, anchor='w').pack(side=tk.LEFT, padx=5)
                tk.Label(row, text=purchased_date, font=('Arial', 11), bg='white', width=12, anchor='w').pack(side=tk.LEFT, padx=5)
        else:
            tk.Label(recent_frame, text="No sales yet.", font=('Arial', 11, 'italic'), fg='#6b7280', bg='white', anchor='w').pack(anchor='w', padx=10, pady=2)

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
        # Title: Pass Types and Inclusions, styled to match AdminDashboard (font size 20, bold)
        rides_title = tk.Label(self.content_frame, text="Pass Types and Inclusions", font=('Segoe UI', 20, 'bold'), bg='white', anchor='w', fg='black')
        rides_title.pack(pady=(20, 0), padx=30, anchor='w')
        # Subtitle: font size 15, gray
        rides_subtitle = tk.Label(self.content_frame, text="View Rides Descriptions and Inclusions", font=('Segoe UI', 15), fg='#6b7280', bg='white', anchor='w')
        rides_subtitle.pack(pady=(0, 10), padx=30, anchor='w')

        # Modern grid of pass type cards, styled like AdminDashboard
        grid_frame = tk.Frame(self.content_frame, bg='white')
        grid_frame.pack(pady=(10, 10), padx=0, fill='both', expand=True)
        card_w, card_h, card_r = 290, 270, 35  # Card size and radius
        card_bg = 'white'
        card_fg = 'black'
        card_padx = 20
        card_pady = 20
        pass_descriptions = [
            ("Express Pass", """• Priority access to all rides and attractions\n• Skip regular lines\n• Access to exclusive Express Pass lanes\n• Unlimited rides all day\n• Special discounts at food stalls\n• Free locker usage\n• Free parking\n• Exclusive souvenir"""),
            ("Junior Pass", """• Access to all kid-friendly rides\n• Special access to children's play areas\n• Meet and greet with mascots\n• Free snack pack\n• Age requirement: 4-12 years old\n• Free kid's meal\n• Free face painting\n• Access to kids' workshops"""),
            ("Regular Pass", """• Standard access to all rides and attractions\n• Regular queue lines\n• Full day access\n• Basic amenities access\n• Suitable for all ages\n• Free water bottle\n• Access to rest areas\n• Standard locker rental rates"""),
            ("Student Pass", """• Access to all rides and attractions\n• Special student discount\n• Valid student ID required\n• Available on weekdays only\n• Includes free locker use\n• Free study area access\n• Student meal discount\n• Free WiFi access"""),
            ("Senior Citizen Pass", """• Access to all rides and attractions\n• Priority queuing at selected rides\n• Special assistance available\n• Senior citizen ID required\n• Includes free refreshments\n• Access to senior's lounge\n• Free health monitoring\n• Special meal options"""),
            ("PWD Pass", """• Access to all rides and attractions\n• Priority queuing at all rides\n• Special assistance available\n• PWD ID required\n• Companion gets 50% discount\n• Free wheelchair service\n• Dedicated assistance staff\n• Special facilities access""")
        ]
        for idx, (pass_type, description) in enumerate(pass_descriptions):
            row = idx // 3
            col = idx % 3
            # Canvas for rounded card
            card_canvas = tk.Canvas(grid_frame, width=card_w, height=card_h, bg='white', highlightthickness=0)
            card_canvas.grid(row=row, column=col, padx=card_padx, pady=card_pady, sticky='n')
            # Draw rounded rectangle for card
            rect_id = self.draw_rounded_rect(card_canvas, 0, 0, card_w, card_h, card_r, fill=card_bg, outline='#E0E0E0', width=2)
            card_frame = tk.Frame(card_canvas, bg=card_bg)
            card_canvas.create_window((card_w//2, card_h//2), window=card_frame, anchor='center')
            # Pass type title: font size 15, bold, maroon
            tk.Label(card_frame, text=pass_type, font=('Segoe UI', 15, 'bold'), bg=card_bg, fg='#9A4E62').pack(anchor='w', padx=14, pady=(10, 0))
            # Description: font size 10, gray
            tk.Label(card_frame, text=description, font=('Segoe UI', 10), bg=card_bg, fg=card_fg, justify=tk.LEFT, anchor='w', wraplength=card_w-28).pack(anchor='w', padx=15, pady=(0, 15))
            # Hover effect for glowing outline
            def on_enter(event, canvas=card_canvas, rid=rect_id):
                canvas.itemconfig(rid, outline='#FFD700', width=5)
            def on_leave(event, canvas=card_canvas, rid=rect_id):
                canvas.itemconfig(rid, outline='#E0E0E0', width=2)
            card_canvas.bind('<Enter>', on_enter)
            card_canvas.bind('<Leave>', on_leave)

    # Utility for rounded rect (copy from main.py)
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
        self.clear_content()
        # --- Title and subtitle, styled to match AdminDashboard ---
        customer_title = tk.Label(self.content_frame, text="Customers", font=('Segoe UI', 20, 'bold'), bg='white', anchor='w')
        customer_title.pack(pady=(20, 0), padx=30, anchor='w')
        customer_subtitle = tk.Label(self.content_frame, text="View, Add, Edit, and Delete Customers", font=('Segoe UI', 15), fg='#6b7280', bg='white', anchor='w')
        customer_subtitle.pack(pady=(0, 10), padx=30, anchor='w')

        # --- Controls frame with themed background ---
        controls_frame = tk.Frame(self.content_frame, bg='white')
        controls_frame.pack(fill=tk.X, pady=10, padx=30)
        search_frame = tk.Frame(controls_frame, bg='white')
        search_frame.pack(side=tk.LEFT)
        tk.Label(search_frame, text="Search:", bg='white').pack(side=tk.LEFT, padx=5)
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, font=('Segoe UI', 11), width=30)
        search_entry.pack(side=tk.LEFT, padx=5)
        sort_frame = tk.Frame(controls_frame, bg='white')
        sort_frame.pack(side=tk.LEFT, padx=10)
        tk.Label(sort_frame, text="Sort by:", bg='white').pack(side=tk.LEFT, padx=5)
        sort_options = ttk.Combobox(sort_frame, values=["Name (A-Z)", "Name (Z-A)", "Date (Newest)", "Date (Oldest)"], width=15, font=('Segoe UI', 10))
        sort_options.pack(side=tk.LEFT, padx=5)
        sort_options.set("Name (A-Z)")
        sort_options.bind('<<ComboboxSelected>>', lambda e: self.sort_customers(sort_options.get()))
        btn_frame = tk.Frame(controls_frame, bg='white')
        btn_frame.pack(side=tk.RIGHT, padx=10)
        tk.Button(btn_frame, text="Add Customer", command=self.add_customer_dialog, bg='#4CAF50', fg='white', font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Edit Customer", command=self.edit_customer_dialog, bg='#2196F3', fg='white', font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Delete Customer", command=self.delete_customer, bg='#f44336', fg='white', font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="View Receipt", command=self.view_receipt, bg="#D0A011", fg='white', font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT, padx=5)

        # --- Table in a modern rounded card ---
        card_w, card_h, card_r = 1000, 400, 35
        table_card_canvas = tk.Canvas(self.content_frame, width=card_w, height=card_h, bg='white', highlightthickness=0)
        table_card_canvas.pack(padx=30, pady=(10, 0))
        self.draw_rounded_rect(table_card_canvas, 0, 0, card_w, card_h, card_r, fill='white', outline='')
        table_inner = tk.Frame(table_card_canvas, bg='white')
        table_card_canvas.create_window((card_w//2, card_h//2), window=table_inner, anchor='center', width=card_w-30, height=card_h-30)
        columns = ('Ticket ID', 'Name', 'Email', 'Quantity', 'Amount', 'Booked Date', 'Purchased Date', 'Pass Type')
        self.customers_tree = ttk.Treeview(table_inner, columns=columns, show='headings')
        for col in columns:
            self.customers_tree.heading(col, text=col)
            self.customers_tree.column(col, width=120)
        self.customers_tree.pack(fill=tk.BOTH, expand=True, pady=10)
        scrollbar = ttk.Scrollbar(table_inner, orient=tk.VERTICAL, command=self.customers_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.customers_tree.configure(yscrollcommand=scrollbar.set)
        sort_options.bind('<<ComboboxSelected>>', lambda e: self.sort_customers(sort_options.get()))
        self.load_customers_data()
        def clear_customers_selection(event):
            self.customers_tree.selection_remove(self.customers_tree.selection())
        self.customers_tree.bind("<FocusOut>", clear_customers_selection)
        def clear_selection_on_click(event):
            region = self.customers_tree.identify("region", event.x, event.y)
            if region == "nothing":
                self.customers_tree.selection_remove(self.customers_tree.selection())
        self.customers_tree.bind("<Button-1>", clear_selection_on_click, add="+")

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
        if sort_option == "Name (A-Z)":
            items.sort(key=lambda x: x[1])
        elif sort_option == "Name (Z-A)":
            items.sort(key=lambda x: x[1], reverse=True)
        elif sort_option == "Date (Newest)":
            items.sort(key=lambda x: x[6], reverse=True)
        elif sort_option == "Date (Oldest)":
            items.sort(key=lambda x: x[6])
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
        
        # Pass Type (move this before quantity)
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
        # Prepare ticket content for email
        ticket_content = f"""FunPass: Amusement Park Ticketing System

FunPass Booking Receipt

Booking Details
---------------------
Ticket ID: {ticket_id}
Customer Name: {name}
Email: {email}
Ticket Type: {pass_type}
Quantity: {quantity}
Unit Price: ₱{float(amount)/int(quantity):,.2f} 
Total Amount: ₱{float(amount):,.2f}
Booked Date: {booked_date}
Purchased Date: {purchased_date}

Terms & Conditions:
• Tickets are valid only for the booked date
• No refunds for unused tickets
• Please present this receipt at the entrance
• Subject to park rules and regulations
"""
        # Send email if email is provided and looks valid
        if email and "@" in email:
            self.send_ticket_via_email(email, ticket_content)

        # Print window code (existing)
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
        details_frame.pack(padx=30, pady=(0, 12), anchor='n')  # <-- anchor left

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
            row.pack(fill=tk.X, pady=2, anchor='w')  # <-- anchor left
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
    
    def show_cancellations(self):
        self.clear_content()
        # --- Title and subtitle, styled to match AdminDashboard ---
        cancel_title = tk.Label(self.content_frame, text="Cancellations & Refunds", font=('Segoe UI', 20, 'bold'), bg='white', anchor='w')
        cancel_title.pack(pady=(20, 0), padx=30, anchor='w')
        cancel_subtitle = tk.Label(self.content_frame, text="Add, Edit, and Delete Cancellation Requests (Status is always Pending)", font=('Segoe UI', 15), fg='#6b7280', bg='white', anchor='w')
        cancel_subtitle.pack(pady=(0, 10), padx=30, anchor='w')

        # --- Controls frame with themed background ---
        controls_frame = tk.Frame(self.content_frame, bg='white')
        controls_frame.pack(fill=tk.X, pady=10, padx=30)
        left_frame = tk.Frame(controls_frame, bg='white')
        left_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        search_frame = tk.Frame(left_frame, bg='white')
        search_frame.pack(side=tk.LEFT, fill=tk.X)
        tk.Label(search_frame, text="Search:", bg='white').pack(side=tk.LEFT, padx=5)
        self.cancel_search_var = tk.StringVar()
        self.cancel_search_var.trace('w', self.search_cancellations)
        search_entry = tk.Entry(search_frame, textvariable=self.cancel_search_var, font=('Segoe UI', 11), width=30)
        search_entry.pack(side=tk.LEFT, padx=5)
        sort_frame = tk.Frame(left_frame, bg='white')
        sort_frame.pack(side=tk.LEFT)
        tk.Label(sort_frame, text="Sort by:", bg='white').pack(side=tk.LEFT, padx=5)
        sort_options = ttk.Combobox(sort_frame, values=["Name (A-Z)", "Name (Z-A)", "Date (Newest)", "Date (Oldest)"], font=('Segoe UI', 10), width=15)
        sort_options.pack(side=tk.LEFT, padx=5)
        sort_options.set("Name (A-Z)")
        sort_options.bind('<<ComboboxSelected>>', lambda e: self.sort_cancellations(sort_options.get()))
        btn_frame = tk.Frame(controls_frame, bg='white')
        btn_frame.pack(side=tk.RIGHT, padx=10)
        tk.Button(btn_frame, text="Add Request", command=self.add_cancellation_dialog, bg='#4CAF50', fg='white', font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Edit Request", command=self.edit_cancellation_dialog, bg='#2196F3', fg='white', font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Delete Request", command=self.delete_cancellation, bg='#f44336', fg='white', font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT, padx=5)

        # --- Table in a modern rounded card ---
        card_w, card_h, card_r = 1000, 400, 35
        table_card_canvas = tk.Canvas(self.content_frame, width=card_w, height=card_h, bg='white', highlightthickness=0)
        table_card_canvas.pack(padx=30, pady=(10, 0))
        self.draw_rounded_rect(table_card_canvas, 0, 0, card_w, card_h, card_r, fill='white', outline='')
        table_inner = tk.Frame(table_card_canvas, bg='white')
        table_card_canvas.create_window((card_w//2, card_h//2), window=table_inner, anchor='center', width=card_w-30, height=card_h-30)
        columns = ('Ticket ID', 'Name', 'Email', 'Reasons', 'Quantity', 'Amount', 'Pass Type', 'Booked Date', 'Purchased Date', 'Status')
        self.cancellations_tree = ttk.Treeview(table_inner, columns=columns, show='headings', height=12)
        for col in columns:
            self.cancellations_tree.heading(col, text=col)
            self.cancellations_tree.column(col, width=120)
        self.cancellations_tree.pack(fill=tk.BOTH, expand=True, pady=10)
        y_scrollbar = ttk.Scrollbar(table_inner, orient=tk.VERTICAL, command=self.cancellations_tree.yview)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        x_scrollbar = ttk.Scrollbar(table_inner, orient=tk.HORIZONTAL, command=self.cancellations_tree.xview)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.cancellations_tree.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
        self.load_cancellations_data()
        def clear_cancellations_selection(event):
            self.cancellations_tree.selection_remove(self.cancellations_tree.selection())
        self.cancellations_tree.bind("<FocusOut>", clear_cancellations_selection)
        def clear_selection_on_click(event):
            region = self.cancellations_tree.identify("region", event.x, event.y)
            if region == "nothing":
                self.cancellations_tree.selection_remove(self.cancellations_tree.selection())
        self.cancellations_tree.bind("<Button-1>", clear_selection_on_click, add="+")

    def load_cancellations_data(self):
        # Clear existing items
        for item in self.cancellations_tree.get_children():
            self.cancellations_tree.delete(item)
            
        try:
            conn = sqlite3.connect('funpass.db')
            cursor = conn.cursor()
            cursor.execute('''
                SELECT ticket_id, name, email, reasons, quantity, 
                       amount, pass_type,
                       strftime('%Y-%m-%d', booked_date) as booked_date,
                       strftime('%Y-%m-%d', purchased_date) as purchased_date,
                       status
                FROM cancellations
            ''')
            cancellations = cursor.fetchall()
            conn.close()

            # Insert data into treeview
            for cancellation in cancellations:
                # Convert tuple to list for modification
                data_list = list(cancellation)
                
                # Format dates if they exist (positions 7 and 8 in the list)
                if data_list[7]:  # booked_date
                    try:
                        date_obj = datetime.strptime(data_list[7], '%Y-%m-%d')
                        data_list[7] = date_obj.strftime('%m/%d/%Y')
                    except ValueError:
                        pass
                        
                if data_list[8]:  # purchased_date
                    try:
                        date_obj = datetime.strptime(data_list[8], '%Y-%m-%d')
                        data_list[8] = date_obj.strftime('%m/%d/%Y')
                    except ValueError:
                        pass

                # Insert the formatted data into treeview
                self.cancellations_tree.insert('', tk.END, values=data_list)

        except Exception as e:
            messagebox.showerror("Database Error", f"Error loading cancellation data: {str(e)}")

    def search_cancellations(self, *args):
        search_text = self.cancel_search_var.get().lower()
        
        # Clear existing items
        for item in self.cancellations_tree.get_children():
            self.cancellations_tree.delete(item)
            
        try:
            conn = sqlite3.connect('funpass.db')
            cursor = conn.cursor()
            cursor.execute('''
                SELECT ticket_id, name, email, reasons, quantity, 
                       amount, pass_type, booked_date, purchased_date, status
                FROM cancellations
            ''')
            cancellations = cursor.fetchall()
            conn.close()

            # Filter and insert matching data
            for cancellation in cancellations:
                if any(search_text in str(value).lower() for value in cancellation):
                    self.cancellations_tree.insert('', tk.END, values=cancellation)

        except Exception as e:
            messagebox.showerror("Search Error", f"Error searching cancellations: {str(e)}")

    def sort_cancellations(self, sort_option):
        """Sort the cancellations based on the selected option."""
        items = []
        for item in self.cancellations_tree.get_children():
            values = self.cancellations_tree.item(item)['values']
            items.append(values)
            
        # Sort based on selected option
        if sort_option == "Name (A-Z)":
            items.sort(key=lambda x: x[1].lower() if x[1] else '')  # Sort by name
        elif sort_option == "Name (Z-A)":
            items.sort(key=lambda x: x[1].lower() if x[1] else '', reverse=True)
        elif sort_option == "Date (Newest)":
            items.sort(key=lambda x: x[8] if x[8] else '', reverse=True)  # Sort by booked date
        elif sort_option == "Date (Oldest)":
            items.sort(key=lambda x: x[8] if x[8] else '')
            
        # Clear and repopulate the tree
        for item in self.cancellations_tree.get_children():
            self.cancellations_tree.delete(item)
        for item in items:
            self.cancellations_tree.insert('', tk.END, values=item)

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
        tk.Label(main_frame, text="Email (optional):", font=('Arial', 11), bg='white').pack(anchor='w')
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
        
        # Pass Type (dropdown with default value)
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
                dialog.destroy()
                self.load_cancellations_data()
                messagebox.showinfo("Success", "Cancellation request added!")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {str(e)}")

        tk.Button(main_frame, text="Save", command=save_cancellation, bg='#4CAF50', fg='white').pack(pady=10)
        tk.Button(main_frame, text="Cancel", command=dialog.destroy, bg='#f44336', fg='white').pack()

    def edit_cancellation_dialog(self):
        selected = self.cancellations_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a request to edit.")
            return
        values = self.cancellations_tree.item(selected[0])['values']
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Cancellation Request")
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

        # Email (optional)
        tk.Label(main_frame, text="Email (optional):", font=('Arial', 11), bg='white').pack(anchor='w')
        email_var = tk.StringVar(value=values[2])
        email_entry = tk.Entry(main_frame, textvariable=email_var, font=('Arial', 11))
        email_entry.pack(fill=tk.X, pady=(0, 10))

        # Reasons
        tk.Label(main_frame, text="Reasons:", font=('Arial', 11), bg='white').pack(anchor='w')
        reasons_text = tk.Text(main_frame, font=('Arial', 11), height=4)
        reasons_text.insert('1.0', values[3])
        reasons_text.pack(fill=tk.X, pady=(0, 10))

        # Quantity
        tk.Label(main_frame, text="Quantity:", font=('Arial', 11), bg='white').pack(anchor='w')
        quantity_var = tk.StringVar(value=values[4])
        quantity_entry = tk.Entry(main_frame, textvariable=quantity_var, font=('Arial', 11))
        quantity_entry.pack(fill=tk.X, pady=(0, 10))

        # Amount (now editable)
        tk.Label(main_frame, text="Amount:", font=('Arial', 11), bg='white').pack(anchor='w')
        amount_var = tk.StringVar(value=values[5])
        amount_entry = tk.Entry(main_frame, textvariable=amount_var, font=('Arial', 11))  # Removed readonly state
        amount_entry.pack(fill=tk.X, pady=(0, 10))

        # Pass Type (dropdown with default value)
        tk.Label(main_frame, text="Pass Type:", font=('Arial', 11), bg='white').pack(anchor='w')
        pass_types = self.get_pass_types()
        pass_type_var = tk.StringVar(value=values[6])
        pass_type_combo = ttk.Combobox(main_frame, textvariable=pass_type_var, values=pass_types, font=('Arial', 11), state="readonly")
        pass_type_combo.pack(fill=tk.X, pady=(0, 10))
        if pass_types and values[6] not in pass_types:
            pass_type_combo.set(pass_types[0])  # Fallback to default if current value not in list

        # Booked Date (now editable)
        tk.Label(main_frame, text="Booked Date:", font=('Arial', 11), bg='white').pack(anchor='w')
        booked_date_entry = DateEntry(main_frame, font=('Arial', 11), width=18, date_pattern='MM/dd/yyyy')
        try:
            date_obj = datetime.strptime(values[7], '%m/%d/%Y')
            booked_date_entry.set_date(date_obj)
        except ValueError:
            pass
        booked_date_entry.pack(fill=tk.X, pady=(0, 10))

        # Purchased Date (now editable)
        tk.Label(main_frame, text="Purchased Date:", font=('Arial', 11), bg='white').pack(anchor='w')
        purchased_date_entry = DateEntry(main_frame, font=('Arial', 11), width=18, date_pattern='MM/dd/yyyy')
        try:
            date_obj = datetime.strptime(values[8], '%m/%d/%Y')
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
            name = name_var.get().strip()
            email = email_var.get().strip()  # Optional
            reasons = reasons_text.get('1.0', 'end-1c').strip()
            quantity = quantity_var.get().strip()
            amount = amount_var.get().strip()
            pass_type = pass_type_var.get().strip()
            
            try:
                booked_date = booked_date_entry.get_date().strftime('%Y-%m-%d')
                purchased_date = purchased_date_entry.get_date().strftime('%Y-%m-%d')
            except AttributeError:
                messagebox.showerror("Error", "Invalid date format!")
                return

            # Email is optional now
            if not all([name, reasons, quantity, amount, pass_type, booked_date, purchased_date]):
                messagebox.showerror("Error", "All fields except Email are required!")
                return

            try:
                conn = sqlite3.connect('funpass.db')
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE cancellations 
                    SET name=?, email=?, reasons=?, quantity=?, amount=?, 
                        pass_type=?, booked_date=?, purchased_date=?, status=?
                    WHERE ticket_id=?
                ''', (name, email, reasons, quantity, amount, pass_type, 
                     booked_date, purchased_date, 'Pending', ticket_id_var.get()))
                conn.commit()
                conn.close()
                dialog.destroy()
                self.load_cancellations_data()
                messagebox.showinfo("Success", "Cancellation request updated successfully!")
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

    def delete_cancellation(self):
        selected = self.cancellations_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a request to delete.")
            return

        values = self.cancellations_tree.item(selected[0])['values']
        
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this request?"):
            try:
                conn = sqlite3.connect('funpass.db')
                cursor = conn.cursor()
                # Fix: Use values[0] which is the ticket_id (first column) instead of values[1]
                cursor.execute('DELETE FROM cancellations WHERE ticket_id=?', (values[0],))
                conn.commit()
                conn.close()
                self.load_cancellations_data()
                messagebox.showinfo("Success", "Request deleted successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def show_pricing(self):
        self.clear_content()
        # --- Title and subtitle, styled to match AdminDashboard ---
        pricing_title = tk.Label(self.content_frame, text="Pass Type Pricing", font=('Segoe UI', 20, 'bold'), bg='white', anchor='w')
        pricing_title.pack(pady=(20, 0), padx=30, anchor='w')
        pricing_subtitle = tk.Label(self.content_frame, text="View Only - Pricing is managed by Admin", font=('Segoe UI', 15), fg='#6b7280', bg='white', anchor='w')
        pricing_subtitle.pack(pady=(0, 10), padx=30, anchor='w')

        # --- Table in a modern rounded card ---
        card_w, card_h, card_r = 800, 400, 35
        table_card_canvas = tk.Canvas(self.content_frame, width=card_w, height=card_h, bg='white', highlightthickness=0)
        table_card_canvas.pack(padx=30, pady=(10, 0))
        self.draw_rounded_rect(table_card_canvas, 0, 0, card_w, card_h, card_r, fill='white', outline='')
        table_inner = tk.Frame(table_card_canvas, bg='white')
        table_card_canvas.create_window((card_w//2, card_h//2), window=table_inner, anchor='center', width=card_w-30, height=card_h-30)
        prices = self.get_all_prices()
        for pass_type, current_price in prices:
            row = tk.Frame(table_inner, bg='white')
            row.pack(fill=tk.X, pady=10, padx=30)
            label = tk.Label(row, text=pass_type, font=('Segoe UI', 12, 'bold'), bg='white', width=20, anchor='w')
            label.pack(side=tk.LEFT, padx=(20, 10), pady=10)
            price_frame = tk.Frame(row, bg='white')
            price_frame.pack(side=tk.LEFT, pady=10)
            currency_label = tk.Label(price_frame, text="₱", font=('Segoe UI', 12, 'bold'), bg='white')
            currency_label.pack(side=tk.LEFT, padx=(0, 5))
            price_var = tk.StringVar(value=f"{current_price:,.2f}")
            price_entry = tk.Entry(price_frame, textvariable=price_var, font=('Segoe UI', 12, 'bold'), bg='white', width=10, justify='right', state='readonly', relief='flat')
            price_entry.pack(side=tk.LEFT)

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

    def send_ticket_via_email(self, recipient_email, ticket_content):
        # Email configuration
        sender_email = "funpasstothemagicalpark@gmail.com"
        sender_password = "qauf qaub sexo hefs"  # Use an app password for Gmail

        msg = EmailMessage()
        msg['Subject'] = 'Your FunPass Ticket'
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg.set_content(ticket_content)

        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(sender_email, sender_password)
                smtp.send_message(msg)
            print("Ticket sent successfully!")
        except Exception as e:
            print(f"Failed to send ticket: {e}")
        
if __name__ == "__main__":
    root = tk.Tk()
    create_database()
    EmployeeDashboard(root)
    root.mainloop()