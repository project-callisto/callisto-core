'''
sourced from: https://pypi.python.org/pypi/environ/1.0
'''

import sys

class Environ(object):
    """
    Manages stack based globals.

    A simple example:

    >>> from environ import ctx
    >>> def f():
    ...     return ctx['x']
    >>>
    >>> ctx['x'] = 7
    >>> print f()
    7

    In this example note that f() was not explicitly passed the value for 'x'
    in order to return it.  Instead the stack was probed for the correct value
    for 'x'.  f() could also have decided to change the value as well...

    >>> from environ import ctx
    >>> def f():
    ...    print ctx['x']
    ...    ctx['x'] = 5
    ...    g()
    ...
    >>> def g():
    ...    print ctx['x']
    ...
    >>> ctx['x'] = 7
    >>> f()
    7
    5
    >>> print ctx['x']
    7

    In this case, note how ctx['x'] was changed only for the benefit of g.

    Environ values can also be dynamic, for example:

    >>> from environ import ctx
    >>> ctx['x'] = "HELLO"
    >>>
    >>> # Establish y based on x.
    >>> @ctx.function
    ... def y(ctx):
    ...     return ctx['x'] + "!"
    ...
    >>> ctx['y']
    'HELLO!'

    Additionally functions can choose whether to examine further up the
    stack or back at the top environ.

    >>> from environ import ctx
    >>> ctx['x'] = 'HELLO'
    >>> ctx['y'] = 'WORLD'
    >>>
    >>> def f():
    ...     # Get x from a upper level on the stack.
    ...     @ctx.function
    ...     def x(ctx):
    ...         # Notice recursion here...
    ...         return ctx['x'] + '!'
    ...     print ctx['x']
    ...     print ctx['y']
    >>> f()
    HELLO!
    WORLD
    >>> ctx['x']
    'HELLO'
    >>>
    >>> # Make y dependent on CURRENT x.
    >>> @ctx.function
    ... def y(ctx):
    ...     return ctx['x']
    ...
    >>> f()
    HELLO!
    HELLO
    >>>
    >>> # Make y dependent on TOP x.
    >>> @ctx.function
    ... def y(ctx):
    ...     return ctx.top['x']
    ...
    >>> f()
    HELLO!
    HELLO!

    Environ objects can also be used with other dictionary like objects to
    combine environmental elements into a canonical global-like arena:

    >>> from environ import ctx
    >>> import os
    >>> ignore = ctx.addSource(os.environ)
    >>> ctx['PATH'] is not None
    True
    """

    def __init__(self, frame, top=None, name=None):
        if isinstance(frame, int):
            frame = sys._getframe(frame + 1)
        elif isinstance(frame, str):
            fname = '!' + frame
            frame = sys._getframe(1)
            while frame is not None:
                if frame.f_locals.get(fname):
                    break
                else:
                    frame = frame.f_back
            else:
                raise ValueError("No frame marked with {}.".format(fname))
        self.__dict__['__frame__'] = frame
        self.__dict__['top'] = top
        self.__dict__['__name__'] = name

    def mark(self, fname):
        """
        Marks a environ for use by other environ within the stack framework.

        >>> from environ import ctx
        >>> ctx.mark('TEST')
        >>> globals()['!TEST']
        True
        """
        sys._getframe(1).f_locals['!' + fname] = True

    def bind(self, frame):
        """
        Binds (or seeks) another environ relative to this stack frame.

        >>> from environ import ctx
        >>> import sys
        >>> ctx.mark('TEST')
        >>> f_locals = sys._getframe(0).f_locals
        >>> ctx.bind(0).__frame__.f_locals is f_locals
        True
        >>> ctx.bind('TEST').__frame__.f_locals is f_locals
        True
        """
        if isinstance(frame, int):
            frame += 1
        return Environ(frame, self)

    def addSource(self, src, frameno=0):
        """
        Adds a dictionary-like object to the list of external sources used to
        determine the values for this context.

        >>> from environ import ctx
        >>> ignore = ctx.addSource(dict(x=5))
        >>> ctx['x']
        5

        A typical use is with the os.environ dictionary:

        >>> from environ import ctx
        >>> import os
        >>> ignore = ctx.addSource(os.environ)
        """
        vars = sys._getframe(frameno + 1).f_locals
        vars['##'] = vars.get('##', ()) + (src,)
        return src

    def get(self, name, default=None):
        searcher = iter(self.search(name))
        for frame, obj in searcher:
            if isinstance(obj, self.DynamicVariable):
                return obj.fn(Environ(frame, self.top or self, name))
            else:
                return obj
        else:
            return default

    def __getitem__(self, name):
        obj = self.get(name, KeyError)
        if obj is KeyError or obj is ValueError:
            raise KeyError(name)
        else:
            return obj

    def search(self, name):
        frame = self.__frame__ or sys._getframe(1)
        if name == self.__name__:
            # Skip top frame if the same name as we were working with.
            frame = frame.f_back
        key = '#' + name
        while frame is not None:
            obj = frame.f_locals.get(key, KeyError)
            if obj is KeyError:
                for ext in frame.f_locals.get('##', ()):
                    obj = ext.get(name, KeyError)
                    if obj is not KeyError:
                        yield frame, obj
                frame = frame.f_back
            else:
                yield frame, obj

    def put(self, name, value, frame=0):
        (self.__frame__ or sys._getframe(frame + 1)) \
            .f_locals['#' + name] = value

    def __setitem__(self, name, value):
        (self.__frame__ or sys._getframe(1)).f_locals['#' + name] = value

    def __delitem__(self, name):
        self.put(name, ValueError, 1)

    def inherit(self, name):
        """
        Similar to del ctx[name], except that the name except that the value
        at this context is simply discarded (though returned) instead of being
        left with a marker to consider it deleted.

        >>> from environ import ctx
        >>> def f():
        ...     ctx['x'] = 'overridden'
        ...     print ctx['x']
        ...     del ctx['x']
        ...     try:
        ...         print ctx['x']
        ...     except KeyError:
        ...         print "KEY ERROR"
        ...     ctx.inherit('x')
        ...     print ctx['x']
        ...
        >>> ctx['x'] = 'HELLO'
        >>> f()
        overridden
        KEY ERROR
        HELLO
        """
        return (self.__frame__ or sys._getframe(1)) \
            .f_locals.pop('#' + name, None)

    def function(self, fn, name=None):
        if name is None:
            name = fn.__name__
        self.put(name, self.DynamicVariable(fn), 1)
        return fn

    class DynamicVariable(object):
        __slots__ = ['fn']

        def __init__(self, fn):
            self.fn = fn

ctx = Environ(None)

