from callisto.delivery.hashers import PBKDF2KeyHasher


class PBKDF2TestKeyHasher(PBKDF2KeyHasher):
    """
    Since KeyHasher properties are set on import and not instantiation, it is necessary to change this in order to
    properly test runtime hardening.
    """

    def __init__(self, iterations=1000):
        self.iterations = iterations
