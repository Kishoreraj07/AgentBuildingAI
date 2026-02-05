def switch_to_window(driver, window_index):
    handles = driver.window_handles
    if len(handles)-1 < window_index:
        pass
    else:
        driver.switch_to.window(handles[window_index])
