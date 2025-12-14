# Security Audit Report

I have identified the following vulnerabilities in the code changes:

File: src/caltopo_reporter.py

L21: [MEDIUM] Server-Side Request Forgery (SSRF) - ✅ RESOLVED

When the ALLOW_NON_PROD_CALTOPO_URL environment variable is set to true, the application is vulnerable to Server-Side Request Forgery (SSRF). The CALTOPO_URL environment variable is used to construct the base
URL for API requests without sufficient validation, allowing an attacker to specify an arbitrary URL. This could be abused to make requests to internal services, scan internal networks, or interact with cloud
provider metadata endpoints.

Suggested change:
For development and testing, instead of allowing any URL, implement a more robust check. For example, allow localhost, 127.0.0.1, and perhaps a specific, non-routable test domain. If flexible endpoints are
needed, use an explicit allow-list of domains/IPs in the configuration rather than a simple boolean flag.

Resolution: Replaced ALLOW_NON_PROD_CALTOPO_URL boolean with CALTOPO_ALLOWED_URL_PATTERNS explicit allowlist (src/caltopo_reporter.py:L44-L72). URLs must match explicit patterns in test/dev mode or point to caltopo.com in production.

File: src/gateway_app.py

L434: [MEDIUM] Log Injection

Throughout the _process_\* methods, data received from the MQTT broker is logged directly without sanitization. An attacker who can publish messages to the MQTT topic could craft payloads containing special
characters (e.g., newline characters, ANSI escape codes) to inject fake log entries, corrupt the log file, or manipulate a terminal that is viewing the logs. This can be used to hide malicious activity or trick
a system administrator. This issue is present in multiple logging statements.

Suggested change:
Before logging any data that originates from an external source, sanitize it to remove or escape control characters and other potentially dangerous sequences. A simple approach is to replace newline characters
and other non-printable characters. A more robust solution would be to use a logging formatter that is specifically designed to handle untrusted data. For example, you could replace non-printable characters
before logging: sanitized_longname = longname.encode('utf-8', 'replace').decode('utf-8').
