import tkinter as tk  # Tkinter for GUI
from tkinter import messagebox  # For pop-up messages
from PIL import Image, ImageTk, ImageDraw  # For image handling and drawing
import sqlite3  # For database connection
import os  # For file path operations
from main import AdminDashboard  # Import Admin dashboard
from for_employees import EmployeeDashboard  # Import Employee dashboard

# Keep references to images to prevent garbage collection
image_refs = []

def center_window(root, width=800, height=600):
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    root.geometry(f"{width}x{height}+{x}+{y}")

def get_resample_filter():
    # Use LANCZOS if available, else NEAREST (always exists)
    return getattr(getattr(Image, "Resampling", Image), "LANCZOS", getattr(getattr(Image, "Resampling", Image), "NEAREST", 0))

# Draw a rounded rectangle on a canvas
def draw_rounded_rect(canvas, x1, y1, x2, y2, r, **kwargs):
    points = [
        x1+r, y1, x2-r, y1, x2, y1, x2, y1+r, x2, y2-r, x2, y2,
        x2-r, y2, x1+r, y2, x1, y2, x1, y2-r, x1, y1+r, x1, y1
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)

# Create a rounded Entry widget 
def create_rounded_entry(parent, width=200, height=32, radius=16, bg='#e3eaff', entry_bg='#e3eaff', font=('Arial', 10), show=None):
    if not isinstance(font, tuple):
        font = ('Arial', 10)
    # Create a canvas for the rounded background
    canvas = tk.Canvas(parent, width=width, height=height, bg=str(parent['bg']), highlightthickness=0, bd=0)
    points = [
        radius, 0, width-radius, 0, width, 0, width, radius,
        width, height-radius, width, height, width-radius, height,
        radius, height, 0, height, 0, height-radius, 0, radius, 0, 0
    ]
    canvas.create_polygon(points, smooth=True, fill=str(bg), outline='#CCCCCC')
    # Create the Entry widget on top of the canvas
    entry_args = {
        'font': font,
        'bg': str(entry_bg),
        'bd': 0,
        'highlightthickness': 0,
        'relief': 'flat',
        'justify': 'left',
    }
    if show is not None:
        entry_args['show'] = str(show)
    entry = tk.Entry(canvas, **entry_args)
    entry.place(x=10, y=4, width=width-20, height=height-8)
    canvas.pack(pady=5)
    return entry

# Create a rounded button using a canvas and Pillow image
def create_rounded_button(parent, text, command, width=200, height=40, radius=15, bg='#9A4E62', fg='white', font=('Regular', 12, 'bold')):
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([0, 0, width, height], radius=radius, fill=bg)
    tk_img = ImageTk.PhotoImage(img)
    btn_canvas = tk.Canvas(parent, width=width, height=height, bg=parent['bg'], highlightthickness=0, bd=0)
    btn_canvas.create_image(0, 0, anchor='nw', image=tk_img)
    image_refs.append(tk_img)  # Keep reference globally
    btn_canvas.create_text(width//2, height//2, text=text, fill=fg, font=font)
    btn_canvas.bind("<Button-1>", lambda e=None: command())
    btn_canvas.config(cursor="hand2")
    btn_canvas.pack(pady=30)
    return btn_canvas

# Main Login Window function
def show_login():
    root = tk.Tk()  # Create main window
    root.title("FunPass - Login")
    # Set the window to full screen using geometry
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.geometry(f"{screen_width}x{screen_height}+0+0")
    resample_filter = get_resample_filter()  # Get best image resample filter

    # Try to set a background image
    try:
        image_path = "bg_carousel.jpeg"
        bg_image = Image.open(image_path)
        bg_image_resized = bg_image.resize((screen_width, screen_height), resample_filter)
        bg_photo = ImageTk.PhotoImage(bg_image_resized)
        bg_label = tk.Label(root, image=bg_photo)
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        image_refs.append(bg_photo)
    except Exception as e:
        root.configure(bg='white')
        print(f"Background image error: {e}")

    # Create the login card (rounded rectangle)
    frame_width, frame_height, frame_radius = 400, 600, 50
    login_canvas = tk.Canvas(root, width=frame_width, height=frame_height, highlightthickness=0, bg='#3C476F')
    login_canvas.place(relx=0.5, rely=0.5, anchor='center')
    draw_rounded_rect(login_canvas, 0, 0, frame_width, frame_height, frame_radius, fill='white')
    main_frame = tk.Frame(login_canvas, bg='white')
    login_canvas.create_window((frame_width//2, frame_height//2), window=main_frame, anchor='center')

    # Logo at the top of the login card
    try:
        logo_path = "FunPass__1_-removebg-preview.png"
        logo_img = Image.open(logo_path)
        logo_width = 230
        aspect_ratio = logo_img.height / logo_img.width
        logo_height = int(logo_width * aspect_ratio)
        logo_img = logo_img.resize((logo_width, logo_height), resample_filter)
        logo = ImageTk.PhotoImage(logo_img)
        logo_label = tk.Label(main_frame, image=logo, bg='white')
        logo_label.pack(pady=(30, 0), anchor='center')
        image_refs.append(logo)
    except Exception:
        # Fallback: show text if logo image fails
        tk.Label(main_frame, text="FunPass", font=('Arial', 24, 'bold'), bg='white', fg='#4CAF50').pack(pady=20)

    tk.Label(main_frame, text="For Faculty Members Only", font=('Arial', 10, 'bold'), bg='white', fg='#666666').pack(pady=(0, 20))

    # Login form frame
    form_frame = tk.Frame(main_frame, bg='white')
    form_frame.pack(pady=10)

    # Username label and entry
    username_label_frame = tk.Frame(form_frame, bg='white')
    username_label_frame.pack(fill='x', padx=5)
    tk.Label(username_label_frame, text="Username:", font=('Arial', 10), bg='white', fg='#333333', anchor='w').pack(side='left', pady=5)
    username_entry = create_rounded_entry(form_frame, bg='#e3eaff', entry_bg='#e3eaff')

    # Password label and entry
    password_label_frame = tk.Frame(form_frame, bg='white')
    password_label_frame.pack(fill='x', padx=5)
    tk.Label(password_label_frame, text="Password:", font=('Arial', 10), bg='white', fg='#333333', anchor='w').pack(side='left', pady=5)
    password_entry = create_rounded_entry(form_frame, bg='#e3eaff', entry_bg='#e3eaff', show='*')

    # Show Password Checkbox
    show_password = tk.BooleanVar()
    def toggle_password_visibility():
        password_entry.config(show="" if show_password.get() else "*")
    showpw_frame = tk.Frame(form_frame, bg='white')
    showpw_frame.pack(fill='x', padx=5)
    tk.Checkbutton(
        showpw_frame, text="Show Password", variable=show_password,
        command=toggle_password_visibility, bg='white', fg='#333333', anchor='w'
    ).pack(side='right', pady=5)

    # Login Button
    def login():
        username = username_entry.get().strip()
        password = password_entry.get().strip()
        if not username or not password:
            messagebox.showwarning("Invalid Input", "Please enter both username and password")
            return
        conn = sqlite3.connect('funpass.db')
        cursor = conn.cursor()
        # 1. Check admin credentials
        cursor.execute('SELECT * FROM admin WHERE username = ? AND password = ?', (username, password))
        admin = cursor.fetchone()
        if admin:
            root.destroy()
            admin_root = tk.Tk()
            AdminDashboard(admin_root)
            admin_root.mainloop()
            conn.close()
            return
        # 2. Check employee credentials
        cursor.execute('SELECT employee_id FROM employees WHERE username = ? AND password = ?', (username, password))
        emp = cursor.fetchone()
        if emp:
            root.destroy()
            emp_root = tk.Tk()
            EmployeeDashboard(emp_root, employee_id=emp[0])
            emp_root.mainloop()
        else:
            messagebox.showerror("Login Failed", "Invalid credentials")
        conn.close()

    # Create the rounded login button
    create_rounded_button(form_frame, text="Log In", command=login, width=210, height=35, radius=35)

    # Allow pressing Enter to trigger login
    def on_enter_key(event):
        login()
    root.bind('<Return>', on_enter_key)
    root.mainloop()


if __name__ == "__main__": # Entry point
    show_login()