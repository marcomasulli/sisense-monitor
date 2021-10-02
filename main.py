from time import sleep
from sisense_monitor import check_builds

if __name__ == "__main__":
    while True:
        check_builds()
        sleep(30)
