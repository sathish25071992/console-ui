import colorama
import sys
import os
import threading
import time
import textwrap
import cursor

import console
from progressbar import progressbar

class cui():
    def __init__(self, width, tasks=[], header_required=True):
        self.tasklist = []
        self.tmtask = None
        self.noelements = 0
        self.tmhdr_required = header_required
        self.taskoffset = 1 if self.tmhdr_required else 0
        self.elements = []
        self.width = width
        self.console = console.con(port_update_rate=100)

        if self.tmhdr_required:
            self.tmtask = {"func": None, "args": None,
                       "message": "", "element": None, "thread": None, 
                       "frame": self.console.registerframe(isheader=True)}

        for task in tasks:
            taskentry = {}
            taskentry["func"], taskentry["args"] = task
            taskentry["message"] = "Starting"
            taskentry["element"] = None
            taskentry["thread"] = None
            taskentry["id"] = self.noelements
            taskentry["title"] = "| task %d:" % self.noelements
            taskentry["failed"] = False
            taskentry["frame"] = self.console.registerframe()
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
                msg = "# of tasks monitored %d/%d" % (
                    completed_task, len(tasklist) + completed_task)
                self.tmtask["frame"].status = self.tmtask["element"].construct(msg, completed_task)
            if len(tasklist) == 0:
                if self.tmhdr_required:
                    self.tmtask["frame"].status = self.tmtask["element"].finish(msg)
                    self.console.render()
                    break
            for task in tasklist:
                msg = task["title"] + " " + task["message"]
                shortmsg = textwrap.shorten(msg, width=self.width-13, placeholder="...")
                task["frame"].status = task["element"].construct(shortmsg)
                if not task["thread"].is_alive():
                    task["frame"].status =  task["element"].finish(task["title"] + " " + "done", success=not task["failed"])
                    tasklist.remove(task)
            self.console.render()

    def register(self, func, args, title=""):
        taskentry = {}
        taskentry["func"] = func
        taskentry["args"] = args
        taskentry["message"] = "Starting"
        taskentry["element"] = None
        taskentry["thread"] = None
        taskentry["failed"] = False
        taskentry["id"] = self.noelements
        taskentry["frame"] = self.console.registerframe()
        if title == "":
            taskentry["title"] = "| task %d:" % self.noelements
        else:
            taskentry["title"] = "| %s:" % title
        self.tasklist.append(taskentry)
        self.noelements += 1

    def start(self):
        msg = "# of tasks monitored: %d" % len(self.tasklist)
        element = progressbar(self.width, max=len(self.tasklist))
        self.tmtask["message"] = msg
        self.tmtask["element"] = element

        thread = threading.Thread(
            target=self.__task_manager, args=(self.tasklist,))
        self.tmtask["thread"] = thread

        for task in self.tasklist:
            element = progressbar(self.width)
            task["element"] = element
            task["message"] = "starting"
            thread = threading.Thread(target=self.__monitor, args=(task,))
            task["thread"] = thread
            task["thread"].isDaemon = True
            task["thread"].start()

        self.console.render()
        self.tmtask["thread"].start()
        self.tmtask["thread"].join()


    def finish(self):
        noelements = self.noelements - 1
        if self.tmhdr_required:
            noelements += 1
        
        self.console.finish(showall=True)
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
    cui.register(test, (2,))
    cui.register(test, (2,))
    cui.register(test, (1,), title="custom title")
    cui.register(
        test, (4,), title="custom title tooooooooooooooooooooooooooooooooooooooooooooooooo long")
    cui.start()
    cui.finish()
    cursor.show()
    colorama.deinit()
