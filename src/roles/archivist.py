class Archivist:
    def run(self, payload: dict) -> dict:
        print("[Archivist] received:", payload)
        return {"role": "Archivist", "output": "dummy output from Archivist"}
