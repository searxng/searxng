import threading
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures._base import Future


class ThreadNoPoolExecutor(ThreadPoolExecutor):

    def __init__(self, max_workers=None, thread_name_prefix='',
                 initializer=None, initargs=()):
        # pylint: disable=super-init-not-called
        if max_workers:
            raise NotImplementedError('max_workers not supported')
        if initializer:
            raise NotImplementedError('initializer not supported')
        if initargs:
            raise NotImplementedError('initargs not supported')
        self.thread_name_prefix = thread_name_prefix

    def submit(self, fn, *args, **kwargs):  # pylint: disable=arguments-differ
        f = Future()

        def worker():
            if not f.set_running_or_notify_cancel():
                return
            try:
                result = fn(*args, **kwargs)
            except BaseException as exc:
                f.set_exception(exc)
            else:
                f.set_result(result)

        t = threading.Thread(
            target=worker,
            name=self.thread_name_prefix + '_engine',
            daemon=True
        )
        t.start()
        return f
    # submit.__text_signature__ = ThreadPoolExecutor.submit.__text_signature__
    # submit.__doc__ = ThreadPoolExecutor.submit.__doc__

    def shutdown(self, wait=True):
        pass
