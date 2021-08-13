import multiprocessing
import uvicorn
import uvicorn.workers
import gunicorn.app.base

from searx import settings


class CustomUvicornWorker(uvicorn.workers.UvicornWorker):
    CONFIG_KWARGS = {}


class StandaloneApplication(gunicorn.app.base.BaseApplication):
    # pylint: disable=abstract-method

    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        config = {
            key: value
            for key, value in self.options.items()
            if key in self.cfg.settings and value is not None
        }
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


def number_of_workers():
    return multiprocessing.cpu_count() + 1


def run_production(app):
    config_kwargs = {
        "loop": "uvloop",
        "http": "httptools",
        "proxy_headers": True,
    }
    base_url = settings["server"]["base_url"] or None
    if base_url:
        # ? config_kwargs['proxy_headers'] = True
        config_kwargs["root_path"] = settings["server"]["base_url"]

    CustomUvicornWorker.CONFIG_KWARGS.update(config_kwargs)

    options = {
        "proc_name": "searxng",
        "bind": "%s:%s"
        % (settings["server"]["bind_address"], settings["server"]["port"]),
        "workers": number_of_workers(),
        "worker_class": "searx.run.CustomUvicornWorker",
        "loglevel": "debug",
        "capture_output": True,
    }
    StandaloneApplication(app, options).run()


def run_debug():
    kwargs = {
        "reload": True,
        "loop": "auto",
        "http": "auto",
        "ws": "none",
        "host": settings["server"]["bind_address"],
        "port": settings["server"]["port"],
        "proxy_headers": True,
    }
    base_url = settings["server"]["base_url"]
    if base_url:
        kwargs["root_path"] = settings["server"]["base_url"]

    uvicorn.run("searx.webapp:app", **kwargs)
