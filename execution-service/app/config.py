import os
from dotenv import load_dotenv

load_dotenv()

JUDGE0_BASE_URL = os.getenv("JUDGE0_BASE_URL")
JUDGE0_API_KEY = os.getenv("JUDGE0_API_KEY")
JUDGE0_TIMEOUT = int(os.getenv("JUDGE0_TIMEOUT"))



RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT"))
RABBITMQ_USER = os.getenv("RABBITMQ_USER")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS")
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE")

HOST = os.getenv("HOST")
PORT = int(os.getenv("SERVICE_PORT"))
DEBUG = os.getenv("DEBUG")
