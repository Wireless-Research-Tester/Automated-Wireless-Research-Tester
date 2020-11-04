pip install PyQt5==5.15.1
pip install matplotlib==3.2.2
pip install pandas==1.1.4 
pip install numpy==1.19.3
pip install pyvisa==1.11.1
::pip install pyvisa-py==0.5.1
pip install pyinstaller==4.0
pyinstaller build.spec
move dist\AutomatedWirelessResearchTester.exe AutomatedWirelessResearchTester.exe
rmdir /S/Q dist
rmdir /S/Q build
