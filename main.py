# Import Tkinter for GUI components
import tkinter as tk
# Import themed widgets (ttk), and messagebox for pop-up dialogs
from tkinter import ttk, messagebox
# Import PIL for image processing (used for logos, icons, etc.)
from PIL import Image, ImageTk # Pillow is a fork of PIL, so we use it for image handling
# Import sqlite3 for database operations (CRUD for app data)
import sqlite3 # SQLite is a lightweight database engine
from datetime import datetime, timedelta # For datetime and timedelta for date/time logic (sales, bookings, etc.)
from tkcalendar import DateEntry # Import tkcalendar's DateEntry for date picker widgets in forms
import time # Time for time-based updates (e.g., live clock)
import random # Import random for generating unique IDs (e.g., employee IDs)
from shared import create_database, BaseWindow # Import shared utilities (database creation, base window class)
import smtplib # For sending emails (e.g., notifications, confirmations)
from email.message import EmailMessage # For creating email messages

# Utility function for drawing rounded rectangles
def draw_rounded_rect(canvas, x1, y1, x2, y2, r, **kwargs):
    # Draw a rounded rectangle on a Tkinter Canvas
    # canvas: the Canvas widget to draw on
    # x1, y1: top-left corner coordinates
    # x2, y2: bottom-right corner coordinates
    # r: radius of the rounded corners
    # **kwargs: additional options (fill, outline, etc.)
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
    # Use create_polygon with smooth=True for rounded effect
    return canvas.create_polygon(points, smooth=True, **kwargs)

class AdminDashboard:
    # Admin dashboard window for FunPass system. Handles all admin GUI and logic
    def __init__(self, root):
        """Initialize the admin dashboard and set up the main window."""
        self.root = root
        self.root.title("FunPass - Admin Dashboard") # Set the window title
        # Make the window full screen and dynamic
        try:
            self.root.attributes('-zoomed', True)  # Windows full screen
        except Exception:
            self.root.state('zoomed')  # Fallback for other platforms
        # Set a background for the root window so the padding is visible
        self.root.configure(bg='white')
        # Configure grid: row 0 will expand vertically
        self.root.grid_rowconfigure(0, weight=1)
        # Column 0 for sidebar (fixed width)
        self.root.grid_columnconfigure(0, weight=0)
        # Column 1 for main content (expands)
        self.root.grid_columnconfigure(1, weight=1)
        # Initialize price entries dictionary for pricing section
        self.price_entries = {}
        # To create the sidebar navigation (buttons, logo)
        self.create_sidebar()
        # Set a fixed size for the main content frame
        self.content_frame = tk.Frame(self.root, bg='white', width=3000, height=2000)
        self.content_frame.grid(row=0, column=1, padx=20, pady=20)
        self.content_frame.pack_propagate(False)
        # Show dashboard by default on startup
        self.show_dashboard()

    def generate_unique_employee_id(self):
        # To generate a unique employee ID (E#####) not present in the database (Acts as a unique identifier)
        conn = sqlite3.connect('funpass.db')  # To connect to the database
        cursor = conn.cursor()
        while True:
            # Generate a random 5-digit employee ID with 'E' prefix
            new_id = f"E{random.randint(10000, 99999)}" # Random 5-digit number
            # Check if the ID already exists in the employees table
            cursor.execute("SELECT 1 FROM employees WHERE employee_id = ?", (new_id,))
            if not cursor.fetchone():  # If ID is unique
                conn.close()
                return new_id

    def _is_sidebar_active(self, name):
        # Check if a sidebar button is currently active
        for n, btn_canvas in self.sidebar_buttons.items():
            rect_id = 1
            if n == name and btn_canvas.itemcget(rect_id, 'fill') == '#FFD966':
                return True
        return False

    def create_rounded_button(self, parent, text, command, width=200, height=38, radius=20, bg='#F0E7D9', fg='black', font=('Segoe UI', 10, 'normal')):
        # Make logout button always #8f1f07
        is_logout = text.strip().startswith('🚪')
        if is_logout:
            btn_bg = '#8f1f07'
            btn_fg = 'white'
            hover_bg = '#6b1604'
        else:
            btn_bg = bg
            btn_fg = fg
            hover_bg = '#F6F6F6'
        btn_canvas = tk.Canvas(parent, width=width, height=height, bg=parent['bg'], highlightthickness=0)
        rect = draw_rounded_rect(btn_canvas, 2, 2, width-2, height-2, radius, fill=btn_bg)
        label = btn_canvas.create_text(14, height//2, text=text, fill=btn_fg, font=font, anchor='w')
        btn_canvas.bind("<Button-1>", lambda e: command())
        def on_enter(e):
            if self._is_sidebar_active(text):
                return
            btn_canvas.itemconfig(rect, fill=hover_bg)
        def on_leave(e):
            if self._is_sidebar_active(text):
                return
            btn_canvas.itemconfig(rect, fill=btn_bg)
        btn_canvas.bind("<Enter>", on_enter)
        btn_canvas.bind("<Leave>", on_leave)
        return btn_canvas

    # To create the sidebar frame
    def create_sidebar(self):
        # Create the sidebar with navigation buttons and logo
        # Sidebar dimensions
        sidebar_width = 280
        sidebar_height = 1000 
        corner_radius = 40

        sidebar_container = tk.Frame(self.root, bg='white')
        sidebar_container.grid(row=0, column=0, sticky="n", padx=(20, 0), pady=(22, 0))
        sidebar_container.grid_rowconfigure(0, weight=1)
        sidebar_container.grid_columnconfigure(0, weight=1)

        sidebar_canvas = tk.Canvas(sidebar_container, width=sidebar_width, height=sidebar_height, bg='white', highlightthickness=0)
        sidebar_canvas.grid(row=0, column=0, sticky="n")

        draw_rounded_rect(sidebar_canvas, 0, 0, sidebar_width, sidebar_height, corner_radius, fill='#ECCD93')

        sidebar_frame = tk.Frame(sidebar_canvas, bg='#ECCD93', width=sidebar_width, height=sidebar_height)
        sidebar_canvas.create_window((sidebar_width//2, 0), window=sidebar_frame, anchor="n")

        try:
            logo_path = "FunPass__1_-removebg-preview.png"
            logo_img = Image.open(logo_path)
            logo_width = 200
            aspect_ratio = logo_img.height / logo_img.width
            logo_height = int(logo_width * aspect_ratio)
            # Handles pillow version compatibility for image resampling
            try:
                resample_filter = Image.Resampling.LANCZOS
                logo_img = logo_img.resize((logo_width, logo_height), resample_filter)
            except AttributeError:
                logo_img = logo_img.resize((logo_width, logo_height))
            self.sidebar_logo = ImageTk.PhotoImage(logo_img)
            logo_label = tk.Label(sidebar_frame, image=self.sidebar_logo, bg='#ECCD93')
            logo_label.pack(padx=(0), pady=(30, 10))
        except Exception as e:
            print(f"Error loading sidebar logo: {e}")

        # To store the sidebar button canvases for active state
        self.sidebar_buttons = {}
        self.sidebar_button_names = [
            ("🏠  Dashboard", self.show_dashboard),
            ("🎢  Rides", self.show_rides),
            ("💼  Employees", self.show_employee_management),
            ("👥  Customers", self.show_customers),
            ("❌  Cancellations", self.show_cancellations),
            ("💳  Pricing", self.show_pricing),
            ("🚪  Logout", self.logout)
        ]
        for text, command in self.sidebar_button_names:
            btn_canvas = self.create_rounded_button(sidebar_frame, text, lambda c=command, n=text: self._sidebar_button_click(n, c), width=200, height=40, radius=20)
            btn_canvas.pack(pady=8)
            self.sidebar_buttons[text] = btn_canvas

    def _sidebar_button_click(self, name, command):
        # Handles the sidebar button click and set active state
        self.set_active_sidebar(name)
        command()

    def set_active_sidebar(self, page_name):
        # Highlight the active sidebar button
        active_color = '#FFD966'  # Highlight color for active
        default_color = '#F0E7D9'  # Default button color
        logout_color = '#FFD966'
        for name, btn_canvas in self.sidebar_buttons.items():
            rect_id = 1
            if name == "🚪  Logout":
                btn_canvas.itemconfig(rect_id, fill=logout_color)
            elif name == page_name:
                btn_canvas.itemconfig(rect_id, fill=active_color)
            else:
                btn_canvas.itemconfig(rect_id, fill=default_color)

    def create_main_content_frame(self):
        # This part to create the main content frame with a rounded card background
        if hasattr(self, 'main_content_canvas') and self.main_content_canvas.winfo_exists():
            self.main_content_canvas.destroy()
        card_w, card_h, card_r = 1000, 673, 45
        self.main_content_canvas = tk.Canvas(self.content_frame, width=card_w, height=card_h, bg='white', highlightthickness=0)
        self.main_content_canvas.pack(padx=0, pady=0)
        draw_rounded_rect(self.main_content_canvas, 0, 0, card_w, card_h, card_r, fill="#FFFFFF", outline='')
        main_content_inner = tk.Frame(self.main_content_canvas, bg="#FFFFFF")
        self.main_content_canvas.create_window((card_w//2, card_h//2), window=main_content_inner, anchor='center', width=card_w-20, height=card_h-20)
        return main_content_inner

    def create_scrollable_main_content_frame(self):
        if hasattr(self, 'main_content_canvas') and self.main_content_canvas.winfo_exists():
            self.main_content_canvas.destroy()
        card_w, card_h, card_r = 1000, 800, 45
        self.main_content_canvas = tk.Canvas(self.content_frame, width=card_w, height=card_h, bg='white', highlightthickness=0)
        self.main_content_canvas.pack(padx=0, pady=0)
        draw_rounded_rect(self.main_content_canvas, 0, 0, card_w, card_h, card_r, fill="#FFFFFF", outline='')
        scroll_canvas = tk.Canvas(self.main_content_canvas, bg="#FFFFFF", highlightthickness=0, width=card_w-20, height=card_h-20)
        scroll_window = self.main_content_canvas.create_window((card_w//2, card_h//2), window=scroll_canvas, anchor='center', width=card_w-20, height=card_h-20)
        v_scrollbar = tk.Scrollbar(self.main_content_canvas, orient=tk.VERTICAL, command=scroll_canvas.yview)
        scroll_canvas.configure(yscrollcommand=v_scrollbar.set)
        scrollable_frame = tk.Frame(scroll_canvas, bg='#F0E7D9')
        frame_window = scroll_canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
        def resize_scrollable_frame(event):
            canvas_width = event.width
            scroll_canvas.itemconfig(frame_window, width=canvas_width)
        scroll_canvas.bind('<Configure>', resize_scrollable_frame)
        def on_frame_configure(event):
            scroll_canvas.configure(scrollregion=scroll_canvas.bbox('all'))
        scrollable_frame.bind('<Configure>', on_frame_configure)
        def _on_mousewheel(event):
            scroll_canvas.yview_scroll(int(-1*(event.delta/120)), 'units')
        scrollable_frame.bind_all('<MouseWheel>', _on_mousewheel)
        return scrollable_frame

    def clear_content(self):
        # Clear all widgets from the main content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        if hasattr(self, 'main_content_canvas'):
            del self.main_content_canvas

    def show_dashboard(self):
        self.clear_content()
        self.set_active_sidebar('🏠  Dashboard')
        # dashboard_frame = self.create_scrollable_main_content_frame()
        dashboard_frame = tk.Frame(self.content_frame, bg='#F0E7D9')
        dashboard_frame.pack(fill=tk.BOTH, expand=True)

        # Centering frame for all content
        center_frame = tk.Frame(dashboard_frame, bg='#F0E7D9')
        center_frame.pack(expand=True)
        # Place all dashboard widgets inside dashboard_frame (no nested scrollable frames)
        title_font = ('Segoe UI', 20, 'bold')
        subtitle_font = ('Segoe UI', 15, 'normal')
        section_title_font = ('Segoe UI', 15, 'bold')
        label_font = ('Segoe UI', 10, 'normal')
        dashboard_title = tk.Label(
            dashboard_frame, text="Dashboard", font=title_font, bg="#F0E7D9", anchor='w', fg='#22223B'
        )
        dashboard_title.pack(pady=(20, 0), padx=30, anchor='w')
        dashboard_subtitle = tk.Label(
            dashboard_frame, text="View and Manage FunPass: Amusement Park Ticketing System",
            font=subtitle_font, fg='#6b7280', bg="#F0E7D9", anchor='w'
        )
        dashboard_subtitle.pack(fill=tk.X, padx=30, anchor='w')
        # Top bar with date and time 
        top_bar_card, top_bar_frame = self.create_rounded_card(dashboard_frame, width=1500, height=150, radius=45, bg='#FFFFFF', inner_bg='#FFFFFF')
        top_bar_card.pack(pady=20, padx=30, fill='x', expand=False)
        
        # Time and date labels with better styling
        time_date_frame = tk.Frame(top_bar_frame, bg='#FFFFFF')
        time_date_frame.pack(side=tk.RIGHT, padx=25, pady=20)
        
        # Date label 
        self.date_label = tk.Label(
            time_date_frame, 
            font=('Segoe UI', 15, 'normal'), 
            bg='#FFFFFF', 
            fg='#6b7280'
        )
        self.date_label.pack(side=tk.TOP, anchor='e')
        
        # Time label 
        self.time_label = tk.Label(
            time_date_frame, 
            font=('Segoe UI', 15, 'bold'), 
            bg='#FFFFFF', 
            fg='#22223B'
        )
        self.time_label.pack(side=tk.TOP, anchor='e', pady=0)
        
        # This just to add a subtle icon or text on the left side
        status_label = tk.Label(
            top_bar_frame,
            text="🟢 System Online",
            font=('Segoe UI', 15, 'normal'),
            bg='#FFFFFF',
            fg='#4CAF50'
        )
        status_label.pack(side=tk.LEFT, padx=20, pady=20, anchor='w')
        
        self.update_time()
        # Overview Card
        overview_card, overview_frame = self.create_rounded_card(dashboard_frame, width=1500, height=310, radius=45, bg='#FFFFFF', inner_bg='#FFFFFF')
        overview_card.pack(pady=20, padx=30, fill='x', expand=False)
        tk.Label(overview_frame, text='Overview', font=section_title_font, bg='#FFFFFF', fg='#22223B', anchor='w').pack(anchor='w', pady=(10, 0), padx=20)
        stats_grid = tk.Frame(overview_frame, bg='#FFFFFF')
        stats_grid.pack(fill='x', padx=20, pady=(10, 10))
        for i in range(3):
            stats_grid.grid_columnconfigure(i, weight=1)
        for i in range(2):
            stats_grid.grid_rowconfigure(i, weight=1)

        # Database Queries for statistics
        conn = sqlite3.connect('funpass.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COALESCE(SUM(amount), 0) FROM customers') # COALESCE handles NULL values.
        total_sales = cursor.fetchone()[0] or 0
        cursor.execute('''
            SELECT COALESCE(SUM(ca.amount), 0) 
            FROM cancellations ca
            WHERE ca.status="Approved"
            AND ca.ticket_id IN (SELECT ticket_id FROM customers)
            ''') # The COALESCE function evaluates its arguments from left to right and returns the first non-NULL value it encounters.
        total_refunds = cursor.fetchone()[0] or 0
        net_total_sales = total_sales - total_refunds # Calculate net sales
        cursor.execute('''SELECT COALESCE(SUM(amount), 0) FROM customers WHERE strftime('%Y-%m', purchased_date) = strftime('%Y-%m', 'now')''')
        total_month_sales = cursor.fetchone()[0] or 0 # Calculate total sales for the current month
        cursor.execute('''SELECT COALESCE(SUM(amount), 0) FROM cancellations WHERE status="Approved" AND strftime('%Y-%m', purchased_date) = strftime('%Y-%m', 'now')''')
        month_refunds = cursor.fetchone()[0] or 0 # Calculate total refunds for the current month
        net_total_month_sales = total_month_sales - month_refunds
        cursor.execute('SELECT COUNT(*) FROM employees')
        active_employees = cursor.fetchone()[0] or 0 # Count active employees
        cursor.execute('SELECT COALESCE(SUM(quantity), 0) FROM customers')
        total_tickets = cursor.fetchone()[0] or 0 # Count total tickets sold
        cursor.execute('SELECT COALESCE(SUM(quantity), 0) FROM cancellations WHERE status="Approved"') #
        total_refunded_tickets = cursor.fetchone()[0] or 0 # Count total tickets refunded
        net_total_tickets = total_tickets - total_refunded_tickets # Calculate net tickets sold
        cursor.execute('SELECT COUNT(*) FROM cancellations WHERE status="Pending"') # Count pending refunds
        pending_refunds = cursor.fetchone()[0] or 0 # Count pending refunds
        cursor.execute('''SELECT pass_type, SUM(quantity) as total_qty FROM customers WHERE strftime('%Y-%m', purchased_date) = strftime('%Y-%m', 'now') GROUP BY pass_type ORDER BY total_qty DESC LIMIT 1''')
        popular_pass = cursor.fetchone() # Get the most popular pass type sold this month
        if popular_pass:
            popular_pass_text = f"{popular_pass[0]} ({popular_pass[1]} sold)"
        else:
            popular_pass_text = "No passes sold yet"
        conn.close()
        stats_data = [
            ("Total Sales", f"₱{net_total_sales:,.2f}", "#2196F3"),
            ("Total Month Sales", f"₱{net_total_month_sales:,.2f}", "#009688"),
            ("Active Employees", str(active_employees), "#4CAF50"),
            ("Total Tickets Sold", str(net_total_tickets), "#FF9800"),
            ("Pending Refunds", str(pending_refunds), "#f44336"),
            ("Most Popular Pass", popular_pass_text, "#673AB7")
        ]
        for idx, (label, value, color) in enumerate(stats_data):
            stat = tk.Frame(stats_grid, bg='#E5ECCB', bd=0, highlightthickness=0)
            stat.grid(row=idx//3, column=idx%3, padx=12, pady=8, sticky='nsew')
            tk.Label(stat, text=label, font=('Segoe UI', 10, 'normal'), bg='#E5ECCB', fg='#6b7280').pack(anchor='w', padx=10, pady=(8, 0))
            tk.Label(stat, text=value, font=('Segoe UI', 20, 'bold'), fg=color, bg='#E5ECCB').pack(anchor='w', padx=10, pady=(0, 8))

        # Top Performing Employees Card
        top_emp_card, top_emp_frame = self.create_rounded_card(dashboard_frame, width=1500, height=300, radius=40, bg='#FFFFFF', inner_bg='#FFFFFF')
        top_emp_card.pack(pady=20, padx=30, fill='x', expand=False)
        tk.Label(top_emp_frame, text='Top Performing Employees', font=section_title_font, bg='#FFFFFF', fg='#22223B', anchor='w').pack(anchor='w', pady=(80, 0), padx=20)
        table_frame = tk.Frame(top_emp_frame, bg='#FFFFFF')
        table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        columns = ('Employee Name', 'Tickets Sold', 'Total Month Sales')
        emp_tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=8)
        emp_tree.heading('Employee Name', text='Employee Name')
        emp_tree.heading('Tickets Sold', text='Tickets Sold')
        emp_tree.heading('Total Month Sales', text='Total Month Sales')
        emp_tree.column('Employee Name', width=200)
        emp_tree.column('Tickets Sold', width=150, anchor='center')
        emp_tree.column('Total Month Sales', width=150, anchor='center')
        emp_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=emp_tree.yview)
        emp_tree.configure(yscrollcommand=emp_scrollbar.set)
        emp_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        
        def on_mousewheel_emp(event):
            emp_tree.yview_scroll(int(-1*(event.delta/120)), 'units')
        emp_tree.bind('<MouseWheel>', on_mousewheel_emp)
        conn = sqlite3.connect('funpass.db')
        cursor = conn.cursor()
        now = datetime.now()
        first_day = now.replace(day=1).strftime('%Y-%m-%d')
        last_day = now.strftime('%Y-%m-%d')
        cursor.execute('''SELECT e.name, COALESCE(SUM(c.quantity), 0) - COALESCE((SELECT SUM(ca.quantity) FROM cancellations ca WHERE ca.status = 'Approved' AND ca.ticket_id IN (SELECT ticket_id FROM customers WHERE employee_id = e.employee_id AND strftime('%Y-%m', purchased_date) = strftime('%Y-%m', 'now')) AND strftime('%Y-%m', ca.purchased_date) = strftime('%Y-%m', 'now')), 0) AS tickets_sold, COALESCE(SUM(c.amount), 0) - COALESCE((SELECT SUM(ca.amount) FROM cancellations ca WHERE ca.status = 'Approved' AND ca.ticket_id IN (SELECT ticket_id FROM customers WHERE employee_id = e.employee_id AND strftime('%Y-%m', purchased_date) = strftime('%Y-%m', 'now')) AND strftime('%Y-%m', ca.purchased_date) = strftime('%Y-%m', 'now')), 0) AS total_sales FROM employees e LEFT JOIN customers c ON e.employee_id = c.employee_id AND c.purchased_date BETWEEN ? AND ? GROUP BY e.employee_id, e.name ORDER BY total_sales DESC LIMIT 5''', (first_day, last_day))
        top_employees = cursor.fetchall()
        conn.close()
        for emp in top_employees:
            name, tickets, sales = emp
            formatted_sales = f"₱{sales:,.2f}" if sales else "₱0.00"
            tickets = str(tickets) if tickets else "0"
            emp_tree.insert('', tk.END, values=(name, tickets, formatted_sales))

    def update_time(self):
        # Update the time and date labels every second
        try:
            current = datetime.now()
            current_time = current.strftime("%m/%d/%Y %H:%M:%S")
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
        # Pass type cards grid 
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

    def create_rounded_card(self, parent, width, height, radius=45, bg='#F5F6FA', inner_bg='white'):
        # Create a rounded card frame for content display
        card_canvas = tk.Canvas(parent, width=width, height=height, bg=parent['bg'], highlightthickness=0)
        draw_rounded_rect(card_canvas, 0, 0, width, height, radius, fill=bg, outline='')
        card_frame = tk.Frame(card_canvas, bg=inner_bg)
        card_canvas.create_window((width//2, height//2), window=card_frame, anchor='center', width=width-20)
        return card_canvas, card_frame

    def create_rounded_frame(self, parent, width, height, radius=45, bg='#F5F6FA', inner_bg='white'):
        # Create a rounded frame for content display
        card_canvas = tk.Canvas(parent, width=width, height=height, bg=parent['bg'], highlightthickness=0)
        draw_rounded_rect(card_canvas, 0, 0, width, height, radius, fill=bg, outline='')
        frame = tk.Frame(card_canvas, bg=inner_bg)
        card_canvas.create_window((width//2, height//2), window=frame, anchor='center', width=width-20)
        return card_canvas, frame

    def show_employee_management(self):
        import customtkinter as ctk
        self.clear_content()
        self.set_active_sidebar('💼  Employees')

        # Main Card Container
        card_frame = ctk.CTkFrame(self.content_frame, fg_color="#FFFFFF", corner_radius=0)
        card_frame.pack(fill="both", expand=True, padx=30, pady=30)

        # Header 
        header_row = ctk.CTkFrame(card_frame, fg_color="#FFFFFF")
        header_row.pack(fill="x", pady=(10, 0), anchor="w")
        header_row.grid_columnconfigure(0, weight=1)
        emp_title = ctk.CTkLabel(header_row, text="Employee", font=("Segoe UI", 22, "bold"), text_color="#22223B")
        emp_title.grid(row=0, column=0, padx=15, sticky="w")
        emp_subtitle = ctk.CTkLabel(header_row, text="View and manage employees", font=("Segoe UI", 15), text_color="#6b7280")
        emp_subtitle.grid(row=1, column=0, padx=15,pady=10, sticky="w")

        # Controls Bar
        controls_bar = ctk.CTkFrame(card_frame, fg_color="#F0E7D9", corner_radius=0, height=50)
        controls_bar.pack(fill="x", padx=10, pady=(0, 15))
        controls_bar.grid_columnconfigure(0, weight=1)
        controls_bar.grid_columnconfigure(1, weight=0)
        controls_bar.grid_columnconfigure(2, weight=0)
        controls_bar.grid_columnconfigure(3, weight=0)
        controls_bar.grid_columnconfigure(4, weight=0)

        # Search Entry
        self.emp_search_var = ctk.StringVar()
        self.emp_search_var.trace('w', self.search_employees)
        search_entry = ctk.CTkEntry(
            controls_bar,
            textvariable=self.emp_search_var,
            placeholder_text="Search Employee...",
            placeholder_text_color="#858585",
            width=220,
            height=36,
            font=("Segoe UI", 12),
            text_color="#3f3f3f",
            fg_color="#fff",
            border_color="#cccccc",
            border_width=2
        )
        search_entry.grid(row=0, column=0, padx=(16, 8), pady=10, sticky="w")

        # Sort Combobox (all columns)
        emp_sort_options_list = [
            ("ID (A-Z)", 0, False), ("ID (Z-A)", 0, True),
            ("Name (A-Z)", 1, False), ("Name (Z-A)", 1, True),
            ("Username (A-Z)", 2, False), ("Username (Z-A)", 2, True),
            ("Password (A-Z)", 3, False), ("Password (Z-A)", 3, True),
            ("Express Alloc (Lowest)", 4, False), ("Express Alloc (Highest)", 4, True),
            ("Junior Alloc (Lowest)", 5, False), ("Junior Alloc (Highest)", 5, True),
            ("Regular Alloc (Lowest)", 6, False), ("Regular Alloc (Highest)", 6, True),
            ("Student Alloc (Lowest)", 7, False), ("Student Alloc (Highest)", 7, True),
            ("PWD Alloc (Lowest)", 8, False), ("PWD Alloc (Highest)", 8, True),
            ("Senior Alloc (Lowest)", 9, False), ("Senior Alloc (Highest)", 9, True),
            ("Month Sales (Lowest)", 10, False), ("Month Sales (Highest)", 10, True)
        ]
        sort_options = ctk.CTkComboBox(
            controls_bar,
            values=[opt[0] for opt in emp_sort_options_list],
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
        sort_options.configure(command=lambda value: self.sort_employees(value))
        self._emp_sort_options = emp_sort_options_list

        # Edit Button
        edit_btn = ctk.CTkButton(
            controls_bar, text="✏️ Edit", width=70, height=36, fg_color="#FFFFFF", text_color="#4CAF50", hover_color="#C8E6C9", border_color="#ADADAD", border_width=2,
            font=("Segoe UI", 12, "bold"), corner_radius=24, command=lambda: self.show_employee_dialog(mode="edit")
        )
        edit_btn.grid(row=0, column=2, padx=(0, 8), pady=10)

        # Delete Button
        delete_btn = ctk.CTkButton(
            controls_bar, text="🗑️ Delete", width=90, height=36, fg_color="#FFFFFF", text_color="#f44336", hover_color="#FFCDD2", border_color="#ADADAD", border_width=2,
            font=("Segoe UI", 12, "bold"), corner_radius=24, command=self.delete_employee
        )
        delete_btn.grid(row=0, column=3, padx=(0, 8), pady=10)

        # Add Account Button
        add_btn = ctk.CTkButton(
            controls_bar, text="+ Add Account", width=140, height=36, fg_color="#4CAF50", text_color="#fff", hover_color="#388E3C",
            font=("Segoe UI", 12, "bold"), corner_radius=10, command=lambda: self.show_employee_dialog(mode="add")
        )
        add_btn.grid(row=0, column=4, padx=(0, 12), pady=10)

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
        columns = ('ID', 'Name', 'Username', 'Password', 'Express Alloc', 'Junior Alloc', 'Regular Alloc', 'Student Alloc', 'PWD Alloc', 'Senior Alloc', 'Month Sales')
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Treeview', font=('Segoe UI', 11), rowheight=32, background='#FFFFFF', fieldbackground='#FFFFFF', borderwidth=0)
        style.configure('Treeview.Heading', font=('Segoe UI', 11, 'bold'), background='#E0E0E0', foreground='#9A4E62', borderwidth=0)
        style.layout('Treeview', [('Treeview.treearea', {'sticky': 'nswe'})])
        self.emp_tree = ttk.Treeview(
            table_card, columns=columns, show='headings', style='Treeview',
            yscrollcommand=yscroll.set, xscrollcommand=xscroll.set
        )
        self.emp_tree.grid(row=0, column=0, sticky='nsew')
        yscroll.configure(command=self.emp_tree.yview)
        xscroll.configure(command=self.emp_tree.xview)
        self.emp_tree.heading('ID', text='Employee ID')
        self.emp_tree.column('ID', width=120, anchor='w')
        self.emp_tree.heading('Name', text='Name')
        self.emp_tree.column('Name', width=160, anchor='w')
        self.emp_tree.heading('Username', text='Username')
        self.emp_tree.column('Username', width=140, anchor='w')
        self.emp_tree.heading('Password', text='Password')
        self.emp_tree.column('Password', width=140, anchor='w')
        alloc_columns = [ ('Express Alloc', 'Express Pass'), ('Junior Alloc', 'Junior Pass'), ('Regular Alloc', 'Regular Pass'), ('Student Alloc', 'Student Pass'), ('PWD Alloc', 'PWD Pass'), ('Senior Alloc', 'Senior C Pass') ]
        self.emp_tree.heading('Month Sales', text='Month Sales')
        self.emp_tree.column('Month Sales', width=140, anchor='center')
        for col, header in alloc_columns:
            self.emp_tree.heading(col, text=header)
            self.emp_tree.column(col, width=110, anchor='center')
        def clear_selection_on_click(event):
            region = self.emp_tree.identify("region", event.x, event.y)
            if region == "nothing":
                self.emp_tree.selection_remove(self.emp_tree.selection())
        self.emp_tree.bind("<Button-1>", clear_selection_on_click, add="+")
        self.load_employees()

    def show_customers(self):
        import customtkinter as ctk
        self.clear_content()
        self.set_active_sidebar('👥  Customers')

        # Main Card Container 
        card_frame = ctk.CTkFrame(self.content_frame, fg_color="#FFFFFF", corner_radius=0)
        card_frame.pack(fill="both", expand=True, padx=30, pady=30)

        # Header Block
        header_row = ctk.CTkFrame(card_frame, fg_color="#FFFFFF")
        header_row.pack(fill="x", pady=(10, 0), anchor="w")
        header_row.grid_columnconfigure(0, weight=1)
        cust_title = ctk.CTkLabel(header_row, text="Customers", font=("Segoe UI", 22, "bold"), text_color="#22223B")
        cust_title.grid(row=0, column=0, padx=15, sticky="w")
        cust_subtitle = ctk.CTkLabel(header_row, text="View All Customers and Ticket Sales", font=("Segoe UI", 15), text_color="#6b7280")
        cust_subtitle.grid(row=1, column=0, padx=15, pady=10, sticky="w")

        # Controls Bar
        controls_bar = ctk.CTkFrame(card_frame, fg_color="#F0E7D9", corner_radius=0, height=50)
        controls_bar.pack(fill="x", padx=10, pady=(0, 15))
        controls_bar.grid_columnconfigure(0, weight=1)
        controls_bar.grid_columnconfigure(1, weight=0)
        controls_bar.grid_columnconfigure(2, weight=0)

        # Search Entry
        self.search_var = ctk.StringVar()
        self.search_var.trace('w', self.search_customers)
        search_entry = ctk.CTkEntry(
            controls_bar,
            textvariable=self.search_var,
            placeholder_text="Search customer...",
            text_color="#3f3f3f",
            placeholder_text_color="#969696",
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
            ("Pass Type (A-Z)", 3, False), ("Pass Type (Z-A)", 3, True),
            ("Quantity (Lowest)", 4, False), ("Quantity (Highest)", 4, True),
            ("Amount (Lowest)", 5, False), ("Amount (Highest)", 5, True),
            ("Booked Date (Newest)", 6, True), ("Booked Date (Oldest)", 6, False),
            ("Purchased Date (Newest)", 7, True), ("Purchased Date (Oldest)", 7, False),
            ("Employee (A-Z)", 8, False), ("Employee (Z-A)", 8, True)
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

        # Delete Button
        delete_btn = ctk.CTkButton(
            controls_bar, text="Delete", width=90, height=36, fg_color="#E0E0E0", text_color="#f44336", hover_color="#FFCDD2",
            font=("Segoe UI", 12, "bold"), corner_radius=10, command=self.delete_customer
        )
        delete_btn.grid(row=0, column=2, padx=(0, 12), pady=10)

        # Table Frame (with scrollbars)
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
        columns = ('Ticket ID', 'Name', 'Email', 'Pass Type', 'Quantity', 'Amount', 'Booked Date', 'Purchased Date', 'Employee')
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
        for col in columns:
            self.customers_tree.heading(col, text=col)
            self.customers_tree.column(col, width=120)
        def clear_selection_on_click(event):
            region = self.customers_tree.identify("region", event.x, event.y)
            if region == "nothing":
                self.customers_tree.selection_remove(self.customers_tree.selection())
        self.customers_tree.bind("<Button-1>", clear_selection_on_click, add="+")
        self.load_customers_data()

    def show_cancellations(self):
        import customtkinter as ctk
        self.clear_content()
        self.set_active_sidebar('❌  Cancellations')

        # Main Card Container 
        card_frame = ctk.CTkFrame(self.content_frame, fg_color="#FFFFFF", corner_radius=0)
        card_frame.pack(fill="both", expand=True, padx=30, pady=30)

        # Header Block
        header_row = ctk.CTkFrame(card_frame, fg_color="#FFFFFF")
        header_row.pack(fill="x", pady=(10, 0), anchor="w")
        header_row.grid_columnconfigure(0, weight=1)
        cancel_title = ctk.CTkLabel(header_row, text="Cancellations and Refunds", font=("Segoe UI", 22, "bold"), text_color="#22223B")
        cancel_title.grid(row=0, column=0, padx=15, sticky="w")
        cancel_subtitle = ctk.CTkLabel(header_row, text="View and Manage Customers Submitted Refund Requests", font=("Segoe UI", 15), text_color="#6b7280")
        cancel_subtitle.grid(row=1, column=0, padx=15, pady=10, sticky="w")

        # Controls Bar
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
            placeholder_text_color="#969696",
            text_color="#3f3f3f",
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
        sort_options.configure(command=lambda value: self.sort_cancellations(value)) # Set the command to sort cancellations
        self._cancel_sort_options = cancel_sort_options_list

        # Edit Status Button
        edit_btn = ctk.CTkButton(
            controls_bar, text="Edit Status", width=110, height=36, fg_color="#E0E0E0", text_color="#4CAF50", hover_color="#C8E6C9",
            font=("Segoe UI", 12, "bold"), corner_radius=10, command=self.edit_cancellation_status
        )
        edit_btn.grid(row=0, column=2, padx=(0, 8), pady=10)

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

    def show_pricing(self):
        self.clear_content()
        
        # Add pass type pricing title and subtitle
        pricing_title = tk.Label(self.content_frame, text="Pass Type Pricing", font=('Arial', 16, 'bold'), bg='white', anchor='w')
        pricing_title.pack(pady=(10, 0), padx=20, anchor='w')
        
        self.price_update_label = tk.Label(self.content_frame, text="", font=('Arial', 10), fg='#4CAF50', bg='white', anchor='w')
        self.price_update_label.pack(pady=(5, 0), padx=20, anchor='w')
        
        pricing_subtitle = tk.Label(self.content_frame, text="View and Manage Ticketing Pricing", font=('Arial', 12), fg='#6b7280', bg='white', anchor='w')
        pricing_subtitle.pack(pady=(0, 10), padx=20, anchor='w')

        # Create main frame for pricing
        main_frame = tk.Frame(self.content_frame, bg='white')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=50, pady=20)

        # Get current prices from database
        conn = sqlite3.connect('funpass.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM pricing')
        prices = cursor.fetchall()
        conn.close()

        # Store entry widgets
        self.price_entries = {}

        # Create price editing interface
        for pass_type, current_price in prices:
            # Create frame for each row
            row = tk.Frame(main_frame, bg='white', name=f"price_row_{pass_type.replace(' ', '_').lower()}")
            row.pack(fill=tk.X, pady=10)

            # Create pass type label (left-aligned)
            label = tk.Label(row, text=pass_type, font=('Arial', 12), bg='white',
                           width=20, anchor='w')
            label.pack(side=tk.LEFT, padx=(20, 10))

            # Create price entry with currency symbol
            price_frame = tk.Frame(row, bg='white')
            price_frame.pack(side=tk.LEFT)

            currency_label = tk.Label(price_frame, text="₱", font=('Arial', 12), bg='white')
            currency_label.pack(side=tk.LEFT, padx=(0, 5))

            # Create StringVar with initial formatted price
            price_var = tk.StringVar(value=f"{float(current_price):.2f}")
            
            # Add validation to only allow numbers and decimal point
            def validate_price(action, value_if_allowed):
                if action == '1':  # Insert
                    if value_if_allowed == "":
                        return True
                    try:
                        # Remove commas for validation
                        cleaned_value = value_if_allowed.replace(',', '')
                        # Allow numbers, single decimal point, and optional negative sign
                        if cleaned_value.count('.') <= 1 and cleaned_value.replace('.', '').replace('-', '', 1).isdigit():
                            # Don't allow just a decimal point or negative sign
                            if cleaned_value not in ['.', '-']:
                                return True
                    except ValueError:
                        pass
                    return False
                return True

            entry = tk.Entry(price_frame, textvariable=price_var, 
                           font=('Arial', 12), width=10,
                           justify='right',
                           name=f"price_entry_{pass_type.replace(' ', '_').lower()}")
            entry.pack(side=tk.LEFT)
            
            self.price_entries[pass_type] = price_var
            
            vcmd = (entry.register(validate_price), '%d', '%P')
            entry.configure(validate="key", validatecommand=vcmd)

            # Add immediate feedback on invalid input
            def on_invalid_input(event):
                widget = event.widget
                if widget.get():
                    try:
                        float(widget.get().replace(',', ''))
                        widget.config(fg='black')
                    except ValueError:
                        widget.config(fg='red')
            
            entry.bind('<KeyRelease>', on_invalid_input)

        # Create buttons frame
        btn_frame = tk.Frame(self.content_frame, bg='white')
        btn_frame.pack(pady=20)

        # Create save button
        save_btn = tk.Button(btn_frame, text="Save Changes", 
                           command=self.save_prices,
                           bg='#4CAF50', fg='white', 
                           font=('Arial', 11, 'bold'),
                           width=15, height=2)
        save_btn.pack(side=tk.LEFT, padx=10)

        # Create reset button
        reset_btn = tk.Button(btn_frame, text="Reset", 
                            command=self.reset_prices,
                            bg='#f44336', fg='white', 
                            font=('Arial', 11, 'bold'),
                            width=15, height=2)
        reset_btn.pack(side=tk.LEFT, padx=10)

        # Show last update time
        self.price_update_label.config(text=f"Last updated: {time.strftime('%m/%d/%Y %H:%M:%S')}")

    def save_prices(self):
        try:
            # Validate that all prices are valid numbers and store them
            new_prices = {}
            for pass_type, price_var in self.price_entries.items():
                try:
                    # Remove commas and spaces, then convert to float
                    price_str = price_var.get().replace(',', '').replace(' ', '')
                    price = float(price_str)
                    if price < 0:
                        raise ValueError(f"Price for {pass_type} cannot be negative")
                    new_prices[pass_type] = price
                except ValueError as e:
                    messagebox.showerror("Invalid Input", str(e))
                    return False

            # Start database transaction
            conn = sqlite3.connect('funpass.db')
            try:
                cursor = conn.cursor()
                # Begin transaction
                cursor.execute('BEGIN')

                for pass_type, price in new_prices.items():
                    # Update price in database
                    cursor.execute('UPDATE pricing SET price = ? WHERE pass_type = ?',
                                 (price, pass_type))
                    # Update the entry display with the formatted price
                    self.price_entries[pass_type].set(f"{price:.2f}")
                
                # Commit transaction
                conn.commit()

                # Generate price update event
                if hasattr(self, 'root') and self.root:
                    print("Generating price update event")  # Debug print
                    self.root.event_generate('<<PriceUpdate>>')
                    print("Price update event generated successfully")  # Debug print
                
                messagebox.showinfo("Success", "Prices updated successfully!")
                return True

            except sqlite3.Error as e:
                # Rollback on error
                conn.rollback()
                messagebox.showerror("Database Error", f"An error occurred: {str(e)}")
                return False
            finally:
                conn.close()

        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")
            return False

    def reset_prices(self):
        if messagebox.askyesno("Confirm Reset", 
                             "Are you sure you want to reset to default prices?"):
            default_prices = {
                'Express Pass': 2300.00,
                'Junior Pass': 900.00,
                'Regular Pass': 1300.00,
                'Student Pass': 1300.00,
                'Senior Citizen Pass': 900.00,
                'PWD Pass': 900.00
            }

            # Update entry fields
            for pass_type, price in default_prices.items():
                if pass_type in self.price_entries:
                    self.price_entries[pass_type].set(f"{price:.2f}")

            # Save to database
            try:
                conn = sqlite3.connect('funpass.db')
                cursor = conn.cursor()
                
                for pass_type, price in default_prices.items():
                    cursor.execute('UPDATE pricing SET price = ? WHERE pass_type = ?',
                                 (price, pass_type))
                
                conn.commit()
                conn.close()
                
                # Notify employee dashboard to refresh prices
                self.notify_price_update()
                
                messagebox.showinfo("Success", "Prices reset to default values!")
            except sqlite3.Error as e:
                messagebox.showerror("Database Error", f"An error occurred: {str(e)}")

    def notify_price_update(self):
        # Call refresh prices on all employee dashboards
        if hasattr(self, 'root') and self.root:
            self.root.event_generate('<<PriceUpdate>>')

    def logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.root.destroy()
            from login import show_login
            show_login()

    def search_employees(self, *args):
        search_text = self.emp_search_var.get().lower()
        
        # To clear current display para everytime search is performed
        for item in self.emp_tree.get_children():
            self.emp_tree.delete(item)
            
        # To get all employees from database   
        conn = sqlite3.connect('funpass.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM employees')
        employees = cursor.fetchall()
        conn.close()
        
        # To filter and display matching employees
        for employee in employees:
            # To search in all fields
            if any(search_text in str(value).lower() for value in employee):
                self.emp_tree.insert('', tk.END, values=employee)

    def sort_employees(self, sort_option):
        items = []
        for item in self.emp_tree.get_children():
            values = self.emp_tree.item(item)['values']
            items.append(values)
        # Find the sort index and reverse from the options
        for label, idx, reverse in self._emp_sort_options:
            if label == sort_option:
                # Special handling for numeric columns
                if idx in [4,5,6,7,8,9]:  # Allocations
                    items.sort(key=lambda x: int(x[idx]), reverse=reverse)
                elif idx == 10:  # Month Sales (currency string)
                    items.sort(key=lambda x: float(str(x[idx]).replace('₱','').replace(',','')), reverse=reverse)
                else:
                    items.sort(key=lambda x: str(x[idx]), reverse=reverse)
                break
        for item in self.emp_tree.get_children():
            self.emp_tree.delete(item)
        for item in items:
            self.emp_tree.insert('', tk.END, values=item)

    def delete_customer(self):
        selected_item = self.customers_tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a customer record to delete.")
            return

        if messagebox.askyesno("Confirm Delete", 
                             "Are you sure you want to delete this customer record?\nThis action cannot be undone."):

            # Get ticket ID from selected item
            ticket_id = self.customers_tree.item(selected_item[0])['values'][0]

            try:
                conn = sqlite3.connect('funpass.db')
                cursor = conn.cursor()
                
                # Delete the customer record
                cursor.execute('DELETE FROM customers WHERE ticket_id = ?', (ticket_id,))
                
                # Commit changes and close connection
                conn.commit()
                conn.close()

                # Remove from treeview
                self.customers_tree.delete(selected_item[0])
                
                messagebox.showinfo("Success", "Customer record deleted successfully!")
            
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"An error occurred: {str(e)}")
                
            except Exception as e:
                messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")
                
                if hasattr(self, 'emp_tree') and self.emp_tree.winfo_exists():
                    self.load_employees()   

    def search_customers(self, *args):
        search_text = self.search_var.get().lower()
        for item in self.customers_tree.get_children():
            self.customers_tree.delete(item)
        conn = sqlite3.connect('funpass.db')
        cursor = conn.cursor()
        cursor.execute('''SELECT c.ticket_id, c.name, c.email, c.pass_type, c.quantity, c.amount, \
                    strftime('%m/%d/%Y', c.booked_date) as booked_date, \
                    strftime('%m/%d/%Y', c.purchased_date) as purchased_date, \
                    IFNULL(e.name, '') as employee_name \
                    FROM customers c \
                    LEFT JOIN employees e ON c.employee_id = e.employee_id''')
        customers = cursor.fetchall()
        conn.close()
        for customer in customers:
            if any(search_text in str(value).lower() for value in customer):
                self.customers_tree.insert('', tk.END, values=customer)

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
        cursor.execute('''SELECT c.ticket_id, c.name, c.email, c.pass_type, c.quantity, c.amount, \
                    strftime('%m/%d/%Y', c.booked_date) as booked_date, \
                    strftime('%m/%d/%Y', c.purchased_date) as purchased_date, \
                    IFNULL(e.name, '') as employee_name \
                    FROM customers c \
                    LEFT JOIN employees e ON c.employee_id = e.employee_id''')
        customers = cursor.fetchall()
        conn.close()
        for customer in customers:
            self.customers_tree.insert('', tk.END, values=customer)

    def edit_cancellation_status(self):
        selected_item = self.cancellations_tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a cancellation to edit.")
            return

        # To get current values
        current_values = self.cancellations_tree.item(selected_item[0])['values']
        
        # To create edit window
        edit_window = tk.Toplevel(self.root)
        edit_window.title("Edit Cancellation Status")
        edit_window.geometry("400x300")
        edit_window.configure(bg='white')

        # To create edit frame
        edit_frame = tk.Frame(edit_window, bg='white', padx=20, pady=20)
        edit_frame.pack(fill=tk.BOTH, expand=True)

        # Show current status
        tk.Label(edit_frame, text="Current Status:", font=('Arial', 11, 'bold'), 
        bg='white').pack(pady=5)
        tk.Label(edit_frame, text=current_values[9], font=('Arial', 11), 
                bg='white').pack(pady=5)

        # create new status selection
        tk.Label(edit_frame, text="New Status:", font=('Arial', 11, 'bold'), 
        
        bg='white').pack(pady=10)
        status_var = tk.StringVar(value=current_values[9])
        status_combo = ttk.Combobox(edit_frame, textvariable=status_var,
                                values=["Pending", "Approved", "Rejected"])
        status_combo.pack(pady=5)

        def save_status():
            new_status = status_var.get()
            if new_status != current_values[9]:
        # Update database
                conn = sqlite3.connect('funpass.db')
                cursor = conn.cursor()
                cursor.execute('UPDATE cancellations SET status = ? WHERE ticket_id = ?',
                    (new_status, current_values[0]))
                conn.commit()
                conn.close()

        # Send email notification if status is changed to Approved or Rejected
                if new_status in ["Approved", "Rejected"]:
                    to_email = current_values[2]
                    name = current_values[1]
                    ticket_id = current_values[0]
                    if to_email:
                        self.send_cancellation_status_email(to_email, name, ticket_id, new_status)

        # Refresh all relevant tables and dashboard
                if hasattr(self, 'cancellations_tree') and self.cancellations_tree.winfo_exists():
                    self.load_cancellations_data()
                if hasattr(self, 'emp_tree') and self.emp_tree.winfo_exists():
                    self.load_employees()
                self.show_cancellations()
                messagebox.showinfo("Success", "Status updated successfully!")
            # Always close the window after clicking Save
            edit_window.destroy()

        # to create buttons
        buttons_frame = tk.Frame(edit_frame, bg='white')
        buttons_frame.pack(pady=20)
        
        tk.Button(buttons_frame, text="Save", command=save_status,
                 bg='#4CAF50', fg='white', font=('Arial', 11)).pack(side=tk.LEFT, padx=5)
        tk.Button(buttons_frame, text="Cancel", command=edit_window.destroy,
                 bg='#f44336', fg='white', font=('Arial', 11)).pack(side=tk.LEFT, padx=5)

    def delete_cancellation(self):
        selected_item = self.cancellations_tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a cancellation to delete.")
            return

        if messagebox.askyesno("Confirm Delete", 
                             "Are you sure you want to delete this cancellation record?"):
            # To get ticket ID
            ticket_id = self.cancellations_tree.item(selected_item[0])['values'][0]

            # Delete from database
            conn = sqlite3.connect('funpass.db')
            cursor = conn.cursor()
            cursor.execute('DELETE FROM cancellations WHERE ticket_id = ?', (ticket_id,))
            conn.commit()
            conn.close()

            # Remove from treeview
            self.cancellations_tree.delete(selected_item[0])
            messagebox.showinfo("Success", "Cancellation record deleted successfully!")
    def search_cancellations(self, *args):
        search_text = self.cancel_search_var.get().lower()
        for item in self.cancellations_tree.get_children():
            self.cancellations_tree.delete(item)
        conn = sqlite3.connect('funpass.db')
        cursor = conn.cursor()
        cursor.execute('''        SELECT ticket_id, name, email, pass_type, reasons, quantity, amount,
            strftime('%m/%d/%Y', booked_date) as booked_date, 
            strftime('%m/%d/%Y', purchased_date) as purchased_date,
            status
        FROM cancellations
        ''')
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
        cursor.execute('''
            SELECT ticket_id, name, email, pass_type, reasons, quantity, amount,
                   strftime('%m/%d/%Y', booked_date) as booked_date,
                   strftime('%m/%d/%Y', purchased_date) as purchased_date,
                   status
            FROM cancellations
            ORDER BY id DESC
        ''')
        cancellations = cursor.fetchall()
        conn.close()
        for cancellation in cancellations:
            self.cancellations_tree.insert('', tk.END, values=cancellation)

    def load_employees(self):
        # Clear existing items
        for item in self.emp_tree.get_children():
            self.emp_tree.delete(item)
            
        # Load from database
        conn = sqlite3.connect('funpass.db')
        cursor = conn.cursor()        # First get all employees and their basic info
        cursor.execute('SELECT * FROM employees')
        employees = cursor.fetchall()
        
        # Then get the monthly sales for each employee
        for emp in employees:
            employee_id = emp[0]
            # Get monthly sales
            cursor.execute('''
                SELECT COALESCE(SUM(amount), 0) 
                FROM customers 
                WHERE employee_id = ? 
                AND strftime('%Y-%m', purchased_date) = strftime('%Y-%m', 'now')
            ''', (employee_id,))
            monthly_sales = cursor.fetchone()[0] or 0

            # Get tickets sold this month
            cursor.execute('''
                SELECT COALESCE(SUM(quantity), 0)
                FROM customers
                WHERE employee_id = ?
                AND strftime('%Y-%m', purchased_date) = strftime('%Y-%m', 'now')
            ''', (employee_id,))
            tickets_sold = cursor.fetchone()[0] or 0

            # Get approved refunds for this month (amount)
            cursor.execute('''
                SELECT COALESCE(SUM(amount), 0)
                FROM cancellations
                WHERE ticket_id IN (
                    SELECT ticket_id 
                    FROM customers 
                    WHERE employee_id = ?
                )
                AND status = 'Approved'
                AND strftime('%Y-%m', purchased_date) = strftime('%Y-%m', 'now')
            ''', (employee_id,))
            refunds = cursor.fetchone()[0] or 0

            # Get approved refunds for this month (tickets)
            cursor.execute('''
                SELECT COALESCE(SUM(quantity), 0)
                FROM cancellations
                WHERE ticket_id IN (
                    SELECT ticket_id 
                    FROM customers 
                    WHERE employee_id = ?
                )
                AND status = 'Approved'
                AND strftime('%Y-%m', purchased_date) = strftime('%Y-%m', 'now')
            ''', (employee_id,))
            refunded_tickets = cursor.fetchone()[0] or 0

            # Calculate net monthly sales and tickets
            net_monthly_sales = monthly_sales - refunds
            net_tickets_sold = tickets_sold - refunded_tickets

            # Create list of values for treeview
            emp_list = list(emp)
            emp_list.append(f"₱{net_monthly_sales:,.2f}")  # Add monthly sales 

            # Insert into treeview
            self.emp_tree.insert('', tk.END, values=emp_list)
            
        conn.close()

    def show_employee_dialog(self, mode="add", event=None):
        if mode == "edit":
            selected_items = self.emp_tree.selection()
            if not selected_items:
                messagebox.showwarning("No Selection", "Please select an employee to edit.")
                return
            values = self.emp_tree.item(selected_items[0])['values']

        dialog = tk.Toplevel(self.root)
        dialog.title("Add Employee" if mode == "add" else "Edit Employee")
        dialog.geometry("500x750")  
        dialog.configure(bg='white')

        # Create main frame
        main_frame = tk.Frame(dialog, bg='white', padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Basic info section
        basic_frame = tk.LabelFrame(main_frame, text="Basic Information", bg='white', pady=10, padx=10)
        basic_frame.pack(fill=tk.X, pady=(0, 20))

        # Basic fields
        basic_fields = [
            ('Name:', 'name'),
            ('Username:', 'username'),
            ('Password:', 'password'),
        ]

        basic_entries = {}
        for label_text, field_name in basic_fields:
            field_frame = tk.Frame(basic_frame, bg='white')
            field_frame.pack(fill=tk.X, pady=5)
            label = tk.Label(field_frame, text=label_text, bg='white', font=('Arial', 11), width=12, anchor='w')
            label.pack(side=tk.LEFT, padx=(0, 10))
            entry = tk.Entry(field_frame, font=('Arial', 11), width=30)
           

            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            basic_entries[field_name] = entry

        # Ticket allocation section
        alloc_frame = tk.LabelFrame(main_frame, text="Ticket Allocation", bg='white', pady=10, padx=10)
        alloc_frame.pack(fill=tk.X)

        # Ticket allocation fields
        alloc_fields = [
            ('Express Pass:', 'express'),
            ('Junior Pass:', 'junior'),
            ('Regular Pass:', 'regular'),
            ('Student Pass:', 'student'),
            ('PWD Pass:', 'pwd'),
            ('Senior Pass:', 'senior')
        ]

        alloc_entries = {}
        for label_text, field_name in alloc_fields:
            field_frame = tk.Frame(alloc_frame, bg='white')
            field_frame.pack(fill=tk.X, pady=5)
            label = tk.Label(field_frame, text=label_text, bg='white', font=('Arial', 11), width=12, anchor='w')
            label.pack(side=tk.LEFT, padx=(0, 10))

            # Create spinbox for ticket quantity with default value 0 and hint behavior
            spinbox = tk.Spinbox(field_frame, from_=0, to=1000, width=10, font=('Arial', 11))
            spinbox.pack(side=tk.LEFT)
            spinbox.delete(0, tk.END)
            spinbox.insert(0, "0")  # Set default value and hint

            def on_focus_in(event, sb=spinbox):
                if sb.get() == "0":
                    sb.delete(0, tk.END)

            def on_focus_out(event, sb=spinbox):
                if sb.get() == "":
                    sb.insert(0, "0")

            spinbox.bind("<FocusIn>", on_focus_in)
            spinbox.bind("<FocusOut>", on_focus_out)

            alloc_entries[field_name] = spinbox

        # Set values if editing
        if mode == "edit":
            basic_entries['name'].insert(0, values[1])
            basic_entries['username'].insert(0, values[2])
            basic_entries['password'].insert(0, values[3])
            
            # Set allocation values
            alloc_entries['express'].delete(0, tk.END)
            alloc_entries['express'].insert(0, values[4])
            alloc_entries['junior'].delete(0, tk.END)
            alloc_entries['junior'].insert(0, values[5])
            alloc_entries['regular'].delete(0, tk.END)
            alloc_entries['regular'].insert(0, values[6])
            alloc_entries['student'].delete(0, tk.END)
            alloc_entries['student'].insert(0, values[7])
            alloc_entries['pwd'].delete(0, tk.END)
            alloc_entries['pwd'].insert(0, values[8])
            alloc_entries['senior'].delete(0, tk.END)
            alloc_entries['senior'].insert(0, values[9])

        def save_employee():
            # Get values from entries
            employee_data = {
                'name': basic_entries['name'].get().strip(),
                'username': basic_entries['username'].get().strip(),
                'password': basic_entries['password'].get().strip(),
                'express': int(alloc_entries['express'].get()),
                'junior': int(alloc_entries['junior'].get()),
                'regular': int(alloc_entries['regular'].get()),
                'student': int(alloc_entries['student'].get()),
                'pwd': int(alloc_entries['pwd'].get()),
                'senior': int(alloc_entries['senior'].get())
            }

            # Validate inputs
            if not all([employee_data['name'], employee_data['username'], employee_data['password']]):
                messagebox.showerror("Error", "Name, username and password are required!")
                return
                
            # Validate ticket allocations
            for field in ['express', 'junior', 'regular', 'student', 'pwd', 'senior']:
                if not str(employee_data[field]).isdigit() or int(employee_data[field]) < 0:
                    messagebox.showerror("Error", f"Invalid ticket quantity for {field} pass!")
                    return

            try:
                conn = sqlite3.connect('funpass.db')
                cursor = conn.cursor()
                
                if mode == "add":
                    employee_id = self.generate_unique_employee_id()
                    cursor.execute('''
                        INSERT INTO employees (
                            employee_id, name, username, password, express_pass, junior_pass,
                            regular_pass, student_pass, pwd_pass, senior_citizen_pass
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        employee_id,
                        employee_data['name'], employee_data['username'],
                        employee_data['password'], employee_data['express'],
                        employee_data['junior'], employee_data['regular'],
                        employee_data['student'], employee_data['pwd'],
                        employee_data['senior']
                    )) 
                else:  # edit mode
                    cursor.execute('''
                        UPDATE employees SET
                            name=?, username=?, password=?, express_pass=?,
                            junior_pass=?, regular_pass=?, student_pass=?,
                            pwd_pass=?, senior_citizen_pass=?
                        WHERE employee_id=?
                    ''', (
                        employee_data['name'], employee_data['username'],
                        employee_data['password'], employee_data['express'],
                        employee_data['junior'], employee_data['regular'],
                        employee_data['student'], employee_data['pwd'],
                        employee_data['senior'], values[0]
                    ))

                conn.commit()
                messagebox.showinfo("Success", 
                                  "Employee saved successfully!")
                dialog.destroy()
                self.load_employees()  
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Username already exists!")
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"Database error: {str(e)}")
            finally:
                conn.close()

        # Create buttons frame
        btn_frame = tk.Frame(main_frame, bg='white')
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="Save", command=save_employee,
                 bg='#4CAF50', fg='white', font=('Arial', 11)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Cancel", command=dialog.destroy,
                 bg='#f44336', fg='white', font=('Arial', 11)).pack(side=tk.LEFT, padx=5)

    def delete_employee(self):
        selected_items = self.emp_tree.selection()
        if not selected_items:
            messagebox.showwarning("No Selection", "Please select an employee to delete.")
            return

        if messagebox.askyesno("Confirm Delete", 
                             "Are you sure you want to delete this employee?"):
            employee_id = self.emp_tree.item(selected_items[0])['values'][0]

            conn = sqlite3.connect('funpass.db')
            cursor = conn.cursor()
            try:
                cursor.execute('DELETE FROM employees WHERE employee_id = ?', 
                             (employee_id,))
                conn.commit()
                self.emp_tree.delete(selected_items[0])
                messagebox.showinfo("Success", "Employee deleted successfully!")
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"Database error: {str(e)}")
            finally:
                conn.close()    
    
    # wala ito, sa iba na ito, huwag na lang sigurong galawin hehehe
    def create_icon_button(self, parent, icon, command, bg='black', fg='pink', size=40, radius=15, font_size=20):
        """Reusable helper for modern icon button with rounded gray background."""
        canvas = tk.Canvas(parent, width=size, height=size, bg='#9A4E62', highlightthickness=0, bd=0)
        draw_rounded_rect(canvas, 2, 2, size-2, size-2, radius, fill=bg, outline='')
        canvas.create_text(size//2, size//2, text=icon, fill=fg, font=('Segoe UI', font_size))
        canvas.bind("<Button-1>", lambda e: command())
        canvas.config(cursor='hand2')
        return canvas

    import smtplib
    from email.message import EmailMessage

    def send_cancellation_status_email(self, to_email, name, ticket_id, status):
        SMTP_SERVER = 'smtp.gmail.com'
        SMTP_PORT = 587
        SMTP_USER = 'funpasstothemagicalpark@gmail.com'
        SMTP_PASS = 'qauf qaub sexo hefs'

        subject = f"FunPass Cancellation Request Update (Ticket ID: {ticket_id})"
        if status == "Approved":
            body = f"""\
Hello {name},

We are pleased to inform you that your cancellation request for Ticket ID {ticket_id} has been successfully APPROVED.
Our team has reviewed your request and the necessary documents, and everything appears to be in order. The refund process has now been initiated, and you can expect to receive your refund within the next 5 to 7 business days, depending on your payment method and bank processing times.If you do not receive the refund within this period, or if you have any further concerns, please do not hesitate to reach out to us at funpasstothemagicalpark@gmail.com or visit our customer service desk in person.

Thank you for using FunPass and for being a valued guest of the FunPass Amusement Park. We hope to see you again soon for a more magical experience.

Best regards,
FunPass: Amusement Park Ticketing System
"""
        elif status == "Rejected":
            body = f"""\
Hello {name},

We regret to inform you that your cancellation request for Ticket ID {ticket_id} has been REJECTED.
After careful review by our team, we found that the request did not meet the necessary requirements for approval. This may be due to incomplete or missing documents, invalid justification, or the request being made outside the allowable cancellation period. If you believe this decision was made in error or if you have additional documents that may support your request, we encourage you to resubmit your cancellation request or visit our customer service desk for further assistance.

Please understand that our cancellation policy is in place to ensure fairness to all our guests and to maintain smooth operations within the park. We appreciate your understanding and thank you for being part of the FunPass experience. We still hope to welcome you back for a joyful and memorable visit in the future.

Best regards,  
FunPass: Amusement Park Ticketing System 
"""
        else:
            return  # Only send for Approved or Rejected

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
            print(f"Status update email sent to {to_email}")
        except Exception as e:
            print(f"Failed to send status update email: {e}")

if __name__ == "__main__":
    create_database()  # Initialize the database
    root = tk.Tk()
    app = AdminDashboard(root)
    root.mainloop()