FROM python:3.12-slim-bullseye
ENV DEBIAN_FRONTEND=noninteractive
RUN apt update && apt install -y gcc && rm -rf /var/lib/apt/lists/*

ENV VIRTUAL_ENV=/run/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /run/app

# Dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt && rm requirements.txt

# Run bot
COPY main.py .
COPY modules ./modules
CMD ["python", "main.py"]
