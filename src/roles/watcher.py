class Watcher:
    def run(self, payload: dict) -> dict:
        print("[Watcher] received:", payload)
        return {"role": "Watcher", "output": "dummy output from Watcher"}
