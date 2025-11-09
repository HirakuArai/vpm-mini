from http.server import BaseHTTPRequestHandler, HTTPServer
import os, time
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        body = f"metrics-echo ok ts={int(time.time())} target={os.getenv('TARGET','dev')}\n"
        self.send_response(200); self.send_header("Content-Type","text/plain; charset=utf-8")
        self.end_headers(); self.wfile.write(body.encode())
if __name__=="__main__":
    HTTPServer(("0.0.0.0", int(os.getenv("PORT","8080"))), H).serve_forever()
