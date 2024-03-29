FROM python:3.6-stretch

ENV VIRTUAL_ENV=/usr/local/env

RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN apt-get update \
    && apt-get install -y vim git netcat
RUN python -m pip install --upgrade pip

ARG GIT_USER_NAME
RUN git config --global user.name "${GIT_USER_NAME}"

ARG GIT_USER_EMAIL
RUN git config --global user.email ${GIT_USER_EMAIL}

WORKDIR /usr/local/src/app

COPY ./requirements.txt .
COPY ./*.py ./
COPY ./backend ./backend
COPY ./entrypoint.sh .
COPY ./.env .

RUN pip install -r requirements.txt

EXPOSE 8000

ENTRYPOINT ["/usr/local/src/app/entrypoint.sh"]
