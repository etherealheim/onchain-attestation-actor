# Use official Apify Python image
FROM apify/actor-python:3.11

# Copy requirements and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src ./src
COPY .actor ./.actor

# Set the entrypoint
CMD ["python", "-m", "src.main"]
