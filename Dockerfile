FROM python:3.12-slim

WORKDIR /apps/backend/src

# Python libraries
RUN pip install --upgrade pip
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Source code
COPY . .

# Network interface (default FastAPI/uvicorn port)
EXPOSE 8000

# Entry script
RUN chmod +rx docker-cmd.sh

# Run as non-root user (matches workspace convention)
RUN useradd -u 3000 -m appuser && chown -R 3000:3000 /apps
USER 3000

CMD ["./docker-cmd.sh"]
