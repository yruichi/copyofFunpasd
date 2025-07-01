# Import Tkinter for GUI components
import tkinter as tk
# Import themed widgets (ttk), and messagebox for pop-up dialogs
from tkinter import ttk, messagebox
# Import PIL for image processing (used for logos, icons, etc.)
from PIL import Image, ImageTk
# Import sqlite3 for database operations (CRUD for app data)
import sqlite3
# Import datetime and timedelta for date/time logic (sales, bookings, etc.)
from datetime import datetime, timedelta
# Import tkcalendar's DateEntry for date picker widgets in forms
from tkcalendar import DateEntry
# Import time for time-based updates (e.g., live clock)
import time
# Import random for generating unique IDs (e.g., employee IDs)
import random
# Import shared utilities (database creation, base window class)
from shared import create_database, BaseWindow

# Utility function for drawing rounded rectangles (to avoid code duplication)
def draw_rounded_rect(canvas, x1, y1, x2, y2, r, **kwargs):
    # Draw a rounded rectangle on a Tkinter Canvas
    # canvas: the Canvas widget to draw on
    # x1, y1: top-left corner coordinates
    # x2, y2: bottom-right corner coordinates
    # r: radius of the rounded corners
    # **kwargs: additional options (fill, outline, etc.)
    points = [
        x1+r, y1,              # Start at top-left, move right by radius
        x2-r, y1,              # Top edge, leave space for top-right corner
        x2, y1,                # Top-right corner start
        x2, y1+r,              # Curve down for top-right corner
        x2, y2-r,              # Right edge, leave space for bottom-right corner
        x2, y2,                # Bottom-right corner start
        x2-r, y2,              # Curve left for bottom-right corner
        x1+r, y2,              # Bottom edge, leave space for bottom-left corner
        x1, y2,                # Bottom-left corner start
        x1, y2-r,              # Curve up for bottom-left corner
        x1, y1+r,              # Left edge, leave space for top-left corner
        x1, y1                 # Close the shape
    ]
    # Use create_polygon with smooth=True for rounded effect
    return canvas.create_polygon(points, smooth=True, **kwargs)

class AdminDashboard:
    # Admin dashboard window for FunPass system. Handles all admin GUI and logic
    def __init__(self, root):
        """Initialize the admin dashboard and set up the main window."""
        self.root = root
        # Set the window title
        self.root.title("FunPass - Admin Dashboard")
        # Maximize the window on open
        self.root.state('zoomed')
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
        # Create the sidebar navigation (buttons, logo)
        self.create_sidebar()
        # Main content area (right side of the window)
        self.content_frame = tk.Frame(self.root, bg='white') 
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        # Show dashboard by default on startup
        self.show_dashboard()

    def generate_unique_employee_id(self):
        # Generate a unique employee ID (E#####) not present in the database
        conn = sqlite3.connect('funpass.db')  # Connect to the database
        cursor = conn.cursor()
        while True:
            # Generate a random 5-digit employee ID with 'E' prefix
            new_id = f"E{random.randint(10000, 99999)}"
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
        # Create a custom rounded button using a Canvas
        btn_canvas = tk.Canvas(parent, width=width, height=height, bg=parent['bg'], highlightthickness=0)
        rect = draw_rounded_rect(btn_canvas, 2, 2, width-2, height-2, radius, fill=bg)
        label = btn_canvas.create_text(14, height//2, text=text, fill=fg, font=font, anchor='w')
        btn_canvas.bind("<Button-1>", lambda e: command())
        def on_enter(e):
            if self._is_sidebar_active(text):
                return
            btn_canvas.itemconfig(rect, fill='#F6F6F6')
        def on_leave(e):
            if self._is_sidebar_active(text):
                return
            btn_canvas.itemconfig(rect, fill=bg)
        btn_canvas.bind("<Enter>", on_enter)
        btn_canvas.bind("<Leave>", on_leave)
        return btn_canvas

    # Create the sidebar frame
    def create_sidebar(self):
        # Create the sidebar with navigation buttons and logo
        # Sidebar dimensions
        sidebar_width = 280
        sidebar_height = 670  # Fixed height for visible rounded corners
        corner_radius = 40

        sidebar_container = tk.Frame(self.root, bg='white')
        sidebar_container.grid(row=0, column=0, sticky="n", padx=(20, 0), pady=(22, 0))
        sidebar_container.grid_rowconfigure(0, weight=1)
        sidebar_container.grid_columnconfigure(0, weight=1)

        sidebar_canvas = tk.Canvas(sidebar_container, width=sidebar_width, height=sidebar_height, bg='white', highlightthickness=0)
        sidebar_canvas.grid(row=0, column=0, sticky="n")

        # Replace all draw_rounded_rect calls with the utility function
        draw_rounded_rect(sidebar_canvas, 0, 0, sidebar_width, sidebar_height, corner_radius, fill='#ECCD93')

        sidebar_frame = tk.Frame(sidebar_canvas, bg='#ECCD93', width=sidebar_width, height=sidebar_height)
        sidebar_canvas.create_window((sidebar_width//2, 0), window=sidebar_frame, anchor="n")

        try:
            logo_path = "FunPass__1_-removebg-preview.png"
            logo_img = Image.open(logo_path)
            logo_width = 200
            aspect_ratio = logo_img.height / logo_img.width
            logo_height = int(logo_width * aspect_ratio)
            # Handle Pillow version compatibility for image resampling
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

        # Store sidebar button canvases for active state
        self.sidebar_buttons = {}
        self.sidebar_button_names = [
            ("🏠  Dashboard", self.show_dashboard),
            ("🎢  Rides", self.show_rides),
            ("💼  Employee Management", self.show_employee_management),
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
        # Handle sidebar button click and set active state
        self.set_active_sidebar(name)
        command()

    def set_active_sidebar(self, page_name):
        # Highlight the active sidebar button
        active_color = '#FFD966'  # Highlight color for active
        default_color = '#F0E7D9'  # Default button color
        for name, btn_canvas in self.sidebar_buttons.items():
            # Find the rectangle id (always 1st item created)
            rect_id = 1
            if name == page_name:
                btn_canvas.itemconfig(rect_id, fill=active_color)
            else:
                btn_canvas.itemconfig(rect_id, fill=default_color)

    def create_main_content_frame(self):
        # Create the main content frame with a rounded card background
        if hasattr(self, 'main_content_canvas') and self.main_content_canvas.winfo_exists():
            self.main_content_canvas.destroy()
        card_w, card_h, card_r = 1000, 673, 45
        self.main_content_canvas = tk.Canvas(self.content_frame, width=card_w, height=card_h, bg='white', highlightthickness=0)
        self.main_content_canvas.pack(padx=0, pady=0)
        draw_rounded_rect(self.main_content_canvas, 0, 0, card_w, card_h, card_r, fill='#F0E7D9', outline='')
        main_content_inner = tk.Frame(self.main_content_canvas, bg='#F0E7D9')
        self.main_content_canvas.create_window((card_w//2, card_h//2), window=main_content_inner, anchor='center', width=card_w-20, height=card_h-20)
        return main_content_inner

    def create_scrollable_main_content_frame(self):
        if hasattr(self, 'main_content_canvas') and self.main_content_canvas.winfo_exists():
            self.main_content_canvas.destroy()
        card_w, card_h, card_r = 1000, 673, 45
        self.main_content_canvas = tk.Canvas(self.content_frame, width=card_w, height=card_h, bg='white', highlightthickness=0)
        self.main_content_canvas.pack(padx=0, pady=0)
        draw_rounded_rect(self.main_content_canvas, 0, 0, card_w, card_h, card_r, fill='#F0E7D9', outline='')
        scroll_canvas = tk.Canvas(self.main_content_canvas, bg='#F0E7D9', highlightthickness=0, width=card_w-20, height=card_h-20)
        scroll_window = self.main_content_canvas.create_window((card_w//2, card_h//2), window=scroll_canvas, anchor='center', width=card_w-20, height=card_h-20)
        v_scrollbar = tk.Scrollbar(self.main_content_canvas, orient=tk.VERTICAL, command=scroll_canvas.yview)
        # v_scrollbar.pack(fill=tk.Y, side=tk.RIGHT)  # invisible
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
        dashboard_frame = self.create_scrollable_main_content_frame()
        # Place all dashboard widgets inside dashboard_frame (no nested scrollable frames)
        title_font = ('Segoe UI', 20, 'bold')
        subtitle_font = ('Segoe UI', 15, 'normal')
        section_title_font = ('Segoe UI', 15, 'bold')
        label_font = ('Segoe UI', 10, 'normal')
        dashboard_title = tk.Label(
            dashboard_frame, text="Dashboard", font=title_font, bg='#F0E7D9', anchor='w', fg='#22223B'
        )
        dashboard_title.pack(pady=(20, 0), padx=30, anchor='w')
        dashboard_subtitle = tk.Label(
            dashboard_frame, text="View and Manage FunPass: Amusement Park Ticketing System",
            font=subtitle_font, fg='#6b7280', bg='#F0E7D9', anchor='w'
        )
        dashboard_subtitle.pack(fill=tk.X, padx=30, anchor='w')
        # Top bar with date and time - MODERN CARDED DESIGN
        top_bar_card, top_bar_frame = self.create_rounded_card(dashboard_frame, width=900, height=150, radius=45, bg='#FFFFFF', inner_bg='#FFFFFF')
        top_bar_card.pack(pady=20, padx=30, fill='x', expand=False)
        
        # Time and date labels with better styling
        time_date_frame = tk.Frame(top_bar_frame, bg='#FFFFFF')
        time_date_frame.pack(side=tk.RIGHT, padx=25, pady=20)
        
        # Date label with larger font
        self.date_label = tk.Label(
            time_date_frame, 
            font=('Segoe UI', 15, 'normal'), 
            bg='#FFFFFF', 
            fg='#6b7280'
        )
        self.date_label.pack(side=tk.TOP, anchor='e')
        
        # Time label with larger, bold font
        self.time_label = tk.Label(
            time_date_frame, 
            font=('Segoe UI', 15, 'bold'), 
            bg='#FFFFFF', 
            fg='#22223B'
        )
        self.time_label.pack(side=tk.TOP, anchor='e', pady=0)
        
        # Add a subtle icon or text on the left side
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
        overview_card, overview_frame = self.create_rounded_card(dashboard_frame, width=900, height=310, radius=45, bg='#FFFFFF', inner_bg='#FFFFFF')
        overview_card.pack(pady=20, padx=30, fill='x', expand=False)
        tk.Label(overview_frame, text='Overview', font=section_title_font, bg='#FFFFFF', fg='#22223B', anchor='w').pack(anchor='w', pady=(10, 0), padx=20)
        stats_grid = tk.Frame(overview_frame, bg='#FFFFFF')
        stats_grid.pack(fill='x', padx=20, pady=(10, 10))
        for i in range(3):
            stats_grid.grid_columnconfigure(i, weight=1)
        for i in range(2):
            stats_grid.grid_rowconfigure(i, weight=1)

        # DATABASE QUERIES
        conn = sqlite3.connect('funpass.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COALESCE(SUM(amount), 0) FROM customers')
        total_sales = cursor.fetchone()[0] or 0
        cursor.execute('SELECT COALESCE(SUM(amount), 0) FROM cancellations WHERE status="Approved"')
        total_refunds = cursor.fetchone()[0] or 0
        net_total_sales = total_sales - total_refunds
        cursor.execute('''SELECT COALESCE(SUM(amount), 0) FROM customers WHERE strftime('%Y-%m', purchased_date) = strftime('%Y-%m', 'now')''')
        total_month_sales = cursor.fetchone()[0] or 0
        cursor.execute('''SELECT COALESCE(SUM(amount), 0) FROM cancellations WHERE status="Approved" AND strftime('%Y-%m', purchased_date) = strftime('%Y-%m', 'now')''')
        month_refunds = cursor.fetchone()[0] or 0
        net_total_month_sales = total_month_sales - month_refunds
        cursor.execute('SELECT COUNT(*) FROM employees')
        active_employees = cursor.fetchone()[0] or 0
        cursor.execute('SELECT COALESCE(SUM(quantity), 0) FROM customers')
        total_tickets = cursor.fetchone()[0] or 0
        cursor.execute('SELECT COALESCE(SUM(quantity), 0) FROM cancellations WHERE status="Approved"')
        total_refunded_tickets = cursor.fetchone()[0] or 0
        net_total_tickets = total_tickets - total_refunded_tickets
        cursor.execute('SELECT COUNT(*) FROM cancellations WHERE status="Pending"')
        pending_refunds = cursor.fetchone()[0] or 0
        cursor.execute('''SELECT pass_type, SUM(quantity) as total_qty FROM customers WHERE strftime('%Y-%m', purchased_date) = strftime('%Y-%m', 'now') GROUP BY pass_type ORDER BY total_qty DESC LIMIT 1''')
        popular_pass = cursor.fetchone()
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
        top_emp_card, top_emp_frame = self.create_rounded_card(dashboard_frame, width=900, height=300, radius=40, bg='#FFFFFF', inner_bg='#FFFFFF')
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
        
        # Add mouse wheel scrolling support
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

        # Recent Sales Card
        recent_sales_card, recent_sales_frame = self.create_rounded_card(dashboard_frame, width=900, height=300, radius=40, bg='#FFFFFF', inner_bg='#FFFFFF')
        recent_sales_card.pack(pady=20, padx=30, fill='x', expand=False)
        tk.Label(recent_sales_frame, text='Recent Sales', font=section_title_font, bg='#FFFFFF', fg='#22223B', anchor='w').pack(anchor='w', pady=(80, 0), padx=20)
        sales_table_frame = tk.Frame(recent_sales_frame, bg='#FFFFFF')
        sales_table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        sales_columns = ('Ticket ID', 'Name', 'Email', 'Pass Type', 'Quantity', 'Amount', 'Booked Date', 'Purchased Date', 'Employee')
        sales_tree = ttk.Treeview(sales_table_frame, columns=sales_columns, show='headings', height=8)
        column_widths = {
            'Ticket ID': 100,
            'Name': 150,
            'Email': 150,
            'Pass Type': 120,
            'Quantity': 70,
            'Amount': 100,
            'Booked Date': 100,
            'Purchased Date': 100,
            'Employee': 150
        }
        for col in sales_columns:
            sales_tree.heading(col, text=col)
            sales_tree.column(col, width=column_widths.get(col, 100))
            if col in ['Quantity']:
                sales_tree.column(col, anchor='center')
            elif col in ['Amount']:
                sales_tree.column(col, anchor='w')
        sales_scrollbar = ttk.Scrollbar(sales_table_frame, orient=tk.VERTICAL, command=sales_tree.yview)
        sales_tree.configure(yscrollcommand=sales_scrollbar.set)
        sales_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add mouse wheel scrolling support
        def on_mousewheel_sales(event):
            sales_tree.yview_scroll(int(-1*(event.delta/120)), 'units')
        sales_tree.bind('<MouseWheel>', on_mousewheel_sales)
        def load_recent_sales(sort_option=None):
            # Clear all rows in the sales_tree before loading new data
            sales_tree.delete(*sales_tree.get_children())
            # Connect to the database
            conn = sqlite3.connect('funpass.db')
            cursor = conn.cursor()
            # Query: Get the 5 most recent sales, joining with employee names
            cursor.execute('''SELECT c.ticket_id, c.name, c.email, c.pass_type, c.quantity, c.amount, strftime('%m/%d/%Y', c.booked_date) as booked_date, strftime('%m/%d/%Y', c.purchased_date) as purchased_date, COALESCE(e.name, 'N/A') as employee_name FROM customers c LEFT JOIN employees e ON c.employee_id = e.employee_id ORDER BY datetime(c.purchased_date) DESC LIMIT 5''')
            recent_sales = cursor.fetchall()
            conn.close()
            for sale in recent_sales:
                formatted_values = list(sale)
                # Format the amount as currency (₱X,XXX.XX)
                formatted_values[5] = f"₱{float(sale[5]):,.2f}"
                # Insert the row into the sales_tree
                sales_tree.insert('', tk.END, values=formatted_values)
        load_recent_sales()

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
        self.set_active_sidebar('🎢  Rides')
        rides_frame = self.create_scrollable_main_content_frame()
        header_row = tk.Frame(rides_frame, bg='#F0E7D9')
        header_row.pack(fill=tk.X, pady=(20, 0), padx=30)
        title = tk.Label(header_row, text="Pass Types and Inclusions", font=('Segoe UI', 20, 'bold'), bg='#F0E7D9', fg='black', anchor='w')
        title.pack(side=tk.LEFT, anchor='w')
        
        # Subtitle (optional)
        subtitle = tk.Label(rides_frame, text="View rides descriptions and inclusions", font=('Segoe UI', 15), fg='#6b7280', bg='#F0E7D9', anchor='w')
        subtitle.pack(fill=tk.X, padx=30, anchor='w')

        # Pass type cards grid
        grid_frame = tk.Frame(rides_frame, bg='#F0E7D9')
        grid_frame.pack(pady=(10, 10), padx=(0, 0), fill='both', expand=True)  # Increased right padding
        card_w2, card_h2, card_r2 = 290, 270, 35  # Slightly reduced card width
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
            card_canvas2 = tk.Canvas(grid_frame, width=card_w2, height=card_h2, bg='#F0E7D9', highlightthickness=0)
            card_canvas2.grid(row=row, column=col, padx=card_padx, pady=card_pady, sticky='n')
            # Draw the rounded rectangle and keep its id for outline changes
            rect_id = draw_rounded_rect(card_canvas2, 0, 0, card_w2, card_h2, card_r2, fill=card_bg, outline='#E0E0E0', width=2)
            card_frame2 = tk.Frame(card_canvas2, bg=card_bg)
            card_canvas2.create_window((card_w2//2, card_h2//2), window=card_frame2, anchor='center')
            tk.Label(card_frame2, text=pass_type, font=('Segoe UI', 15, 'bold'), bg=card_bg, fg='#9A4E62').pack(anchor='w', padx=14, pady=(10, 0))
            tk.Label(card_frame2, text=description, font=('Segoe UI', 10), bg=card_bg, fg=card_fg, justify=tk.LEFT, anchor='w', wraplength=card_w2-28).pack(anchor='w', padx=15, pady=(0, 15))
            # Hover effect for glowing outline
            def on_enter(event, canvas=card_canvas2, rid=rect_id):
                canvas.itemconfig(rid, outline='#FFD700', width=5)  # Gold glow
            def on_leave(event, canvas=card_canvas2, rid=rect_id):
                canvas.itemconfig(rid, outline='#E0E0E0', width=2)
            card_canvas2.bind('<Enter>', on_enter)
            card_canvas2.bind('<Leave>', on_leave)

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
        self.clear_content()
        self.set_active_sidebar('💼  Employee Management')
        card_frame = self.create_main_content_frame()
        # Header row
        header_row = tk.Frame(card_frame, bg='#F0E7D9')
        header_row.pack(fill=tk.X, pady=(20, 0), padx=30)
        emp_title = tk.Label(header_row, text="Employee", font=('Segoe UI', 20, 'bold'), bg='#F0E7D9', anchor='w', fg='#22223B')
        emp_title.pack(side=tk.LEFT, anchor='w')
        emp_subtitle = tk.Label(card_frame, text="View and manage employees", font=('Segoe UI', 15), fg='#6b7280', bg='#F0E7D9', anchor='w')
        emp_subtitle.pack(fill=tk.X, padx=30, pady=(0, 18), anchor='w')
        # Add Account button in its own row above controls_row
        add_btn_row = tk.Frame(card_frame, bg='#F0E7D9')
        add_btn_row.pack(fill=tk.X, padx=30, pady=(0, 0))
        add_btn = tk.Button(add_btn_row, text="+ Add Account", command=lambda: self.show_employee_dialog(mode="add"), bg='#F0E7D9', fg='#6b7280', font=('Segoe UI', 10, 'bold'), bd=0, padx=5, pady=5, relief='flat', cursor='hand2')
        add_btn.pack(side=tk.RIGHT, anchor='e')

        # Controls row (simple, white background)
        controls_row = tk.Frame(card_frame, bg='#9A4E62')
        controls_row.pack(fill=tk.X, padx=28, pady=(0, 10))
        # Left: Edit/Delete buttons
        icon_btns_frame = tk.Frame(controls_row, bg='#9A4E62')
        icon_btns_frame.pack(side=tk.LEFT, padx=(0, 0), pady=5)
        edit_icon_btn = self.create_icon_button(
            icon_btns_frame, "     ✏️", lambda: self.show_employee_dialog(mode="edit"),
            bg='white', fg='black', size=36, radius=10, font_size=20
        )
        edit_icon_btn.pack(side=tk.LEFT, padx=5)
        delete_icon_btn = self.create_icon_button(
            icon_btns_frame, "     🗑️", self.delete_employee,
            bg='white', fg='black', size=35, radius=10, font_size=20
        )
        delete_icon_btn.pack(side=tk.LEFT, padx=5)

        # Right: Search bar (flat, rounded, with icon) and sort dropdown
        search_frame = tk.Frame(controls_row, bg='white')
        search_frame.pack(side=tk.RIGHT, padx=(0, 0), pady=0)
        self.emp_search_var = tk.StringVar()
        self.emp_search_var.trace('w', self.search_employees)
        search_entry = tk.Entry(
            search_frame, textvariable=self.emp_search_var,
            font=('Segoe UI', 11), width=28, relief='flat', bd=1, bg='#f8f8f8', highlightthickness=1, highlightbackground='#e0e0e0'
        )
        search_entry.pack(side=tk.LEFT, fill='y', ipady=6, padx=(0, 0))
        search_icon = tk.Label(search_frame, text="🔍", bg='#f8f8f8', font=('Segoe UI', 12), fg='#888')
        search_icon.place(in_=search_entry, relx=1.0, x=-24, rely=0.5, anchor='e')
        # Sort dropdown beside search bar
        # Custom style for sort dropdown to match theme
        style = ttk.Style()
        style.theme_use('default')
        style.configure(
            "Theme.TCombobox",
            fieldbackground="#9A4E62",  # Maroon background for entry field
            background="#9A4E62",       # Maroon background for dropdown arrow
            foreground="#fff",          # White text
            bordercolor="#9A4E62",      # Maroon border
            padding=8,                   # Extra padding for a modern look
            relief="flat"
        )
        style.map(
            "Theme.TCombobox",
            fieldbackground=[('readonly', '#9A4E62')],
            background=[('readonly', '#9A4E62')],
            foreground=[('readonly', '#fff')]
        )
        # --- Create the sort dropdown with the custom style ---
        sort_options = ttk.Combobox(
            search_frame,
            values=["Name (A-Z)", "Name (Z-A)", "Username (A-Z)", "Username (Z-A)"],
            font=('Segoe UI', 10),
            width=14,
            state='readonly',
            style="Theme.TCombobox"
        )
        sort_options.pack(side=tk.LEFT, padx=(10, 20), ipady=6)
        sort_options.set("Name (A-Z)")
        sort_options.bind('<<ComboboxSelected>>', lambda e: self.sort_employees(sort_options.get()))

        table_frame = tk.Frame(card_frame, bg='#F9F9F9')
        table_frame.pack(fill=tk.BOTH, expand=True, padx=28, pady=(0, 24))
        columns = ('ID', 'Name', 'Username', 'Password', 'Express Alloc', 'Junior Alloc', 'Regular Alloc', 'Student Alloc', 'PWD Alloc', 'Senior Alloc', 'Month Sales')
        style = ttk.Style()
        style.configure('Treeview', font=('Segoe UI', 11), rowheight=32, background='#FFFFFF', fieldbackground='#FFFFFF', borderwidth=0)
        style.configure('Treeview.Heading', font=('Segoe UI', 11, 'bold'), background='#E0E0E0', foreground='#9A4E62', borderwidth=0)
        style.layout('Treeview', [('Treeview.treearea', {'sticky': 'nswe'})])
        self.emp_tree = ttk.Treeview(table_frame, columns=columns, show='headings', style='Treeview')
        self.emp_tree.heading('ID', text='Employee ID')
        self.emp_tree.column('ID', width=120, anchor='center')
        self.emp_tree.heading('Name', text='Name')
        self.emp_tree.column('Name', width=160, anchor='w')
        self.emp_tree.heading('Username', text='Username')
        self.emp_tree.column('Username', width=140, anchor='w')
        self.emp_tree.heading('Password', text='Password')
        self.emp_tree.column('Password', width=140, anchor='w')
        alloc_columns = [ ('Express Alloc', 'Express Pass'), ('Junior Alloc', 'Junior Pass'), ('Regular Alloc', 'Regular Pass'), ('Student Alloc', 'Student Pass'), ('PWD Alloc', 'PWD Pass'), ('Senior Alloc', 'Senior C Pass') ]
        self.emp_tree.heading('Month Sales', text='Month Sales')
        self.emp_tree.column('Month Sales', width=140, anchor='e')
        for col, header in alloc_columns:
            self.emp_tree.heading(col, text=header)
            self.emp_tree.column(col, width=110, anchor='center')
        self.emp_tree.pack(fill=tk.BOTH, expand=True, pady=0)
        def clear_selection_on_click(event):
            region = self.emp_tree.identify("region", event.x, event.y)
            if region == "nothing":
                self.emp_tree.selection_remove(self.emp_tree.selection())
        self.emp_tree.bind("<Button-1>", clear_selection_on_click, add="+")
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.emp_tree.yview)
        self.emp_tree.configure(yscrollcommand=scrollbar.set)
        self.emp_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.load_employees()

    def show_customers(self):
        self.clear_content()
        self.set_active_sidebar('👥  Customers')
        card_frame = self.create_main_content_frame()
        # Title and subtitle with themed background and padding
        customer_title = tk.Label(card_frame, text="Customers", font=('Arial', 20, 'bold'), bg='#F0E7D9', anchor='w')
        customer_title.pack(pady=(20, 0), padx=30, anchor='w')
        customer_subtitle = tk.Label(card_frame, text="View All Customers and Ticket Sales", font=('Arial', 15), fg='#6b7280', bg='#F0E7D9', anchor='w')
        customer_subtitle.pack(pady=(0, 10), padx=30, anchor='w')
        # Controls frame with themed background
        controls_frame = tk.Frame(card_frame, bg='#F0E7D9')
        controls_frame.pack(fill=tk.X, pady=10)
        # Search/sort bar with maroon background
        search_sort_frame = tk.Frame(controls_frame, bg='#9A4E62')
        search_sort_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        # Search label (white background for contrast)
        tk.Label(search_sort_frame, text="Search:", bg='white').pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.search_customers)
        search_entry = tk.Entry(search_sort_frame, textvariable=self.search_var, font=('Arial', 11), width=40)
        search_entry.pack(side=tk.LEFT, padx=5)
        tk.Label(search_sort_frame, text="Sort by:", bg='white').pack(side=tk.LEFT, padx=5)
        sort_options = ttk.Combobox(search_sort_frame, values=["Name (A-Z)", "Name (Z-A)", "Date (Newest)", "Date (Oldest)"])
        sort_options.pack(side=tk.LEFT, padx=5)
        sort_options.set("Name (A-Z)")
        sort_options.bind('<<ComboboxSelected>>', lambda e: self.sort_customers(sort_options.get()))
        buttons_frame = tk.Frame(controls_frame, bg='white')
        buttons_frame.pack(side=tk.RIGHT, padx=10)
        delete_btn = tk.Button(buttons_frame, text="Delete", command=self.delete_customer, bg='#f44336', fg='white')
        delete_btn.pack(side=tk.LEFT, padx=5)
        tree_frame = tk.Frame(card_frame, bg='white')
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        columns = ('Ticket ID', 'Name', 'Email', 'Pass Type', 'Quantity', 'Amount', 'Booked Date', 'Purchased Date', 'Employee')
        self.customers_tree = ttk.Treeview(tree_frame, columns=columns, show='headings')
        for col in columns:
            self.customers_tree.heading(col, text=col)
            self.customers_tree.column(col, width=120)
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.customers_tree.yview)
        self.customers_tree.configure(yscrollcommand=scrollbar.set)
        self.customers_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        def clear_selection_on_click(event):
            region = self.customers_tree.identify("region", event.x, event.y)
            if region == "nothing":
                self.customers_tree.selection_remove(self.customers_tree.selection())
        self.customers_tree.bind("<Button-1>", clear_selection_on_click, add="+")
        self.load_customers_data()

    def show_cancellations(self):
        self.clear_content()
        self.set_active_sidebar('❌  Cancellations & Refunds')
        # Create the main content card (rounded, modern look)
        card_frame = self.create_main_content_frame()
        # Title: Cancellations and Refunds, styled to match the app (font size 20, bold)
        cancel_title = tk.Label(card_frame, text="Cancellations and Refunds", font=('Arial', 20, 'bold'), bg='#F0E7D9', anchor='w')
        cancel_title.pack(pady=(20, 0), padx=30, anchor='w')
        # Subtitle: View and Manage Customers Submitted Refund Requests, font size 15, gray
        cancel_subtitle = tk.Label(card_frame, text="View and Manage Customers Submitted Refund Requests", font=('Arial', 15), fg='#6b7280', bg='#F0E7D9', anchor='w')
        cancel_subtitle.pack(pady=(0, 15), padx=30, anchor='w')
        # Controls frame for search, sort, and action buttons
        controls_frame = tk.Frame(card_frame, bg='white')
        controls_frame.pack(fill=tk.X, pady=10)
        # Search bar and sort dropdown (left side)
        search_frame = tk.Frame(controls_frame, bg='white')
        search_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(search_frame, text="Search:", bg='white').pack(side=tk.LEFT, padx=5)
        self.cancel_search_var = tk.StringVar()
        self.cancel_search_var.trace('w', self.search_cancellations)
        search_entry = tk.Entry(search_frame, textvariable=self.cancel_search_var, font=('Arial', 11), width=30)
        search_entry.pack(side=tk.LEFT, padx=5)
        tk.Label(search_frame, text="Sort by:", bg='white').pack(side=tk.LEFT, padx=5)
        sort_options = ttk.Combobox(search_frame, values=["Name (A-Z)", "Name (Z-A)", "Date (Newest)", "Date (Oldest)", "Status (A-Z)", "Status (Z-A)"])
        sort_options.pack(side=tk.LEFT, padx=5)
        sort_options.set("Name (A-Z)")
        sort_options.bind('<<ComboboxSelected>>', lambda e: self.sort_cancellations(sort_options.get()))
        # Action buttons (right side)
        buttons_frame = tk.Frame(controls_frame, bg='white')
        buttons_frame.pack(side=tk.RIGHT, padx=10)
        edit_btn = tk.Button(buttons_frame, text="Edit Status", command=self.edit_cancellation_status, bg='#4CAF50', fg='white')
        edit_btn.pack(side=tk.LEFT, padx=5)
        delete_btn = tk.Button(buttons_frame, text="Delete", command=self.delete_cancellation, bg='#f44336', fg='white')
        delete_btn.pack(side=tk.LEFT, padx=5)
        # Table frame for cancellations/refunds
        tree_frame = tk.Frame(card_frame, bg='white')
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        # Define columns for the table
        columns = ('Ticket ID', 'Name', 'Email', 'Pass Type', 'Reason', 'Quantity', 'Amount', 'Booked Date', 'Purchased Date', 'Status')
        self.cancellations_tree = ttk.Treeview(tree_frame, columns=columns, show='headings')
        # Set column widths for better readability
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
        # Add vertical scrollbar to the table
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.cancellations_tree.yview)
        self.cancellations_tree.configure(yscrollcommand=scrollbar.set)
        self.cancellations_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        # Clear selection if user clicks on empty space in the table
        def clear_selection_on_click(event):
            region = self.cancellations_tree.identify("region", event.x, event.y)
            if region == "nothing":
                self.cancellations_tree.selection_remove(self.cancellations_tree.selection())
        self.cancellations_tree.bind("<Button-1>", clear_selection_on_click, add="+")
        # Load the data from the database into the table
        self.load_cancellations_data()

    def show_pricing(self):
        self.clear_content()
        self.set_active_sidebar('💳  Pricing')
        # Create the main content card (rounded, modern look)
        card_frame = self.create_main_content_frame()
        # Title: Pass Type Pricing, styled to match the app (font size 20, bold)
        pricing_title = tk.Label(card_frame, text="Pass Type Pricing", font=('Arial', 20, 'bold'), bg='#F0E7D9', anchor='w')
        pricing_title.pack(pady=(20, 0), padx=30, anchor='w')
        # Label for showing price update status/messages
        self.price_update_label = tk.Label(card_frame, text="", font=('Arial', 10), fg='#4CAF50', bg='#F0E7D9', anchor='w')
        self.price_update_label.pack(pady=(5, 0), padx=20, anchor='w')
        # Subtitle: View and Manage Ticketing Pricing, font size 15, gray
        pricing_subtitle = tk.Label(card_frame, text="View and Manage Ticketing Pricing", font=('Arial', 15), fg='#6b7280', bg='#F0E7D9', anchor='w')
        pricing_subtitle.pack(pady=(0, 15), padx=30, anchor='w')

        # Rounded card for pricing table
        card_w, card_h, card_r = 800, 400, 35  # Card size and radius
        pricing_card_canvas = tk.Canvas(card_frame, width=card_w, height=card_h, bg='#F0E7D9', highlightthickness=0)
        pricing_card_canvas.pack(padx=0, pady=0)
        # Draw the rounded rectangle for the card background
        draw_rounded_rect(pricing_card_canvas, 0, 0, card_w, card_h, card_r, fill='white', outline='')
        # Frame inside the card for the pricing table
        pricing_inner = tk.Frame(pricing_card_canvas, bg='white')
        pricing_card_canvas.create_window((card_w//2, card_h//2), window=pricing_inner, anchor='center', width=card_w-30, height=card_h-30)

        # Load pricing data from the database
        conn = sqlite3.connect('funpass.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM pricing')
        prices = cursor.fetchall()
        conn.close()
        self.price_entries = {}
        for pass_type, current_price in prices:
            # Row for each pass type
            row = tk.Frame(pricing_inner, bg='white', name=f"price_row_{pass_type.replace(' ', '_').lower()}")
            row.pack(fill=tk.X, pady=10, padx=30)
            # Pass type label
            label = tk.Label(row, text=pass_type, font=('Arial', 12), bg='white', width=20, anchor='w')
            label.pack(side=tk.LEFT, padx=(20, 10))
            # Frame for price entry and currency
            price_frame = tk.Frame(row, bg='white')
            price_frame.pack(side=tk.LEFT)
            # Peso sign label
            currency_label = tk.Label(price_frame, text="₱", font=('Arial', 12), bg='white')
            currency_label.pack(side=tk.LEFT, padx=(0, 5))
            # StringVar for price entry
            price_var = tk.StringVar(value=f"{float(current_price):.2f}")
            # Validation for price input (only allow valid numbers)
            def validate_price(action, value_if_allowed):
                if action == '1':
                    if value_if_allowed == "":
                        return True
                    try:
                        cleaned_value = value_if_allowed.replace(',', '')
                        if cleaned_value.count('.') <= 1 and cleaned_value.replace('.', '').replace('-', '', 1).isdigit():
                            if cleaned_value not in ['.', '-']:
                                return True
                    except ValueError:
                        pass
                    return False
                return True
            # Entry widget for price (editable)
            entry = tk.Entry(price_frame, textvariable=price_var, font=('Arial', 12), width=10, justify='right', name=f"price_entry_{pass_type.replace(' ', '_').lower()}")
            entry.pack(side=tk.LEFT)
            self.price_entries[pass_type] = price_var
            vcmd = (entry.register(validate_price), '%d', '%P')
            entry.configure(validate="key", validatecommand=vcmd)
            # Highlight entry in red if invalid input
            def on_invalid_input(event):
                widget = event.widget
                if widget.get():
                    try:
                        float(widget.get().replace(',', ''))
                        widget.config(fg='black')
                    except ValueError:
                        widget.config(fg='red')
            entry.bind('<KeyRelease>', on_invalid_input)

        # Frame for Save and Reset buttons
        btn_frame = tk.Frame(card_frame, bg='#F0E7D9')
        btn_frame.pack(pady=20)
        # Save Changes button (green)
        save_btn = tk.Button(btn_frame, text="Save Changes", command=self.save_prices, bg='#4CAF50', fg='white', font=('Arial', 11, 'bold'), width=15, height=2)
        save_btn.pack(side=tk.LEFT, padx=10)
        # Reset button (red)
        reset_btn = tk.Button(btn_frame, text="Reset", command=self.reset_prices, bg='#f44336', fg='white', font=('Arial', 11, 'bold'), width=15, height=2)
        reset_btn.pack(side=tk.LEFT, padx=10)
        # Show last updated time
        self.price_update_label.config(text=f"Last updated: {time.strftime('%m/%d/%Y %H:%M:%S')}")

    def save_prices(self):
        try:
            # Validate that all prices are valid numbers and store them
            new_prices = {}
            for pass_type, price_var in self.price_entries.items():
                try:
                    # Remove any commas and spaces from the price string
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
        
        # to clear current display
        for item in self.emp_tree.get_children():
            self.emp_tree.delete(item)
            
        # to get all employees from database   
        conn = sqlite3.connect('funpass.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM employees')
        employees = cursor.fetchall()
        conn.close()
        
        # to filter and display matching employees
        for employee in employees:
            # to search in all fields
            if any(search_text in str(value).lower() for value in employee):
                self.emp_tree.insert('', tk.END, values=employee)

    def sort_employees(self, sort_option):
        # to get all items
        items = []
        for item in self.emp_tree.get_children():
            values = self.emp_tree.item(item)['values']
            items.append(values)

        # to sort based on selected option
        if sort_option == "Name (A-Z)":
            items.sort(key=lambda x: x[1])  # to sort by name ascending
        elif sort_option == "Name (Z-A)":
            items.sort(key=lambda x: x[1], reverse=True)  # to sort by name descending
        elif sort_option == "Username (A-Z)":
            items.sort(key=lambda x: x[2])  # to sort by username ascending
        elif sort_option == "Username (Z-A)":
            items.sort(key=lambda x: x[2], reverse=True)  # to sort by username descending

        # to clear and reload table
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
        if sort_option == "Name (A-Z)":
            items.sort(key=lambda x: x[1])
        elif sort_option == "Name (Z-A)":
            items.sort(key=lambda x: x[1], reverse=True)
        elif sort_option == "Date (Newest)":
            items.sort(key=lambda x: x[7], reverse=True)
        elif sort_option == "Date (Oldest)":
            items.sort(key=lambda x: x[7])
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

        # to get current values
        current_values = self.cancellations_tree.item(selected_item[0])['values']
        
        # to create edit window
        edit_window = tk.Toplevel(self.root)
        edit_window.title("Edit Cancellation Status")
        edit_window.geometry("400x300")
        edit_window.configure(bg='white')

        # to create edit frame
        edit_frame = tk.Frame(edit_window, bg='white', padx=20, pady=20)
        edit_frame.pack(fill=tk.BOTH, expand=True)

        # to show current status
        tk.Label(edit_frame, text="Current Status:", font=('Arial', 11, 'bold'), 
        bg='white').pack(pady=5)
        tk.Label(edit_frame, text=current_values[9], font=('Arial', 11), 
                bg='white').pack(pady=5)

        # to create new status selection
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
            # to get ticket ID
            ticket_id = self.cancellations_tree.item(selected_item[0])['values'][0]

            # to delete from database
            conn = sqlite3.connect('funpass.db')
            cursor = conn.cursor()
            cursor.execute('DELETE FROM cancellations WHERE ticket_id = ?', (ticket_id,))
            conn.commit()
            conn.close()

            # to remove from treeview
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
        if sort_option == "Name (A-Z)":
            items.sort(key=lambda x: x[1])
        elif sort_option == "Name (Z-A)":
            items.sort(key=lambda x: x[1], reverse=True)
        elif sort_option == "Date (Newest)":
            items.sort(key=lambda x: x[8], reverse=True)
        elif sort_option == "Date (Oldest)":
            items.sort(key=lambda x: x[8])
        elif sort_option == "Status (A-Z)":
            items.sort(key=lambda x: x[9])
        elif sort_option == "Status (Z-A)":
            items.sort(key=lambda x: x[9], reverse=True)
        for item in self.cancellations_tree.get_children():
            self.cancellations_tree.delete(item)
        for item in items:
            self.cancellations_tree.insert('', tk.END, values=item)

    def load_cancellations_data(self):
        for item in self.cancellations_tree.get_children():
            self.cancellations_tree.delete(item)
        conn = sqlite3.connect('funpass.db')
        cursor = conn.cursor()
        cursor.execute('''            SELECT ticket_id, name, email, pass_type, reasons, quantity, amount,
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
        # to clear existing items
        for item in self.emp_tree.get_children():
            self.emp_tree.delete(item)
            
        # to load from database
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
            emp_list.append(f"₱{net_monthly_sales:,.2f}")  # Add monthly sales at the end

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
        dialog.geometry("500x750")  # Made taller to accommodate the new fields
        dialog.configure(bg='white')

        # to create main frame
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
            label = tk.Label(field_frame, text=label_text, bg='white', font=('Arial', 11), width=12, anchor='e')
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
            label = tk.Label(field_frame, text=label_text, bg='white', font=('Arial', 11), width=12, anchor='e')
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

if __name__ == "__main__":
    create_database()  # to initialize the database
    root = tk.Tk()
    app = AdminDashboard(root)
    root.mainloop()