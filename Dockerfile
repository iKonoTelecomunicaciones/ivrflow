# Building stage (host OS)
FROM python:3.8 as base

# set the working directory in the container
WORKDIR /app

# Upgrade pip
RUN python -m pip install --upgrade --no-cache-dir pip

# copy the dependencies file to the working directory
COPY requirements.txt .

# https://docs.python.org/3/using/cmdline.html#envvar-PYTHONUSERBASE
# PYTHONUSERBASE is used to compute the path of the user site-packages
RUN PYTHONUSERBASE=/install pip install --user -r requirements.txt


FROM base AS dev

# PYTHONUSERBASE is used to compute the path of the user site-packages
ENV PYTHONUSERBASE=/install

# copy the dependencies file to the working directory
COPY requirements-dev.txt .

# install dependencies
RUN pip install -r requirements-dev.txt

# copy the content of the local src directory to the working directory
COPY . ./

ENTRYPOINT watchmedo auto-restart --recursive --pattern="*.py" --directory="." -- python -m ivrflow


FROM python:3.8-slim AS runtime

# set the working directory in the container
WORKDIR /app

# copy the content of the local src directory to the working directory
COPY . ./

# copy the dependencies downloaded
COPY --from=base /install /usr/local

# command to run on container start
CMD [ "python", "-m", "ivrflow" ]
