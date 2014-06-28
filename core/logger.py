class Logger(object):
    TAB_LEVEL = 0
    def __init__(self, message):
        self._message = message

    def __enter__(self):
        self.log()
        self.increase_tab()

    def __exit__(self, *args, **kwargs):
        self.decrease_tab()

    @classmethod
    def increase_tab(cls):
        cls.TAB_LEVEL += 1

    @classmethod
    def decrease_tab(cls):
        cls.TAB_LEVEL -= 1

    def log(self, new_line=True):
        messages = self._message.split('\n')
        for m in messages[:-1]:
            print ('|   '*self.TAB_LEVEL) + m
        if new_line:
            print ('|   '*self.TAB_LEVEL) + messages[-1]
        else:
            print ('|   '*self.TAB_LEVEL) + messages[-1],

def log(message, new_line=True):
    logger = Logger(message)
    logger.log(new_line=new_line)

def increase_tab(self):
    Logger.increase_tab()

def decrease_tab(self):
    Logger.decrease_tab()

