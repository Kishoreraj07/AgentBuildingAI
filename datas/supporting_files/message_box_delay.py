import tkinter as tk
from tkinter import messagebox
import time

 
def close_message_box():
    message_box.destroy()

def show_timed_message_box(msg):
    delay=1
    root = tk.Tk()
    root.withdraw()
 

    global message_box
    message_box = tk.Toplevel(root)
    message_box.title("Bot Message")

    # Display message in the message box
    message_label = tk.Label(message_box, text=msg)
    message_label.pack(padx=120, pady=120)

    # Auto-close the message box after 5 seconds
    root.after(delay*1000, close_message_box)
    root.after(delay*1000,root.destroy)
   
    # Run the Tkinter event loop
    root.mainloop()

# Call the function to show the timed message box
#show_timed_message_box("msg", 5)


