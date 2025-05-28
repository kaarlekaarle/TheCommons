import json
import random
import time
import uuid

from locust import HttpUser, between, task




class VotingUser(HttpUser):
    wait_time = between(1, 3)  # Wait between 1-3 seconds between tasks
    token = None
    max_retries = 3
    retry_delay = 1  # seconds

    def on_start(self):
        """Login and get token before starting tasks."""
        retries = 0
        while retries < self.max_retries:
            try:
                # Create a test user with a unique email using UUID
                user_data = {
                    "email": f"testuser_{uuid.uuid4()}@example.com",
                    "password": "testpassword123",
                    "username": f"testuser_{uuid.uuid4()}",
                }

                response = self.client.post("/api/users/", json=user_data)
                if response.status_code == 201:
                    break
                elif response.status_code == 400:
                    # Email or username already exists, try again
                    retries += 1
                    if retries < self.max_retries:
                        time.sleep(self.retry_delay)
                        continue
                    else:
                        raise Exception("Max retries reached for user creation")
                else:
                    # Other error, raise exception
                    raise Exception(f"Failed to create user: {response.text}")
            except Exception as e:
                retries += 1
                if retries >= self.max_retries:
                    raise Exception(
                        f"Failed to create user after {self.max_retries} attempts: {str(e)}"
                    )
                time.sleep(self.retry_delay)

        # Wait for the database transaction to complete
        time.sleep(0.5)

        # Login to get token
        login_data = {"username": user_data["email"], "password": user_data["password"]}
        retries = 0
        while retries < self.max_retries:
            try:
                response = self.client.post("/api/token", data=login_data)
                if response.status_code == 200:
                    self.token = response.json()["access_token"]
                    self.headers = {"Authorization": f"Bearer {self.token}"}
                    break
                else:
                    retries += 1
                    if retries >= self.max_retries:
                        raise Exception(f"Failed to login: {response.text}")
                    time.sleep(self.retry_delay)
            except Exception as e:
                retries += 1
                if retries >= self.max_retries:
                    raise Exception(
                        f"Failed to login after {self.max_retries} attempts: {str(e)}"
                    )
                time.sleep(self.retry_delay)

    @task(1)
    def create_poll(self):
        """Create a new poll."""
        poll_data = {
            "title": f"Test Poll {random.randint(1000, 9999)}",
            "description": "This is a test poll for load testing",
        }
        response = self.client.post("/api/polls/", json=poll_data, headers=self.headers)
        if response.status_code == 201:
            poll_id = response.json()["id"]
            # Create options for the poll
            for i in range(3):
                option_data = {"text": f"Option {i+1}", "poll_id": poll_id}
                self.client.post(
                    "/api/options/", json=option_data, headers=self.headers
                )

    @task(2)
    def list_polls(self):
        """List all polls."""
        self.client.get("/api/polls/", headers=self.headers)

    @task(3)
    def get_poll(self):
        """Get a specific poll."""
        # First get list of polls
        response = self.client.get("/api/polls/", headers=self.headers)
        if response.status_code == 200:
            polls = response.json()
            if polls:
                poll_id = random.choice(polls)["id"]
                self.client.get(f"/api/polls/{poll_id}", headers=self.headers)

    @task(4)
    def cast_vote(self):
        """Cast a vote on a poll."""
        # First get list of polls
        response = self.client.get("/api/polls/", headers=self.headers)
        if response.status_code == 200:
            polls = response.json()
            if polls:
                poll_id = random.choice(polls)["id"]
                # Get options for the poll
                options_response = self.client.get(
                    f"/api/options/poll/{poll_id}", headers=self.headers
                )
                if options_response.status_code == 200:
                    options = options_response.json()
                    if options:
                        option_id = random.choice(options)["id"]
                        # Create and cast vote
                        vote_data = {"poll_id": poll_id, "option_id": option_id}
                        vote_response = self.client.post(
                            "/api/votes/", json=vote_data, headers=self.headers
                        )
                        if vote_response.status_code == 201:
                            vote_id = vote_response.json()["id"]
                            self.client.post(
                                f"/api/votes/{vote_id}/cast", headers=self.headers
                            )

    @task(5)
    def health_check(self):
        """Check application health."""
        self.client.get("/health")
        self.client.get("/health/db")
