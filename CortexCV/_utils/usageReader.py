import psutil

def getUsage():
    while True:
        try:
            CPU = psutil.cpu_percent(1)
            RAM = psutil.virtual_memory().percent
            return CPU, RAM
        except KeyboardInterrupt:
            break

