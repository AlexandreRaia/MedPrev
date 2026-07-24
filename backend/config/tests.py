from django.test import Client, SimpleTestCase


class HealthEndpointTests(SimpleTestCase):
    def test_api_responde_com_status_ok(self) -> None:
        response = Client().get("/api/v1/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "ok",
                "service": "medprev-api",
            },
        )
