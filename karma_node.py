import http.server
import json
import os

print("KARMA SOVEREIGN NODE v0.1 — Genesis Online")

class KarmaHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/api/pulse"):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"network": "KARMA Testnet", "status": "online"}).encode())
        else:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    server = http.server.HTTPServer(('0.0.0.0', port), KarmaHandler)
    print(f"API running on port {port}")
    server.serve_forever()
