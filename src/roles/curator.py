class Curator:
    def run(self, payload: dict) -> dict:
        print("[Curator] received:", payload)
        return {"role": "Curator", "output": "dummy output from Curator"}
