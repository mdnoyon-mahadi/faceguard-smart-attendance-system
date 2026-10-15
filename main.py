

from database.db_connection import test_connection
from views.splash_screen import SplashScreen
import sys
import os


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    print("=" * 50)
    print(f"  Face Recognition Attendance System")
    print("=" * 50)

    # Create the single global root window (hidden)
    import customtkinter as ctk
    ctk.set_appearance_mode("dark")
    root = ctk.CTk()
    root.withdraw()

    # DB connection check
    if not test_connection():
        from tkinter import messagebox
        messagebox.showerror(
            "Database Error",
            "Could not connect to the MySQL database!\n\n"
            "1. Check whether the MySQL service is running\n"
            "2. Verify the password in the .env file\n"
            "3. Run python setup.py again"
        )
        root.destroy()
        sys.exit(1)

    # Launch the application via the splash screen Toplevel
    app = SplashScreen(master=root)
    root.mainloop()


if __name__ == "__main__":
    main()  