FROM python:3.9-alpine as build-image
RUN apk add build-base
ARG PIP_EXTRA_INDEX_URL
WORKDIR /service
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
# COPY requirements requirements/
COPY ./requirements.txt .
RUN pip install --no-cache-dir --disable-pip-version-check --requirement requirements.txt --trusted-host 5.53.125.17


FROM python:3.9-alpine as runtime-image
RUN adduser -D service
USER service
COPY --chown=service:service --from=build-image /opt/venv /opt/venv
COPY --chown=service:service . /service
WORKDIR /service
ARG AVATAR_VERSION
ARG AVATAR_TITLE
ENV AVATAR_VERSION $AVATAR_VERSION
ENV AVATAR_TITLE $AVATAR_TITLE
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENTRYPOINT ["python", "-m", "app"]
