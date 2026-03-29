"""
Signal CLI JSON-RPC client.

Communicates with signal-cli via JSON-RPC protocol.
"""

from __future__ import annotations

import base64
import json
import subprocess
from dataclasses import dataclass
from typing import Optional


@dataclass
class SignalMessage:
    """Incoming Signal message."""
    sender_uuid: str
    sender_name: str
    sender_phone: str | None
    text: str
    timestamp: int  # Signal server timestamp (unique ID)
    is_voice: bool = False
    attachments: list[dict] | None = None


class SignalRPC:
    """
    JSON-RPC client for signal-cli.
    
    Starts signal-cli in jsonRpc mode and communicates via stdin/stdout.
    """
    
    def __init__(self, phone: str):
        """
        Args:
            phone: Bot's phone number (registered with signal-cli)
        """
        self.phone = phone
        self.process: subprocess.Popen | None = None
        self.request_id = 0
    
    def start(self) -> None:
        """Start signal-cli JSON-RPC process."""
        self.process = subprocess.Popen(
            ["signal-cli", "-a", self.phone, "jsonRpc"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
    
    def stop(self) -> None:
        """Stop signal-cli process."""
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.process = None
    
    def _send_request(self, method: str, params: dict | None = None) -> dict:
        """Send JSON-RPC request and return response."""
        if not self.process:
            raise RuntimeError("SignalRPC not started")
        
        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params or {},
        }
        
        self.process.stdin.write(json.dumps(request) + "\n")
        self.process.stdin.flush()
        
        # Read response
        response_line = self.process.stdout.readline()
        if not response_line or not response_line.strip():
            return {}
        
        try:
            return json.loads(response_line)
        except json.JSONDecodeError:
            return {}
    
    def subscribe(self) -> None:
        """Subscribe to receive messages."""
        self._send_request("subscribeReceive")
    
    def read_message(self) -> SignalMessage | None:
        """
        Read next message (blocking).
        
        Returns None for non-message events.
        """
        if not self.process:
            raise RuntimeError("SignalRPC not started")
        
        line = self.process.stdout.readline()
        if not line:
            return None
        
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            return None
        
        # Check if this is a receive event
        if data.get("method") != "receive":
            return None
        
        params = data.get("params", {})
        envelope = params.get("envelope", {})
        if not envelope:
            return None
        
        # Extract message data
        data_msg = envelope.get("dataMessage")
        sync_msg = envelope.get("syncMessage")
        
        # Only incoming messages (not sent-by-self)
        if not data_msg or sync_msg:
            return None
        
        sender_uuid = envelope.get("sourceUuid", "")
        sender_name = envelope.get("sourceName", "Unknown")
        sender_phone = envelope.get("sourceNumber")
        message_text = data_msg.get("message") or ""
        timestamp = envelope.get("timestamp", 0)
        
        # Debug: print envelope keys
        print(f"📨 Envelope: uuid={sender_uuid[:8] if sender_uuid else 'None'}... phone={sender_phone} name={sender_name}", flush=True)
        
        # Check for voice message
        attachments = data_msg.get("attachments", [])
        is_voice = any(
            a.get("contentType", "").startswith("audio/") 
            for a in attachments
        )
        
        return SignalMessage(
            sender_uuid=sender_uuid,
            sender_name=sender_name,
            sender_phone=sender_phone,
            text=message_text,
            timestamp=timestamp,
            is_voice=is_voice,
            attachments=attachments if attachments else None,
        )
    
    def send_message(self, recipient_uuid: str, text: str) -> None:
        """
        Send message to a recipient by UUID.
        
        Args:
            recipient_uuid: Recipient's UUID
            text: Message text
        """
        self._send_request("send", {
            "recipient": [recipient_uuid],
            "message": text,
        })
    
    def send_to_phone(self, phone: str, text: str) -> None:
        """
        Send message to a recipient by phone number.
        
        Args:
            phone: Recipient's phone number (e.g. +4917664104484)
            text: Message text
        """
        self._send_request("send", {
            "recipient": [phone],
            "message": text,
        })
    
    def get_user_id(self, phone: str) -> str | None:
        """
        Get UUID for a phone number.
        
        Args:
            phone: Phone number (e.g. +4917664104484)
        
        Returns:
            UUID string or None if not found
        """
        try:
            response = self._send_request("getUserId", {"recipient": phone})
            result = response.get("result")
            if isinstance(result, dict):
                return result.get("uuid")
            return result
        except Exception:
            return None
    
    def get_attachment(self, attachment_id: str) -> bytes | None:
        """Download attachment data."""
        try:
            response = self._send_request("getAttachment", {"id": attachment_id})
            result = response.get("result")
            
            if isinstance(result, str):
                return base64.b64decode(result)
            elif isinstance(result, dict) and "data" in result:
                return base64.b64decode(result["data"])
            
            return None
        except Exception:
            return None
