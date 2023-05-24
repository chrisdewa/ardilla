
class SingletonMeta(type):
    """
    Singleton Metaclass helper
    """
    _instances = {}
    def __call__(cls, *ags, **kws):
        return cls._instances.setdefault(
            cls, super().__call__(*ags, **kws)
        )