import time
from collections import OrderedDict
from typing import Dict


class Timer(object):
    def __init__(self, name, start=False, log=False):
        """
        :param str name: The name of the timer
        :param bool start: start the timer now?
        :param bool log: log time when exiting the context manager?
            only applicable when the timer is used as a context manager
        """
        self.name = name
        self.time = 0.0
        self._start_time = None
        if start:
            self._start_time = time.time()
        self._log = log
        self._timers = OrderedDict()  # type: Dict[str, Timer]

    def add_timer(self, name, start=False):
        # type: (str, bool) -> Timer
        if name not in self._timers:
            self._timers[name] = Timer(name, start=start)
        return self._timers[name]

    def get_timer(self, name):
        # type: (str) -> Timer
        return self._timers[name]

    def start(self, clear=False):
        if clear:
            self.time = 0.0
        elif self._start_time is not None:
            self.stop()
        self._start_time = time.time()

    def stop(self, log=False):
        try:
            self.time += time.time() - self._start_time
        except TypeError:
            if self._start_time is not None:
                raise
            else:
                pass
        self._start_time = None
        if log:
            self.log()

    def log(self, indent=0):
        print '%s%s time: %s' % ('| '*indent, self.name, self.time)
        sub_timer_time = 0.0
        for timer in self._timers.values():
            timer.log(indent=indent+1)
            sub_timer_time += timer.time
        if self._timers and sub_timer_time < self.time:
            print '%s__untracked__ time: %s' % ('| '*(indent+1), self.time-sub_timer_time)

    def __enter__(self):
        self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop(log=self._log)
