FROM ghcr.io/openhands/agent-server:1.37.0-python@sha256:c188dac7624d486331b455042d54abe020af43b843c2c02694deccecfbed487a

USER root
WORKDIR /opt/reverse-agent
COPY reverse_agent /opt/reverse-agent/reverse_agent
RUN python -m pip install --no-cache-dir temporalio==1.30.0

ENV PYTHONPATH=/opt/reverse-agent
ENV OPENHANDS_SUPPRESS_BANNER=1
USER 10001:10001
ENTRYPOINT ["/usr/local/bin/python", "-m"]
