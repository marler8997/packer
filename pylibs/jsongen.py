from enum import Enum

_PROP_FLAG = 0x1
_NOT_FIRST_FLAG = 0x2

class JsonGenerator:
    def __init__(self, file):
        self.file = file
        self.state_stack = []

    def start(self):
        assert len(self.state_stack) == 0
        self.state_stack.append(0)
    def finish(self):
        assert len(self.state_stack) == 1
        state = self.state_stack.pop()

    def _next(self, prop_name = None):
        last_index = len(self.state_stack) - 1
        state = self.state_stack[last_index]
        if prop_name:
            assert state & _PROP_FLAG == _PROP_FLAG
        else:
            assert state & _PROP_FLAG == 0
        if state & _NOT_FIRST_FLAG:
            self.file.write(",")
        else:
            self.state_stack[last_index] |= _NOT_FIRST_FLAG
        if prop_name:
            self.file.write('"')
            self.file.write(prop_name)
            self.file.write('":')

    def _obj(self):
        self.file.write("{")
        self.state_stack.append(_PROP_FLAG)
    def obj(self):
        self._next()
        self._obj()
    def prop_obj(self, name):
        self._next(name)
        self._obj()

    def _array(self):
        self.file.write("[")
        self.state_stack.append(0)
    def array(self):
        self._next()
        self._array()
    def prop_array(self, name):
        self._next(name)
        self._array()

    def _str(self, value):
        self.file.write('"')
        self.file.write(value)
        self.file.write('"')
    def str(self, value):
        self._next()
        self._str(value)
    def prop_str(self, name, value):
        self._next(name)
        self._str(value)

    def bool(self, value):
        self._next()
        self.file.write("true" if value else "false")
    def prop_bool(self, name, value):
        self._next(name)
        self.file.write("true" if value else "false")

    def val(self, value):
        self._next()
        self.file.write(str(value))
    def prop_val(self, name, value):
        self._next(name)
        self.file.write(str(value))

    def end_obj(self):
        state = self.state_stack.pop()
        assert state & _PROP_FLAG == _PROP_FLAG
        self.file.write("}")
    def end_array(self):
        state = self.state_stack.pop()
        assert state & _PROP_FLAG == 0
        self.file.write("]")
