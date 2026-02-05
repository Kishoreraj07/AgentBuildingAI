import time
import win32gui
import win32con
import win32process
import win32api
import pygetwindow as gw
import pyautogui

def force_activate_window(title_keyword: str):
    windows = gw.getWindowsWithTitle(title_keyword)
    if not windows:
        raise Exception("Window not found")

    win = windows[0]
    hwnd = win._hWnd

    # Get thread IDs
    fg_hwnd = win32gui.GetForegroundWindow()
    fg_thread, _ = win32process.GetWindowThreadProcessId(fg_hwnd)
    target_thread, _ = win32process.GetWindowThreadProcessId(hwnd)

    # Attach threads
    win32process.AttachThreadInput(target_thread, fg_thread, True)

    # Restore + bring to front
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    win32gui.SetWindowPos(
        hwnd,
        win32con.HWND_TOP,
        0, 0, 0, 0,
        win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW
    )

    win32gui.SetForegroundWindow(hwnd)
    time.sleep(0.3)

    # Detach threads
    win32process.AttachThreadInput(target_thread, fg_thread, False)

def set_zoom(driver, percentage: int):

    # Force browser focus
    title = driver.title[:10]
    try:
        force_activate_window(title)
    except:
        pass

    # Reset zoom
    pyautogui.hotkey('ctrl', '0')
    time.sleep(0.4)

    if 90 <= percentage <= 100:
        times = 1
    elif 80 <= percentage < 90:
        times = 2
    elif 75 <= percentage < 80:
        times = 3
    elif 67 <= percentage < 75:
        times = 4
    else:
        times = 5

    for _ in range(times):
        pyautogui.hotkey('ctrl', '-')
        time.sleep(0.3)