class DummyLazyObject(object):
    pass


_dummy_lazy_object = DummyLazyObject()


class LazyObject(object):
    def __init__(self):
        self.obj = _dummy_lazy_object

    def __call__(self, func):
        def deco(*args, **kwargs):
            self.func = func
            self.args = args
            self.kwargs = kwargs
            return self

        return deco

    def _setup(self):
        self.obj = self.func(*self.args, **self.kwargs)


class LazyDict(LazyObject):
    def __getattr__(self, name):
        if self.obj is _dummy_lazy_object:
            self._setup()

        return getattr(self.obj, name)

    def __getitem__(self, key):
        if self.obj is _dummy_lazy_object:
            self._setup()

        return self.obj[key]


