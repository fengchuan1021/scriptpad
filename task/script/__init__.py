def __getattr__(name):

    return __import__(f"task.script.{name}",globals(),locals(),'Main')



