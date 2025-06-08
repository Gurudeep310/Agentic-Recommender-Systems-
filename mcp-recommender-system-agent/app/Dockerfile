FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy app code
COPY . /app

# Permissions
RUN chmod -R 700 /app

COPY requirements.txt /requirements.txt
RUN pip3 install --upgrade pip && \
    pip3 install -r /requirements.txt


# Expose the port your app/server runs on
EXPOSE 8503

# Start the MCP server
CMD ["python", "recommendation-system.py"]