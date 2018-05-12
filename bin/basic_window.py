#! /usr/bin/python
import game_core


class BasicWindow(game_core.AbstractWindow):
    def __init__(self):
        super(BasicWindow, self).__init__()
        self.title = 'Basic Window'

    def keyboard_event(self, key, scancode, action, mods):
        """
        Args:
            key (int): The keyboard key that was pressed or released.
            scancode (int): The system-specific scancode of the key.
            action (int): glfw.PRESS, glfw.RELEASE or glfw.REPEAT.
            mods (int): Bit field describing which modifier keys were held down.
        """
        print 'key pressed: key={}  scancode={}  action={}  mods={}'.format(key, scancode, action, mods)
        super(BasicWindow, self).keyboard_event(key, scancode, action, mods)

    def mouse_button_event(self, button, action, mods):
        """Called when a mouse button is pressed or released

        :param int button: The pressed/released mouse button
        :param int action: glfw.PRESS or glfw.RELEASE
        :param int mods: Bit field describing which modifier keys were held down.
        """
        print 'button pressed: button={}  action={}  mods={}'.format(button, action, mods)

    def reshape(self, w, h):
        print 'reshaping: w={} h={}'.format(w, h)
        super(BasicWindow, self).reshape(w, h)

    def integrate(self, t, delta_time):
        pass

    def draw(self):
        pass


if __name__ == '__main__':
    BasicWindow().run()

