# Automated Wireless Research Tester v0.9.2
## About The Project

* The goal of this project is to create software which will automatically <br />
operate antenna measurement equipment and collect/display antenna pattern measurements.
* The software is designed to be used by engineers at the Wireless Research Center<br /> 
(WRC) and technicians who work with them. 
* The software was tested to be used with the HP 8753D Vector Network Analyzer <br />
and the QPT-130 Positioner.

### What's in the Source Code?
* `AutomatedWirelessResearchTester.exe` is the packaged executable file which <br />
can be run on any Windows OS without prerequisites.
* The `data_processing` folder contains code related to plotting antenna measurements.
* The `gui` folder contains code related to user interface design/logic.
* The `measurement_ctrl` folder contains code related to the control and <br />
operation of the positioner and VNA.
* `mainWindow_app.py` is the top-level code for the software.
* Any `.bat` or `.spec` files are used for automating the repackaging process.


### Built With

* Python 3.8
* PyQt5 (5.15.1)
* PyVISA (1.11.1)
* Matplotlib (3.2.2)
* Pandas (1.1.4)
* Numpy (1.19.3)
* PyInstaller (4.0)


## Getting Started

1. Install NI-VISA and NI-488.2 Drivers to your computer.
2. To run the software, simply open `AutomatedWirelessResearchTester.exe`. 
3. For detailed instructions on how to use/modify the software, view `User Manual.pdf`.

### Repackaging the code

1. Run `gui/ui2py.bat` if you have made changes to the `.ui` files.
2. Run `resources.bat` if you have made changes to any image resources in the project.
3. Run `build.bat`. Batch file will check for prerequisites, and then source <br />
code will be packaged using PyInstaller.


## License

Distributed under the MIT License. See `LICENSE` for more information.