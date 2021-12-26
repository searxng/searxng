import typing
import inspect
from json import JSONDecodeError
from urllib.parse import urlparse
from httpx import HTTPError, HTTPStatusError
from searx.exceptions import (
    SearxXPathSyntaxException,
    SearxEngineXPathException,
    SearxEngineAPIException,
    SearxEngineAccessDeniedException,
)
from searx import searx_parent_dir, settings
from searx.engines import engines


errors_per_engines = {}


class ErrorContext:

    __slots__ = (
        'filename',
        'function',
        'line_no',
        'code',
        'exception_classname',
        'log_message',
        'log_parameters',
        'secondary',
    )

    def __init__(self, filename, function, line_no, code, exception_classname, log_message, log_parameters, secondary):
        self.filename = filename
        self.function = function
        self.line_no = line_no
        self.code = code
        self.exception_classname = exception_classname
        self.log_message = log_message
        self.log_parameters = log_parameters
        self.secondary = secondary

    def __eq__(self, o) -> bool:
        if not isinstance(o, ErrorContext):
            return False
        return (
            self.filename == o.filename
            and self.function == o.function
            and self.line_no == o.line_no
            and self.code == o.code
            and self.exception_classname == o.exception_classname
            and self.log_message == o.log_message
            and self.log_parameters == o.log_parameters
            and self.secondary == o.secondary
        )

    def __hash__(self):
        return hash(
            (
                self.filename,
                self.function,
                self.line_no,
                self.code,
                self.exception_classname,
                self.log_message,
                self.log_parameters,
                self.secondary,
            )
        )

    def __repr__(self):
        return "ErrorContext({!r}, {!r}, {!r}, {!r}, {!r}, {!r}) {!r}".format(
            self.filename,
            self.line_no,
            self.code,
            self.exception_classname,
            self.log_message,
            self.log_parameters,
            self.secondary,
        )


def add_error_context(engine_name: str, error_context: ErrorContext) -> None:
    errors_for_engine = errors_per_engines.setdefault(engine_name, {})
    errors_for_engine[error_context] = errors_for_engine.get(error_context, 0) + 1
    engines[engine_name].logger.warning('%s', str(error_context))


def get_trace(traces):
    for trace in reversed(traces):
        split_filename = trace.filename.split('/')
        if '/'.join(split_filename[-3:-1]) == 'searx/engines':
            return trace
        if '/'.join(split_filename[-4:-1]) == 'searx/search/processors':
            return trace
    return traces[-1]


def get_hostname(exc: HTTPError) -> typing.Optional[None]:
    url = exc.request.url
    if url is None and exc.response is not None:
        url = exc.response.url
    return urlparse(url).netloc


def get_request_exception_messages(
    exc: HTTPError,
) -> typing.Tuple[typing.Optional[str], typing.Optional[str], typing.Optional[str]]:
    url = None
    status_code = None
    reason = None
    hostname = None
    if hasattr(exc, '_request') and exc._request is not None:
        # exc.request is property that raise an RuntimeException
        # if exc._request is not defined.
        url = exc.request.url
    if url is None and hasattr(exc, 'response') and exc.response is not None:
        url = exc.response.url
    if url is not None:
        hostname = url.host
    if isinstance(exc, HTTPStatusError):
        status_code = str(exc.response.status_code)
        reason = exc.response.reason_phrase
    return (status_code, reason, hostname)


def get_messages(exc, filename) -> typing.Tuple:
    if isinstance(exc, JSONDecodeError):
        return (exc.msg,)
    if isinstance(exc, TypeError):
        return (str(exc),)
    if isinstance(exc, ValueError) and 'lxml' in filename:
        return (str(exc),)
    if isinstance(exc, HTTPError):
        return get_request_exception_messages(exc)
    if isinstance(exc, SearxXPathSyntaxException):
        return (exc.xpath_str, exc.message)
    if isinstance(exc, SearxEngineXPathException):
        return (exc.xpath_str, exc.message)
    if isinstance(exc, SearxEngineAPIException):
        return (str(exc.args[0]),)
    if isinstance(exc, SearxEngineAccessDeniedException):
        return (exc.message,)
    return ()


def get_exception_classname(exc: Exception) -> str:
    exc_class = exc.__class__
    exc_name = exc_class.__qualname__
    exc_module = exc_class.__module__
    if exc_module is None or exc_module == str.__class__.__module__:
        return exc_name
    return exc_module + '.' + exc_name


def get_error_context(framerecords, exception_classname, log_message, log_parameters, secondary) -> ErrorContext:
    searx_frame = get_trace(framerecords)
    filename = searx_frame.filename
    if filename.startswith(searx_parent_dir):
        filename = filename[len(searx_parent_dir) + 1 :]
    function = searx_frame.function
    line_no = searx_frame.lineno
    code = searx_frame.code_context[0].strip()
    del framerecords
    return ErrorContext(filename, function, line_no, code, exception_classname, log_message, log_parameters, secondary)


def count_exception(engine_name: str, exc: Exception, secondary: bool = False) -> None:
    if not settings['general']['enable_metrics']:
        return
    framerecords = inspect.trace()
    try:
        exception_classname = get_exception_classname(exc)
        log_parameters = get_messages(exc, framerecords[-1][1])
        error_context = get_error_context(framerecords, exception_classname, None, log_parameters, secondary)
        add_error_context(engine_name, error_context)
    finally:
        del framerecords


def count_error(
    engine_name: str, log_message: str, log_parameters: typing.Optional[typing.Tuple] = None, secondary: bool = False
) -> None:
    if not settings['general']['enable_metrics']:
        return
    framerecords = list(reversed(inspect.stack()[1:]))
    try:
        error_context = get_error_context(framerecords, None, log_message, log_parameters or (), secondary)
        add_error_context(engine_name, error_context)
    finally:
        del framerecords
