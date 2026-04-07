import wireless
import webrepl
import time

wireless.connect()

webrepl_password = "burockets"

try:
    import webrepl_cfg
except ImportError:
    #no existing config, make one
    with open("webrepl_cfg.py", 'w') as f:
        f.write(f"PASS = '{webrepl_password}'\n")

webrepl.start()