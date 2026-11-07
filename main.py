from machine import Pin
import time
import sys
button = Pin(15, Pin.IN, Pin.PULL_UP)

# the app will start when booted if the button on pin 15 is 
# not engaged (default behavior). If the button is depressed
# then app.py is not run and you can work with the python files.
# if button.value() == 0:  
if button.value() == 1:
    print("** Application auto started **")
    try:
        import bt_ir
    except Exception as e:
        print("Exception: Restarting",e)
        with open('exception.txt', 'a')  as f:
            # 1. Get the local time tuple 
            # (year, month, mday, hour, minute, second, weekday, yearday)
            t = time.localtime()
            # 2. Format using an f-string with zero-padding (:02d means 2 digits, padded with 0)
            readable_time = f"{t[0]}-{t[1]:02d}-{t[2]:02d} {t[3]:02d}:{t[4]:02d}:{t[5]:02d}"
            f.write(f"{readable_time}: " + "\n")
            sys.print_exception(e,f)
        time.sleep(2)
        machine.reset()
else:
    print("** No auto start of app, manually run app to test **")
