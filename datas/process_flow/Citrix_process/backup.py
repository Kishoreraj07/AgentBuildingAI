# from datas.process_flow.Citrix_process.table_conf_popup import show_confirmation_popup
from table_conf_popup import show_confirmation_popup
result = show_confirmation_popup("Is this pagination table?")
if result:
    print("User clicked YES")
else:
    print("User clicked NO")