# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Raise exception for an HTTP response is an error.

"""

from searx.exceptions import (
    SearxEngineCaptchaException,
    SearxEngineTooManyRequestsException,
    SearxEngineAccessDeniedException,
)
from searx import get_setting


def is_cloudflare_challenge(resp):
    if resp.status_code in [429, 503]:
        if ('__cf_chl_jschl_tk__=' in resp.text) or (
            '/cdn-cgi/challenge-platform/' in resp.text
            and 'orchestrate/jsch/v1' in resp.text
            and 'window._cf_chl_enter(' in resp.text
        ):
            return True
    if resp.status_code == 403 and '__cf_chl_captcha_tk__=' in resp.text:
        return True
    return False


def is_cloudflare_firewall(resp):
    return resp.status_code == 403 and '<span class="cf-error-code">1020</span>' in resp.text


def raise_for_cloudflare_captcha(resp):
    if resp.headers.get('Server', '').startswith('cloudflare'):
        if is_cloudflare_challenge(resp):
            # https://support.cloudflare.com/hc/en-us/articles/200170136-Understanding-Cloudflare-Challenge-Passage-Captcha-
            # suspend for 2 weeks
            raise SearxEngineCaptchaException(
                message='Cloudflare CAPTCHA', suspended_time=get_setting('search.suspended_times.cf_SearxEngineCaptcha')
            )

        if is_cloudflare_firewall(resp):
            raise SearxEngineAccessDeniedException(
                message='Cloudflare Firewall',
                suspended_time=get_setting('search.suspended_times.cf_SearxEngineAccessDenied'),
            )


def raise_for_recaptcha(resp):
    if resp.status_code == 503 and '"https://www.google.com/recaptcha/' in resp.text:
        raise SearxEngineCaptchaException(
            message='ReCAPTCHA', suspended_time=get_setting('search.suspended_times.recaptcha_SearxEngineCaptcha')
        )


def raise_for_captcha(resp):
    raise_for_cloudflare_captcha(resp)
    raise_for_recaptcha(resp)


def raise_for_httperror(resp):
    """Raise exception for an HTTP response is an error.

    Args:
        resp (requests.Response): Response to check

    Raises:
        requests.HTTPError: raise by resp.raise_for_status()
        searx.exceptions.SearxEngineAccessDeniedException: raise when the HTTP status code is 402 or 403.
        searx.exceptions.SearxEngineTooManyRequestsException: raise when the HTTP status code is 429.
        searx.exceptions.SearxEngineCaptchaException: raise when if CATPCHA challenge is detected.
    """
    if resp.status_code and resp.status_code >= 400:
        raise_for_captcha(resp)
        if resp.status_code in (402, 403):
            raise SearxEngineAccessDeniedException(message='HTTP error ' + str(resp.status_code))
        if resp.status_code == 429:
            raise SearxEngineTooManyRequestsException()
        resp.raise_for_status()
