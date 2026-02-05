@echo off
echo Building ABA executable with all required modules...

pyinstaller --onefile --noconsole --icon=icon_3.ico ^
--add-data "font;font" ^
--add-data "gif;gif" ^
--add-data "Icon;Icon" ^
--add-data "json_info;json_info" ^
--add-data "sound;sound" ^
--add-data "code_py;code_py" ^
--add-data "styles;styles" ^
--add-data "video_transcript_pdf_output;video_transcript_pdf_output" ^
--add-data "xpath_find.py;." ^
--add-data "element_confirmation.py;." ^
--add-data "verify_xpath.py;." ^
--add-data "config.py;." ^
--name=ABA login_page.py

echo Build completed!
pause
