import pyvisa as visa
rm = visa.ResourceManager()
print("Available resources:")
print(rm.list_resources())
addr = input("GPIB address of the VNA: ")
vna = rm.open_resource('GPIB0::' + addr + '::INSTR')
vna.query('*IDN?')