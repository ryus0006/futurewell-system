FROM python:3.12-slim

WORKDIR /apps/backend/src

# Python libraries
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Source code
COPY . .

# Network interface (8080; 8000 is taken by Coolify on the host)
EXPOSE 8080

# Entry script
RUN chmod +rx docker-cmd.sh

# Run as non-root user (matches workspace convention)
RUN useradd -u 3000 -m appuser && chown -R 3000:3000 /apps
USER 3000

CMD ["./docker-cmd.sh"]
