import os
import httpx
import structlog

logger = structlog.get_logger()

class APIClient:
    def __init__(self):
        self.base_url = os.getenv("BACKEND_API_URL", "http://backend:8000")
        self.token = None
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=10.0)

    async def login(self, username: str = "admin", password: str = "admin123") -> bool:
        try:
            response = await self.client.post(
                "/api/auth/login",
                data={"username": username, "password": password}
            )
            if response.status_code == 200:
                self.token = response.json()["access_token"]
                self.client.headers.update({"Authorization": f"Bearer {self.token}"})
                logger.info("API Client logged in successfully")
                return True
            logger.error("API Login failed", status=response.status_code, body=response.text)
            return False
        except Exception as e:
            logger.error("API Login connection error", error=str(e))
            return False

    async def get_stats(self) -> dict:
        try:
            # Login if not logged in
            if not self.token:
                await self.login()
            response = await self.client.get("/api/stats/dashboard")
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            logger.error("Failed to fetch statistics", error=str(e))
            return {}

    async def get_logs(self, limit: int = 100, plate: str | None = None) -> list:
        try:
            if not self.token:
                await self.login()
            params = {"limit": limit}
            if plate:
                params["plate_number"] = plate
            response = await self.client.get("/api/access-logs", params=params)
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            logger.error("Failed to fetch logs", error=str(e))
            return []

    async def get_vehicles(self, query: str | None = None, status: str | None = None) -> list:
        try:
            if not self.token:
                await self.login()
            params = {}
            if query:
                params["query"] = query
            if status:
                params["status"] = status
            response = await self.client.get("/api/vehicles", params=params)
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            logger.error("Failed to fetch vehicles", error=str(e))
            return []

    async def update_vehicle(self, vehicle_id: str, payload: dict) -> bool:
        try:
            if not self.token:
                await self.login()
            response = await self.client.put(f"/api/vehicles/{vehicle_id}", json=payload)
            return response.status_code == 200
        except Exception as e:
            logger.error("Failed to update vehicle", id=vehicle_id, error=str(e))
            return False

    async def get_vehicle_history(self, plate: str) -> list:
        try:
            if not self.token:
                await self.login()
            response = await self.client.get(f"/api/access-logs/history/{plate}")
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            logger.error("Failed to fetch vehicle history", plate=plate, error=str(e))
            return []

api_client = APIClient()
