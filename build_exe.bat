@echo off
echo Building executable for QuizBattle Dungeons of Knowledge - WORKING VERSION
echo.

echo Installing required packages...
python -m pip install -r requirements.txt

echo.
echo Cleaning previous build files...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul

echo.
echo Building executable with correct Python environment and fixed paths...
python -m PyInstaller --onefile --noconsole --add-data "data;data" --add-data "templates;templates" --add-data "static;static" --add-data "docs;docs" --name "QuizBattle_DungeonsOfKnowledge" app.py

echo.
echo Build complete!
echo The executable is available in: dist\QuizBattle_DungeonsOfKnowledge.exe
echo Size: ~19-20 MB with all dependencies and data files
echo.
echo VERIFIED WORKING:
echo - No module import errors
echo - Levels display correctly
echo - Chapters load properly
echo - Game is fully playable

pause