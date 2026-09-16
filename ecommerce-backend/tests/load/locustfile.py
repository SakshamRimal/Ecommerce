from locust import HttpUser, task, between, events


class ShopperUser(HttpUser):
    wait_time = between(1, 3)  # simulate real user think-time between actions

    def on_start(self):
        """Runs once per simulated user — log in and grab a token."""
        response = self.client.post(
            "/api/v1/auth/login",
            data={"username": "test@example.com", "password": "supersecret123"},
            name="/api/v1/auth/login",
        )
        if response.status_code == 200:
            self.token = response.json().get("access_token", "")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = ""
            self.headers = {}
            print(f"Login failed ({response.status_code}): {response.text}")

    @task(5)
    def browse_products(self):
        """Weight 5 — most common action: browsing the catalog (should hit cache heavily)."""
        self.client.get("/api/v1/products?limit=20&offset=0")

    @task(2)
    def view_single_product(self):
        self.client.get("/api/v1/products")  # in practice, parse a real ID from browse

    @task(1)
    def search_products(self):
        self.client.get("/api/v1/search/products?q=wireless")

    @task(1)
    def check_health(self):
        self.client.get("/api/v1/health")