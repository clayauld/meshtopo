Security Audit Report

I have identified the following vulnerabilities in the code changes:

1. Command Injection in Makefile

- Vulnerability: Command Injection
- Severity: Critical
- Location: Makefile:136
- Line Content:
  - docker build -t ghcr.io/$(REPO):latest -t ghcr.io/$(REPO):$(shell git rev-parse --short HEAD) -f deploy/Dockerfile .
  - docker pull ghcr.io/$(REPO):latest
  - docker push ghcr.io/$(GITHUB_REPOSITORY):latest; \
- Description: The docker-build, docker-pull, and docker-push targets in the Makefile use the $(REPO) and $(GITHUB_REPOSITORY) variables directly in shell commands without any sanitization. An attacker who can
    control the GITHUB_REPOSITORY environment variable can inject arbitrary shell commands. For example, setting GITHUB_REPOSITORY to a; rm -rf / would result in the execution of rm -rf /.
- Recommendation: Sanitize the GITHUB*REPOSITORY variable before using it in shell commands. Ensure it only contains characters appropriate for a repository name (e.g., alphanumeric,*, -, /).

2. Leaking Secrets in Process List

- Vulnerability: Exposure of Sensitive Information to an Unauthorized Actor
- Severity: Medium
- Location: Makefile:202
- Line Content: docker login ghcr.io -u $(GITHUB_ACTOR) -p $(GITHUB_TOKEN)
- Description: The docker-login target passes the GITHUB_TOKEN secret on the command line using the -p flag. This is insecure because the command and its arguments are visible in the process list (ps aux).
    Anyone with access to the machine running make can see the GITHUB_TOKEN.
- Recommendation: Pass the token via stdin to the docker login command. For example: echo $(GITHUB_TOKEN) | docker login ghcr.io -u $(GITHUB_ACTOR) --password-stdin.

3. Traefik Routing Rule Injection

- Vulnerability: Traefik Routing Rule Injection
- Severity: High
- Location: deploy/docker-compose.yml:51
- Line Content:
    - -   "traefik.http.routers.traefik.rule=Host(\traefik.${SSL_DOMAIN}\)"
    - -   "traefik.http.routers.mosquitto-ws.rule=Host(\mqtt.${SSL_DOMAIN}\)"
- Description: The SSL_DOMAIN environment variable is used directly in Traefik's routing rules without sanitization. An attacker who can control this environment variable can inject malicious expressions into
    the Host() function, potentially redirecting traffic, bypassing access controls, or causing a denial of service. For example, an attacker could set SSL_DOMAIN to ` ) || PathPrefix("/") `` to route all
    traffic to a specific service.
- Recommendation: Sanitize the SSL_DOMAIN variable to ensure it only contains a valid domain name. It should not contain any characters that have a special meaning in Traefik's rule syntax, such as (, ), &, |,
    etc.

4. Unnecessary Build Tools in Production Image

- Vulnerability: Unnecessary build tools in production image.
- Severity: Low
- Location: deploy/Dockerfile:8-10
- Line Content: RUN apt-get update && apt-get install -y --no-install-recommends gcc=4:14.2.0-1
- Description: The gcc compiler is installed in the base image and is present in the final production image. Build tools like compilers are not needed at runtime and increase the attack surface of the
    container.
- Recommendation: Use a multi-stage build. Create a builder stage where you install gcc and build any dependencies that need it. Then, in the production stage, copy the built artifacts from the builder stage
    without installing gcc.

5. Insecure Service Configuration in Integration Tests

- Vulnerability: Use of an insecure service configuration.
- Severity: Low
- Location: deploy/docker-compose.integration.yml:16
- Line Content: command: mosquitto -c /mosquitto-no-auth.conf
- Description: The integration tests use a Mosquitto configuration that likely allows anonymous access. While this is acceptable for a test environment, it's important to document that this configuration is
    not suitable for production and ensure that the production configuration is secure.
- Recommendation: Ensure that the production docker-compose.yml uses a secure Mosquitto configuration with authentication enabled. Add a comment to docker-compose.integration.yml to clarify that it's for
    testing purposes only and should not be used in production.

6. Unsanitized File Path from Command-line Argument

- Vulnerability: Path Traversal
- Severity: Low
- Location: src/gateway.py:29
- Line Content: config_path = sys.argv[1] if len(sys.argv) > 1 else "config/config.yaml"
- Description: The application takes a file path from a command-line argument and uses it to read a configuration file. An attacker with the ability to control the command-line arguments could potentially
    specify an arbitrary file on the system to be parsed as a config file, leading to information disclosure or unexpected behavior. For example, an attacker could provide /etc/passwd as the config file path.
- Recommendation: While the immediate risk is low due to the execution context, it's a good practice to sanitize the input. For example, you could restrict the file path to a specific directory, or at least
    resolve the path and ensure it's within the project's directory.

7. Insecure Deserialization in SqliteDict

- Vulnerability: Insecure Deserialization
- Severity: Critical
- Location: src/gateway_app.py:87-90
- Line Content:
  - self.node_id_mapping = SqliteDict("meshtopo_state.sqlite", tablename="node_id_mapping", autocommit=True)
  - self.callsign_mapping = SqliteDict("meshtopo_state.sqlite", tablename="callsign_mapping", autocommit=True)
- Description: The application uses SqliteDict with its default pickle serializer to store data received from Meshtastic devices. pickle is known to be insecure and can lead to remote code execution if an
    attacker can control the data being deserialized. An attacker who can control the longname or shortname of a Meshtastic device could craft a malicious pickle object and store it in the database. When the
    application later retrieves this value, it will deserialize the malicious object, leading to RCE.
- Recommendation: When initializing SqliteDict, explicitly set encode=json.dumps and decode=json.loads. json is a safe serialization format. For example: SqliteDict("meshtopo_state.sqlite",
    tablename="node_id_mapping", autocommit=True, encode=json.dumps, decode=json.loads).

8. Inconsistent Log Sanitization

- Vulnerability: Log Injection
- Severity: Medium
- Location: src/gateway_app.py:244-246
- Description: The application has a \_sanitize_for_log method, but it's not used consistently. Several logging statements in \_process_message and \_process_position_message log raw data from MQTT messages, such
    as numeric_node_id, message_type, and hardware_id. This could allow an attacker who can control these values to inject malicious characters into the logs, potentially corrupting the log file or tricking an
    administrator.
- Recommendation: Apply the \_sanitize_for_log method to all variables that come from the MQTT message before logging them.

## Resolution Status

All identified vulnerabilities have been addressed:

1. **Command Injection in Makefile**: Fixed by sanitizing `$(REPO)` variable.
2. **Leaking Secrets in Process List**: Fixed by using `--password-stdin` for `docker login`.
3. **Traefik Routing Rule Injection**: Fixed by sanitizing `SSL_DOMAIN` in Makefile.
4. **Unnecessary Build Tools**: Fixed by using multi-stage Dockerfile.
5. **Insecure Service Configuration**: Added warning comments to `docker-compose.integration.yml`.
6. **Unsanitized File Path**: Added strict path validation in `src/gateway.py`.
7. **Insecure Deserialization**: Switched `SqliteDict` to use JSON serialization.
8. **Inconsistent Log Sanitization**: Applied `_sanitize_for_log` consistently.
