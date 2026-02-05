import ctypes
def popup_message_box(msg):
    msg = str(msg)
    ctypes.windll.user32.MessageBoxW(0, msg, "Agent Message", 0x40 | 0x1)  # 0x40: MB_TOPMOST, 0x1: MB_OK
