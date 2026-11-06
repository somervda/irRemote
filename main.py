from machine import Pin
import time
import sys

button = Pin(15, Pin.IN, Pin.PULL_UP)

# the app will start when booted if the button on pin 15 is 
# not engaged (default behavior). If the button is depressed
# then app.py is not run and you can work with the python files.
# if button.value() == 1:  
if button.value() == 0:
    print("** Application auto started **")
    try:
        import bt_ir
    except Exception as e:
        print("Exception: Restarting",e)
        f=open('exception.txt', 'a')  
        f.write(str(time.localtime()) + "\n")
        sys.print_exception(e,f)
        f.close()
        time.sleep(2)
        machine.reset()
else:
    print("** No auto start of app, manually run app to test **")
