class Synthesizer:
    def run(self, payload: dict) -> dict:
        print("[Synthesizer] received:", payload)
        return {"role": "Synthesizer", "output": "dummy output from Synthesizer"}
