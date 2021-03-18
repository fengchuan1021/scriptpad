def __getattr__(name):

    return __import__(f"scriptpad.script.{name}",globals(),locals(),'Main')



