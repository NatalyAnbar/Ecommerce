# Start from a small official image that already has Python 3.13.
FROM python:3.13-slim

# Don't write .pyc files, and print logs right away.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Everything below happens inside /app in the container.
WORKDIR /app

# Install the libraries first, so Docker reuses this step
# when only the code changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Then copy the project itself.
COPY . .

# Django listens on port 8000.
EXPOSE 8000

# Listen on 0.0.0.0 so the browser outside the container can reach it.
CMD ["sh","start.sh"]