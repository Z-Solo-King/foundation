            "operation": "knowledge",
            "strict_zero_cost_only": True,
            # Nightly research is evidence-gated: deterministic fallback cannot count as provider execution.
            "require_model_generation": True,
        }

        url = self.server.public_worker_url.rstrip("/") + "/api/v1/chat"
        request = Request(
            url,
            data=json.dumps(upstream_payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": "Bearer " + self.server.auth_token,