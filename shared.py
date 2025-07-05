"""
This module contains utilities and UI elements shared between modules.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from tkcalendar import DateEntry
from datetime import datetime
import sqlite3
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import random
import string

# Common database functions
def create_database():
    conn = sqlite3.connect('funpass.db')
    cursor = conn.cursor()
    
    # Employees table
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
    
    # Admin table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin (
            admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    
    # Insert default admin if not exists
    cursor.execute('SELECT * FROM admin WHERE username = ?', ('admin',))
    if not cursor.fetchone():
        cursor.execute('INSERT INTO admin (username, password) VALUES (?, ?)', ('admin', 'admin'))

    # Customers table
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

    # Cancellations table
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

    # Pricing table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pricing (
            pass_type TEXT PRIMARY KEY,
            price REAL NOT NULL
        )
    ''')

    # Insert default pricing if table is empty
    cursor.execute('SELECT COUNT(*) FROM pricing')
    if cursor.fetchone()[0] == 0:
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

# Common UI utilities
class BaseWindow:
    def center_window(self):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = 800
        window_height = 600
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
