#!/usr/bin/env python3
"""
StudyMate Proxy Server - bypasses CORS for AI API calls
"""
from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import urllib.request
import urllib.error
import logging
import os

logging.basicConfig(level=logging.INFO)

class ProxyHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        logging.info(f"{self.address_string()} - {format % args}")
    
    def do_POST(self):
        if self.path == '/api/chat':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                body = json.loads(post_data)
                
                # Get API key and config from body
                api_key = body.pop('_apiKey', '')
                provider = body.pop('_provider', 'minimax')
                model = body.pop('_model', 'MiniMax-M2.1')
                
                logging.info(f"Provider: {provider}, Model: {model}")
                
                # Build request based on provider
                if provider == 'minimax':
                    api_url = 'https://api.minimax.chat/v1/text/chatcompletion_v2'
                    # MiniMax requires GroupId - this is a demo limitation
                    headers = {
                        'Content-Type': 'application/json',
                        'Authorization': f'Bearer {api_key}'
                    }
                    body['model'] = model
                elif provider == 'openai':
                    api_url = 'https://api.openai.com/v1/chat/completions'
                    headers = {
                        'Content-Type': 'application/json',
                        'Authorization': f'Bearer {api_key}'
                    }
                    body['model'] = model
                elif provider == 'deepseek':
                    api_url = 'https://api.deepseek.com/v1/chat/completions'
                    headers = {
                        'Content-Type': 'application/json',
                        'Authorization': f'Bearer {api_key}'
                    }
                    body['model'] = model
                else:
                    api_url = 'https://api.openai.com/v1/chat/completions'
                    headers = {
                        'Content-Type': 'application/json',
                        'Authorization': f'Bearer {api_key}'
                    }
                
                logging.info(f"Forwarding to {api_url}")
                
                req = urllib.request.Request(
                    api_url,
                    data=json.dumps(body).encode(),
                    headers=headers,
                    method='POST'
                )
                
                with urllib.request.urlopen(req, timeout=90) as response:
                    result = response.read()
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(result)
                    
            except urllib.error.HTTPError as e:
                error_body = e.read()
                logging.error(f"HTTP Error: {e.code}")
                self.send_response(e.code)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(error_body)
            except Exception as e:
                logging.error(f"Error: {e}")
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())
        else:
            self.send_error(404)
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

PORT = 8082
print(f"🚀 Starting StudyMate proxy on http://localhost:{PORT}")
HTTPServer(('0.0.0.0', PORT), ProxyHandler).serve_forever()
