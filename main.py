import datetime
import os

def run_task():
    now = datetime.datetime.now()
    print(f"Success! The Python script ran at {now}")
    
    # Optional: Check for an environment variable
    secret_value = os.getenv("MY_SECRET_VARIABLE", "No secret found")
    print(f"Secret check: {secret_value}")

if __name__ == "__main__":
    run_task()