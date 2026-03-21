"""Application keys used for aiohttp web app storage."""

from aiohttp import web

# Shared strongly-typed key object for gateway_app access to fix NotAppKeyWarning
GATEWAY_APP_KEY: web.AppKey = web.AppKey("gateway_app")
