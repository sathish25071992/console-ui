import os
import sys
import difflib

def cursor_up(x=1):
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


def clear_screen():
    sys.stdout.write("\033[J")


class _frame:
    def __init__(self, header=False):
        self.visible = False
        self._status = ""
        self._content = ""
        self.header = header

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
    def __init__(self):
        self.frames = []

    def __len__(self):
        return len(self.frames)

    def __getitem__(self, slice):
        return self.frames[slice.start:slice.stop:slice.step]

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
    def __init__(self, port_update_rate=300, frame_update_rate=0.01):
        print("")
        self.viewport = _viewport()
        self.first = True
        self.pur = port_update_rate
        self.fur = frame_update_rate
        self.frame_upcnt = 0
        self.consheight = 0
        self.headerframe = None

    def registerframe(self, isheader=False):
        frame = _frame(header=isheader)
        if isheader and self.headerframe != None:
            raise Exception("Already a header frame is registered")
        elif isheader:
            self.headerframe = frame
        else:
            self.viewport.append(frame)
        return frame

    def render(self):
        # if self.frame_upcnt % self.pur == 0:
        _, newheight = os.get_terminal_size()
        if self.headerframe != None:
            cursor_up()
            self.headerframe.visible = True
            self.headerframe.update()
            cursor_down()
            newheight -= 1
        newheight -= 1
        if newheight != self.consheight:
            self.frame_upcnt = 0
        noports = int(len(self.viewport) / newheight) + 1
        viewportindex = int(self.frame_upcnt / self.pur)

        si = (viewportindex % noports) * newheight
        ei = si + newheight
        if self.frame_upcnt % self.pur == 0:
            clear_screen()
            vframes = len(self.viewport) if len(self.viewport) < newheight else newheight
            sys.stdout.write('\n' * vframes)
            sys.stdout.flush()
            cursor_up(vframes)
        self.consheight = newheight
        # Assuming we are in the origin (relative) excluding the headerframe
        for frame in self.viewport[si:ei]:
            frame.visible = True
            frame.update()
            cursor_down()

        cursor_up(len(self.viewport[si:ei]))
        self.frame_upcnt += 1

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
    con = con(port_update_rate=10)

    frames=[]
    frame = con.registerframe(isheader=True)
    frame.status = "Header"
    frames.append(frame)

    for i in range(1, 15):
        frames.append(con.registerframe())

    for j in range(0, 100):
        for i in range(1, 15):
            frames[15-i].status = "Sathish %d" % i
        con.render()
        time.sleep(0.1)
    con.finish(showall=True)