import colorama
import sys
import os
import threading
import time
import textwrap
import cursor

lock = threading.Lock()


def _get_cursor_position_posix():
    import termios
    print("\033[6n", end="", flush=True)
    fd = sys.stdin.fileno()
    oldterm = termios.tcgetattr(fd)
    newattr = termios.tcgetattr(fd)
    newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
    termios.tcsetattr(fd, termios.TCSANOW, newattr)
    try:
        sys.stdin.read(2)
        s = ""
        while True:
            c = sys.stdin.read(1)
            if c == "R":
                break
            s += c
        return tuple(map(int, s.split(";")))
    except IOError:
        pass


def _get_cursor_position_win():
    winterm = colorama.winterm.WinTerm()
    pos = winterm.get_position(handle=colorama.win32.STDOUT)
    return (pos.Y, pos.X)


def get_cursor_position():
    if os.name == 'nt':
        return _get_cursor_position_win()
    elif os.name == 'posix':
        return _get_cursor_position_posix()


def set_cursor_position(y, x):
    sys.stdout.write("\033[%d;%dH" % (y, x))


def cursor_up(x):
    sys.stdout.write("\033[%dA" % x)


def cursor_down(x):
    sys.stdout.write("\033[%dB" % x)


def cursor_right(x):
    sys.stdout.write("\033[%dC" % x)


def cursor_left(x):
    for i in range(0, x):
        sys.stdout.write("\033[D")


def cursor_prev():
    sys.stdout.write("\033[1F")


def cursor_next():
    sys.stdout.write("\033[1E")


def cursor_leftmost():
    sys.stdout.write("\r")


def cursor_save():
    sys.stdout.write("\033[s")


def cursor_restore():
    sys.stdout.write("\033[u")


def clear_line():
    # Erase the entire line
    sys.stdout.write("\033[2K")


class cui():
    class element():
        def __init__(self, message, width, position, widget=None, percentage_required=False):
            self.message = message
            self.width = width
            self.available_msg_width = width - 10
            self.position = position
            self.progress = 0
            self.refresh = False
            self.visible = False
            clear_line()
            if widget == None:
                self.widget = self.bounce_widget()
            else:
                self.widget = widget
            self.progresspos = 0

        def _update_message(self, msg):
            if self.message != msg or self.visible == False:
                clear_line()
                shortmsg = textwrap.shorten(
                    msg, width=self.available_msg_width - 3, placeholder="...")
                sys.stdout.write(shortmsg)
                sys.stdout.flush()
                self.steps = self.width - len(shortmsg) - 2
                # self.steps = self.width
                self.message = shortmsg
                self.visible = True
                self.refresh = True
            else:
                cursor_right(len(self.message))

        def _update_progress(self, value):
            if (value != -1):
                x = int((value * self.steps) / 100)
                for i in range(self.progresspos, x + 1):
                    cursor_leftmost()
                    cursor_right(len(self.message))
                    self.widget.update(self.refresh, self.progresspos, self.steps, (self.position[0], len(self.message) + 1))
                    self.progresspos += 1
            else:
                self.widget.update(self.refresh, self.progresspos, self.steps, (self.position[0], len(self.message) + 1))
                self.progresspos += 1

        def update(self, value=-1, message=""):
            lock.acquire()
            if message == "":
                message = self.message
            self._update_message(message)
            self._update_progress(value)
            lock.release()

        def _finish(self, msg, success):
            self._update_message(msg)
            self.widget.finish(msg, self.steps, (self.position[0], len(self.message) + 1), success)

        def finish(self, message="", success=True):
            if message == "":
                message = self.message
            self._finish(message, success)

        class bounce_widget():
            def __init__(self, marker="<=>"):
                self.bouncestr = marker

            def update(self, refresh, progresspos, steps, pos):
                # Corecting the steps for bouncer sting length
                # (since bouncer string will occupy that space so no need to update that part)
                ori_steps = steps
                steps -= (len(self.bouncestr) - 1)

                if (int(progresspos / steps) % 2) == 0:
                    ppos = progresspos % steps
                    updatebouncestr = (
                        " " if ppos != 0 else "") + self.bouncestr
                    # corecting for space we added above
                    ppos -= 1 if (ppos != 0) else 0
                else:
                    # corecting for space we added below (Note: This won't be conditional)
                    ppos = steps - (progresspos % steps) - 1
                    updatebouncestr = self.bouncestr + \
                        (" " if ppos != (steps - 1) else "")

                if refresh == True:
                    sys.stdout.write("[" + (" " * ppos) + updatebouncestr + (
                        " " * (ori_steps - ppos - (len(updatebouncestr)))) + "]")
                    sys.stdout.flush()
                else:
                    # +1 for offseting '[' character
                    cursor_right(ppos + 1)
                    sys.stdout.write(updatebouncestr)
                    sys.stdout.flush()

            def finish(self, pre_msg, steps, pos, success):
                marker = "*" if success == True else "x"
                sys.stdout.write("[" + marker * steps + "]")

        class default_widget():
            def __init__(self):
                pass

            def update(self, refresh, progresspos, steps, pos):
                if refresh == True:
                    sys.stdout.write("[" + "*" * progresspos + " " * (steps - progresspos) + "] ")
                else:
                    cursor_right(progresspos)
                    sys.stdout.write("*")

            def finish(self, msg, steps, pos, success):
                pass

    def __init__(self, width, tasks=[], header_required=True):
        self.tasklist = []
        self.tmtask = None
        self.noelements = 0
        self.tmhdr_required = header_required
        self.taskoffset = 1 if self.tmhdr_required else 0
        self.elements = []
        self.width = width

        for task in tasks:
            taskentry = {}
            taskentry["func"], taskentry["args"] = task
            taskentry["message"] = "Starting"
            taskentry["element"] = None
            taskentry["thread"] = None
            taskentry["id"] = self.noelements
            taskentry["title"] = "| task %d:" % self.noelements
            taskentry["failed"] = False
            self.tasklist.append(taskentry)
            self.noelements += 1

    def register(self, func, args, title=""):
        taskentry = {}
        taskentry["func"] = func
        taskentry["args"] = args
        taskentry["message"] = "Starting"
        taskentry["element"] = None
        taskentry["thread"] = None
        taskentry["failed"] = False
        taskentry["id"] = self.noelements
        if title == "":
            taskentry["title"] = "| task %d:" % self.noelements
        else:
            taskentry["title"] = "| %s:" % title
        self.tasklist.append(taskentry)
        self.noelements += 1

    def __monitor(self, task):
        try:
            for msg in task["func"](*task["args"]):
                task["message"] = msg
        except:
            task["failed"] = True

    def __task_manager(self, tasklist):
        while True:
            time.sleep(0.01)
            if self.tmhdr_required:
                completed_task = self.noelements - len(tasklist)
                msg = "# of tasks monitored %d/%d" % (completed_task, len(tasklist) + completed_task)
                self.tmtask["element"].update(int((completed_task / self.noelements) * 100), message=msg)
            if len(tasklist) == 0:
                if self.tmhdr_required:
                    self.tmtask["element"].finish()
                break
            for task in tasklist:
                cursor_down(task["id"] + self.taskoffset)
                cursor_leftmost()
                task["element"].update(message=task["title"] + " " + task["message"])
                if not task["thread"].is_alive():
                    cursor_leftmost()
                    task["element"].finish(task["title"] + " " + task["message"], success=not task["failed"])
                    tasklist.remove(task)
                cursor_up(task["id"] + self.taskoffset)
                cursor_leftmost()

    def start(self):
        print("")
        clear_line()
        noelements = self.noelements - 1
        if self.tmhdr_required:
            noelements += 1
        sys.stdout.write("\n" * noelements)
        sys.stdout.write("\033[%dA" % noelements)
        self.uistartpt = (1,1)

        start = 0
        if self.tmhdr_required:
            start = 1

        msg = "# of tasks monitored: %d" % len(self.tasklist)
        element = self.element(msg, self.width, self.uistartpt, widget=self.element.default_widget())
        self.tmtask = {"func": None, "args": None,
                        "message": msg, "element": element, "thread": None}
        thread = threading.Thread(
            target=self.__task_manager, args=(self.tasklist,))
        self.tmtask["thread"] = thread

        for i in range(0, len(self.tasklist)):
            element = self.element("task %d: %s" % (
                i, " starting"), self.width, (self.uistartpt[0] + i + start, self.uistartpt[1]))
            self.tasklist[i]["element"] = element
            self.tasklist[i]["message"] = "starting"
            thread = threading.Thread(
                target=self.__monitor, args=(self.tasklist[i],))
            self.tasklist[i]["thread"] = thread
            thread.isDaemon = True
            self.tasklist[i]["thread"].start()

        self.tmtask["thread"].start()
        self.tmtask["thread"].join()

    def finish(self):
        noelements = self.noelements - 1
        if self.tmhdr_required:
            noelements += 1
        # set the cursor position to appropriate end location
        cursor_leftmost()
        cursor_down(noelements)
        print("")


if __name__ == "__main__":
    def test(x):
        # To update the status, yield
        yield "status 1"
        time.sleep(x)
        yield "status 2"
        time.sleep(2)
        yield "done"
        if x == 5:
            raise("")

    colorama.init()
    cursor.hide()
    cui = cui(80)
    cui.register(test, (2,))
    cui.register(test, (3,))
    cui.register(test, (5,))
    cui.register(test, (2,))
    cui.register(test, (2,))
    cui.register(test, (2,))
    cui.register(test, (2,))
    cui.register(test, (2,))
    cui.register(test, (2,))
    cui.register(test, (2,))
    cui.register(test, (2,))
    cui.register(test, (2,))
    cui.register(test, (2,))
    cui.register(test, (1,), title="custom title")
    cui.register(test, (4,), title="custom title tooooooooooooooooooooooooooooooooooooooooooooo long")
    cui.start()
    cui.finish()
    cursor.show()
    colorama.deinit()
