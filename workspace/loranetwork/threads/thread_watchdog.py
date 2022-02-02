from threading import Thread
import time

from utils.api_utils import getDeviceKeys


class ThreadWatchdog(Thread):
    def __init__(self, watchdog, threadLock, criticalSectionLock):
        Thread.__init__(self)
        self.watchdog = watchdog
        self.threadLock = threadLock #serve per non accedere allo stesso gateway contemporaneamente
        self.criticalSectionLock = criticalSectionLock
        self._running = True

    def run(self):
        resp = getDeviceKeys(self.watchdog.devEUI)
        self.watchdog.app_key = resp.device_keys.nwk_key
        self.threadLock.acquire()
        self.watchdog.join()
        self.threadLock.release()
        while self._running:
            currentMillis = round(time.time() * 1000)
            if (currentMillis - self.watchdog.previousMillisS) > self.watchdog.timetosend:
                self.criticalSectionLock.acquire()
                self.threadLock.acquire()
                self.watchdog.send_data()
                self.threadLock.release()
                self.criticalSectionLock.release()
                self.watchdog.previousMillisS = currentMillis

    def stop(self):
        self._running = False
        print("thread_watchdog stoped")


