import sys
import time

class widget:
    def __init__(self):
        pass

    def generate(self, msg):
        return "[" + msg + "]"

    def finish(self, max=100, success=True):
        marker = "*" if success else "x"
        return "[" + marker*(max - 2) + "]"

class percentage_widget(widget):
    def __init__(self):
        pass

    def generate(self, val, max=100):
        # -2 is for "[]" markers
        max -= 2
        val = val if val < max else max
        content = ("*"*val) + (" " * (max - val))
        return super().generate(content)

class bounce_widget(widget):
    def __init__(self):
        self.marker="<=>"

    def generate(self, val, max=100):
        # -2 is for "[]" markers
        max = max - len(self.marker) - 2
        pos = (val % max) if (int(val / max) % 2) == 0 else max - (val % max)
        return super().generate(" "*pos + self.marker + " "*(max-pos))

class progressbar:
    def __init__(self, width, max=None):
        self.width = width
        self.count = 0
        self.max = max
        if self.max == None:
            self.widget = bounce_widget()
        else:
            self.widget = percentage_widget()

    def construct(self, message, value=None):
        # |----------------------------width------------------------------|
        # |                     |----------progressbar_width--------------|
        # |--------message------|"["|--progress_marker--empty_marker--|"]"|
        if self.max != None and value >= (self.max - 1):
            value = self.max - 1
        prog = message
        rmax = self.width - len(message)
        rval = int(self.count if self.max == None else (value * rmax) / self.max)

        prog += self.widget.generate(rval, rmax)
        if self.max == None:
            self.count += 1
        return prog

    def finish(self, message, success=True):
        prog = message
        rmax = self.width - len(message)
        prog += self.widget.finish(rmax, success)
        return prog

if __name__ == "__main__":
    percentage = progressbar(50, max=100)
    bounce = progressbar(50)
    # percentage bar
    for i in range(0, 200):
        sys.stdout.write('\r' + percentage.construct("status %d" % i, value=i))
        sys.stdout.flush()
        time.sleep(0.01)
    sys.stdout.write('\r' + bounce.finish("done"))

    print("")
    #bounce bar
    for i in range(0, 200):
        sys.stdout.write('\r' + bounce.construct("status %d" % i))
        sys.stdout.flush()
        time.sleep(0.01)
    sys.stdout.write('\r' + bounce.finish("done"))

    