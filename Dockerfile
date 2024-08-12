FROM python:3.10-slim

# add user and drop root permissions
ENV USER=cryptogull
RUN useradd -ms /bin/bash "${USER}"
USER ${USER}
WORKDIR /home/${USER}

# install source code
COPY --chown=${USER}:${USER} bot ./bot
COPY --chown=${USER}:${USER} pyproject.toml ./
COPY --chown=${USER}:${USER} poetry.lock ./

# required for 'poetry' command to execute when installed as user:
ENV PATH=${PATH}:/home/${USER}/.local/bin

# install dependencies
RUN pip install --disable-pip-version-check --user poetry && \
    poetry install --no-dev

ENV PYTHONUNBUFFERED=True
HEALTHCHECK NONE
CMD ["poetry", "run", "python", "-m", "bot"]
