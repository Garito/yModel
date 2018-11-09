from asyncio import get_event_loop, iscoroutinefunction

from unittest import TestCase

#  https://stackoverflow.com/questions/23033939/how-to-test-python-3-4-asyncio-code

class AioTestCase(TestCase):
  def __init__(self, methodName = 'runTest', loop = None):
    self.loop = loop or get_event_loop()
    self._function_cache = {}
    super(AioTestCase, self).__init__(methodName = methodName)

  def coroutine_function_decorator(self, func):
    def wrapper(*args, **kwargs):
      return self.loop.run_until_complete(func(*args, **kwargs))
    return wrapper

  def __getattribute__(self, item):
    attr = object.__getattribute__(self, item)
    if iscoroutinefunction(attr):
      if item not in self._function_cache:
        self._function_cache[item] = self.coroutine_function_decorator(attr)

      return self._function_cache[item]
    return attr
