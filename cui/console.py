import os
import sys
import difflib

def cursor_up(x):
    sys.stdout.write("\033[%dA" % x)


def cursor_down(x=1):
    sys.stdout.write("\033[%dB" % x)


def cursor_right(x):
    sys.stdout.write("\033[%dC" % x)


def cursor_left(x):
    sys.stdout.write("\033[%dD" % x)


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
    sys.stdout.write("\033[0K")


def clear_entire_line():
    # Erase the entire line
    sys.stdout.write("\033[2K")


class _frame:
    def __init__(self):
        self.visible = False
        self._status = ""
        self._content = ""

    def update(self):
        # No need to clear the entire screen
        self._content = self._status
        sys.stdout.write("\r" + self._status)

        # clear stray characters after the content update
        clear_line()

    def __fancy_update(self):
        # Not knowing '\r' will do the trick for flickering, implemented a way
        # of finding diff between already existing content and new content and update only the
        # diff blocks. But this takes the tole on performance (obviously). Don't know will use it
        # But keeping it for book-keeping
        _update = []
        diff = difflib.SequenceMatcher(None, self._content, self._status)
        ratio = diff.ratio()
        if (ratio < 0.4):
            _update.append((0, None))
        else:
            for op in diff.get_opcodes():
                status, _, _, newa, newb = op
                if status == "equal":
                    continue
                elif status == "insert" or status == "delete":
                    _update.append((newa,None))
                    break
                elif status == "replace":
                    _update.append((newa, newb))

        self._content = self._status
        if self.visible:
            for u in _update:
                cursor_leftmost()
                cursor_right(u[0] + 1)
                sys.stdout.write(self._status[u[0]:u[1]])

    def _get_status(self):
        return self._status

    def _set_status(self, status):
        self._status = status

    def _del_status(self):
        del self._status

    status = property(_get_status, _set_status, _del_status)

class _viewport:
    def __init__(self, port_update_rate=3):
        self.frames = []

    def __len__(self):
        return len(self.frames)

    def __contains__(self, f):
        if f in self.frames:
            return True
        else:
            return False

    def __iter__(self):
        for frame in self.frames:
            yield frame

    def append(self, frame):
        if isinstance(frame, _frame):
            self.frames.append(frame)

    def updateframe(self, frame, s):
        frame.update(s)

class con:
    def __init__(self):
        print("")
        self.viewport = _viewport()
        self.first = True

    def registerframe(self):
        frame = _frame()
        self.viewport.append(frame)
        return frame

    def render(self):
        _, rows = os.get_terminal_size()
        rows -= 1
        if self.first:
            frames = len(self.viewport)
            vframes = frames if frames < rows else rows
            sys.stdout.write('\n' * vframes)
            sys.stdout.flush()
            cursor_up(vframes)
        self.first = False
        # Assuming we are in the origin (relative)
        i = 0
        for frame in self.viewport:
            if i < rows:
                frame.visible = True
                frame.update()
                cursor_down()
            else:
                break
            i += 1
        cursor_up(i)

    def finish(self, showall=False):
        _, rows = os.get_terminal_size()
        if showall:
            for i, frame in enumerate(self.viewport):
                frame.visible = True
                frame.update()
                if i < (rows-1):
                    cursor_down()
                else:
                    print("")
        else:
            frames = len(self.viewport)
            cursor_down(frames-1 if frames < rows else rows-1)

if __name__ == "__main__":
    import time
    con = con()

    frames=[]
    for i in range(0, 15):
        frames.append(con.registerframe())

    for j in range(0, 100):
        for i in reversed(range(0, 15)):
            frames[14-i].status = "Sathish %d" % i
        con.render()
        time.sleep(0.01)
    con.finish(showall=True)