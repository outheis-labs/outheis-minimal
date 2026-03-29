"""
Signal transport.

Receives messages from Signal via signal-cli JSON-RPC,
writes to messages.jsonl, watches for responses, sends back.
"""

from __future__ import annotations

import threading
import time
from pathlib import Path

from outheis.core.config import Config, get_messages_path
from outheis.core.message import Message, create_user_message
from outheis.core.queue import append, read_last_n
from outheis.transport.base import Transport
from outheis.transport.signal_rpc import SignalRPC, SignalMessage


class SignalTransport(Transport):
    """
    Signal Messenger transport.
    
    Runs two threads:
    - Main thread: receives Signal messages, writes to queue
    - Watcher thread: monitors queue for responses, sends back via Signal
    """
    
    name = "signal"
    
    def __init__(self, config: Config):
        """
        Args:
            config: outheis configuration
        """
        self.config = config
        
        # Validate config
        if not config.signal or not config.signal.bot_phone:
            raise ValueError("signal.bot_phone not configured")
        if not config.user.phone:
            raise ValueError("user.phone not configured")
        
        self.bot_phone = config.signal.bot_phone
        self.user_phone = config.user.phone
        self.user_uuid: str | None = None  # Learned on first message
        
        self.rpc = SignalRPC(self.bot_phone)
        self.queue_path = get_messages_path()
        
        # Pending responses: {message_id: sender_uuid}
        self.pending: dict[str, str] = {}
        self._lock = threading.Lock()
        
        # Watcher thread control
        self._watching = False
        self._watcher_thread: threading.Thread | None = None
        
        # Optional: Whisper for voice
        self.whisper_model = None
        self._init_whisper()
    
    def _init_whisper(self) -> None:
        """Initialize Whisper for voice transcription (optional)."""
        try:
            from faster_whisper import WhisperModel
            print("🎤 Loading Whisper model...", flush=True)
            self.whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
            print("✓ Whisper loaded", flush=True)
        except ImportError:
            print("ℹ️  Whisper not available (install faster-whisper for voice)", flush=True)
    
    def _is_allowed(self, msg: SignalMessage) -> bool:
        """Check if sender is allowed (single-user mode: only user.phone)."""
        # Check UUID if we know it
        if self.user_uuid and msg.sender_uuid == self.user_uuid:
            return True
        
        # Check phone number
        if msg.sender_phone and msg.sender_phone == self.user_phone:
            # Learn UUID for future
            self.user_uuid = msg.sender_uuid
            return True
        
        return False
    
    def _transcribe_voice(self, audio_data: bytes) -> str | None:
        """Transcribe voice message with Whisper."""
        if not self.whisper_model:
            return None
        
        import tempfile
        
        try:
            # Write to temp file
            with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f:
                f.write(audio_data)
                temp_path = f.name
            
            # Transcribe
            segments, _ = self.whisper_model.transcribe(
                temp_path,
                language="de",  # TODO: from config.user.language
                beam_size=5,
            )
            
            text = " ".join(s.text.strip() for s in segments)
            
            # Cleanup
            Path(temp_path).unlink(missing_ok=True)
            
            return text if text else None
            
        except Exception as e:
            print(f"⚠️ Transcription error: {e}", flush=True)
            return None
    
    def send(self, text: str) -> Message:
        """Create and queue a user message."""
        msg = create_user_message(
            text=text,
            channel="signal",
            identity=self.user_phone or "signal_user",
        )
        append(self.queue_path, msg)
        return msg
    
    def wait_for_response(self, message_id: str, timeout: float = 30.0) -> Message | None:
        """Wait for a response (used internally by watcher)."""
        start = time.time()
        
        while time.time() - start < timeout:
            messages = read_last_n(self.queue_path, 20)
            
            for msg in messages:
                if (
                    msg.reply_to == message_id
                    and msg.to == "transport"
                    and msg.from_agent
                ):
                    return msg
            
            time.sleep(0.5)
        
        return None
    
    def _watch_responses(self) -> None:
        """Watcher thread: check for responses and send back via Signal."""
        while self._watching:
            time.sleep(1)  # Check every second
            
            with self._lock:
                pending_copy = dict(self.pending)
            
            if not pending_copy:
                continue
            
            # Check for responses
            messages = read_last_n(self.queue_path, 30)
            
            for msg in messages:
                if msg.reply_to in pending_copy and msg.to == "transport":
                    sender_uuid = pending_copy[msg.reply_to]
                    response_text = msg.payload.get("text", "")
                    
                    if response_text:
                        try:
                            self.rpc.send_message(sender_uuid, response_text)
                            print(f"📤 Sent response to Signal", flush=True)
                        except Exception as e:
                            print(f"⚠️ Failed to send: {e}", flush=True)
                    
                    # Remove from pending
                    with self._lock:
                        self.pending.pop(msg.reply_to, None)
    
    def _handle_message(self, msg: SignalMessage) -> None:
        """Handle incoming Signal message."""
        # Check authorization
        if not self._is_allowed(msg):
            print(f"⚠️ Unauthorized: {msg.sender_phone}", flush=True)
            return
        
        text = msg.text
        
        # Handle voice message
        if msg.is_voice and msg.attachments:
            print("🎤 Voice message, transcribing...", flush=True)
            
            voice_att = next(
                (a for a in msg.attachments if a.get("contentType", "").startswith("audio/")),
                None
            )
            
            if voice_att and voice_att.get("id"):
                audio_data = self.rpc.get_attachment(voice_att["id"])
                if audio_data:
                    transcribed = self._transcribe_voice(audio_data)
                    if transcribed:
                        print(f"✓ Transcribed: {transcribed[:50]}...", flush=True)
                        text = transcribed
        
        if not text.strip():
            return
        
        print(f"📩 {msg.sender_name}: {text[:60]}{'...' if len(text) > 60 else ''}", flush=True)
        
        # Create message and add to queue
        user_msg = create_user_message(
            text=text,
            channel="signal",
            identity=msg.sender_phone or msg.sender_uuid,
        )
        append(self.queue_path, user_msg)
        
        # Track for response
        with self._lock:
            self.pending[user_msg.id] = msg.sender_uuid
        
        print(f"💬 Queued [{user_msg.id[:8]}], waiting for response...", flush=True)
    
    def run(self) -> None:
        """Run Signal transport main loop."""
        print("\n" + "=" * 50)
        print("Signal Transport")
        print("=" * 50)
        print(f"Bot phone: {self.bot_phone}")
        print(f"User phone: {self.user_phone}")
        print(f"Voice: {'✓' if self.whisper_model else '✗'}")
        print("=" * 50 + "\n")
        
        # Start RPC
        print("Starting signal-cli...", flush=True)
        self.rpc.start()
        self.rpc.subscribe()
        print("✓ signal-cli connected", flush=True)
        
        # Start watcher thread
        self._watching = True
        self._watcher_thread = threading.Thread(target=self._watch_responses, daemon=True)
        self._watcher_thread.start()
        print("✓ Response watcher started", flush=True)
        
        print("\n👂 Listening for Signal messages...\n")
        
        try:
            while True:
                msg = self.rpc.read_message()
                if msg:
                    self._handle_message(msg)
        
        except KeyboardInterrupt:
            print("\n\n👋 Signal Transport shutting down...")
        finally:
            self._watching = False
            self.rpc.stop()
