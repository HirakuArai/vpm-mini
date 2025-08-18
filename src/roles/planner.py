class Planner:
    def run(self, payload: dict) -> dict:
        print("[Planner] received:", payload)
        return {"role": "Planner", "output": "dummy output from Planner"}
