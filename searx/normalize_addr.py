# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring


from ipaddress import ip_address


class NormalizeAddr:
    """Middleware to normalize the remote address from WSGI environment.

    Converts IPv4 mapped IPv6 addresses to their IPv4 counterparts.

    Some WSGI servers map every IPv4 address to
    a compatible IPv6 address when listening on "::".

    remote_addr >> "::ffff:127.0.0.1"
    remote_addr << "127.0.0.1"

    :param wsgi_app: the WSGI application
    """

    # pylint: disable=too-few-public-methods

    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        remote_addr_str = environ["REMOTE_ADDR"]

        # "None" if connecting via socket
        if remote_addr_str:
            remote_addr = ip_address(remote_addr_str)
            if remote_addr.version == 6 and remote_addr.ipv4_mapped:
                environ["REMOTE_ADDR"] = remote_addr.ipv4_mapped

        return self.wsgi_app(environ, start_response)
