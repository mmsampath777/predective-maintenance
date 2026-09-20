"""
Embedded Pure-Python MQTT 3.1.1 Broker.
Provides a zero-dependency MQTT broker running in a background thread
when an external Mosquitto broker is not installed or running.
Supports CONNECT, PUBLISH (QoS 0 & 1), SUBSCRIBE (with '+' wildcards),
SUBACK, PUBACK, PINGREQ/PINGRESP, and DISCONNECT.
"""

import socket
import threading
import struct
import time
import logging

logger = logging.getLogger("EmbeddedMQTTBroker")

class EmbeddedMQTTBroker:
    def __init__(self, host="0.0.0.0", port=1883):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        self.clients = {}  # socket -> {"client_id": str, "subs": set()}
        self.subscriptions = {}  # topic_filter -> set of sockets
        self.lock = threading.Lock()
        self.thread = None

    def start(self) -> bool:
        """Attempt to bind and start broker. Returns True if started, False if port is already in use."""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(50)
            self.running = True
            
            self.thread = threading.Thread(target=self._accept_loop, daemon=True)
            self.thread.start()
            logger.info(f"Embedded MQTT Broker listening on {self.host}:{self.port}")
            print(f"[MQTT Broker] Embedded MQTT Broker started on {self.host}:{self.port}")
            return True
        except OSError as e:
            logger.info(f"Port {self.port} already in use or unavailable ({e}). Using existing external broker.")
            print(f"[MQTT Broker] Port {self.port} already in use. External MQTT broker assumed active.")
            if self.server_socket:
                try:
                    self.server_socket.close()
                except Exception:
                    pass
            self.server_socket = None
            self.running = False
            return False

    def stop(self):
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass
        with self.lock:
            for s in list(self.clients.keys()):
                try:
                    s.close()
                except Exception:
                    pass
            self.clients.clear()
            self.subscriptions.clear()
        print("[MQTT Broker] Embedded MQTT Broker stopped.")

    def _accept_loop(self):
        while self.running:
            try:
                client_sock, addr = self.server_socket.accept()
                with self.lock:
                    self.clients[client_sock] = {"client_id": f"client_{addr[1]}", "subs": set()}
                t = threading.Thread(target=self._client_handler, args=(client_sock,), daemon=True)
                t.start()
            except Exception:
                break

    def _decode_varlen(self, sock):
        multiplier = 1
        value = 0
        while True:
            b = sock.recv(1)
            if not b:
                return None
            digit = b[0]
            value += (digit & 127) * multiplier
            if (digit & 128) == 0:
                break
            multiplier *= 128
        return value

    def _encode_varlen(self, length):
        out = bytearray()
        while True:
            digit = length % 128
            length = length // 128
            if length > 0:
                digit |= 0x80
            out.append(digit)
            if length <= 0:
                break
        return bytes(out)

    def _client_handler(self, sock):
        try:
            while self.running:
                header = sock.recv(1)
                if not header:
                    break
                packet_type = (header[0] >> 4) & 0x0F
                flags = header[0] & 0x0F
                
                rem_len = self._decode_varlen(sock)
                if rem_len is None:
                    break
                
                payload = bytearray()
                while len(payload) < rem_len:
                    chunk = sock.recv(rem_len - len(payload))
                    if not chunk:
                        break
                    payload.extend(chunk)
                if len(payload) < rem_len:
                    break
                
                # 1: CONNECT
                if packet_type == 1:
                    # Send CONNACK (0x20, 0x02, 0x00, 0x00 -> Connection Accepted)
                    sock.sendall(bytes([0x20, 0x02, 0x00, 0x00]))
                
                # 3: PUBLISH
                elif packet_type == 3:
                    dup = bool(flags & 0x08)
                    qos = (flags >> 1) & 0x03
                    retain = bool(flags & 0x01)
                    
                    topic_len = struct.unpack("!H", payload[0:2])[0]
                    topic = payload[2:2+topic_len].decode("utf-8", errors="replace")
                    offset = 2 + topic_len
                    
                    packet_id = 0
                    if qos > 0:
                        packet_id = struct.unpack("!H", payload[offset:offset+2])[0]
                        offset += 2
                        
                    data = bytes(payload[offset:])
                    
                    # Respond with PUBACK if QoS 1
                    if qos == 1:
                        ack = bytearray([0x40, 0x02])
                        ack.extend(struct.pack("!H", packet_id))
                        sock.sendall(ack)
                        
                    # Route to subscribers
                    self._dispatch_publish(topic, data, qos)
                    
                # 8: SUBSCRIBE
                elif packet_type == 8:
                    packet_id = struct.unpack("!H", payload[0:2])[0]
                    offset = 2
                    granted_qos = []
                    while offset < len(payload):
                        t_len = struct.unpack("!H", payload[offset:offset+2])[0]
                        offset += 2
                        sub_topic = payload[offset:offset+t_len].decode("utf-8", errors="replace")
                        offset += t_len
                        req_qos = payload[offset]
                        offset += 1
                        
                        granted_qos.append(req_qos)
                        with self.lock:
                            if sub_topic not in self.subscriptions:
                                self.subscriptions[sub_topic] = set()
                            self.subscriptions[sub_topic].add(sock)
                            if sock in self.clients:
                                self.clients[sock]["subs"].add(sub_topic)
                                
                    # Send SUBACK (0x90, remaining_len, packet_id, [granted_qos...])
                    suback = bytearray([0x90])
                    suback_payload = bytearray()
                    suback_payload.extend(struct.pack("!H", packet_id))
                    suback_payload.extend(granted_qos)
                    suback.extend(self._encode_varlen(len(suback_payload)))
                    suback.extend(suback_payload)
                    sock.sendall(suback)
                    
                # 12: PINGREQ
                elif packet_type == 12:
                    sock.sendall(bytes([0xD0, 0x00]))
                    
                # 14: DISCONNECT
                elif packet_type == 14:
                    break
        except Exception:
            pass
        finally:
            self._cleanup_client(sock)

    def _cleanup_client(self, sock):
        with self.lock:
            if sock in self.clients:
                for sub_topic in self.clients[sock]["subs"]:
                    if sub_topic in self.subscriptions:
                        self.subscriptions[sub_topic].discard(sock)
                        if not self.subscriptions[sub_topic]:
                            del self.subscriptions[sub_topic]
                del self.clients[sock]
        try:
            sock.close()
        except Exception:
            pass

    def _topic_matches(self, pattern: str, topic: str) -> bool:
        """Check if an MQTT topic matches a pattern (handles '+' wildcard)."""
        if pattern == topic or pattern == "#":
            return True
        p_parts = pattern.split("/")
        t_parts = topic.split("/")
        if len(p_parts) != len(t_parts):
            return False
        for p, t in zip(p_parts, t_parts):
            if p != "+" and p != t:
                return False
        return True

    def _dispatch_publish(self, topic: str, data: bytes, qos: int):
        """Dispatch published data to matching subscriber sockets."""
        targets = set()
        with self.lock:
            for pattern, socks in self.subscriptions.items():
                if self._topic_matches(pattern, topic):
                    targets.update(socks)
                    
        if not targets:
            return

        # Prepare PUBLISH packet (QoS 0 for delivery to subscribers)
        topic_bytes = topic.encode("utf-8")
        pub_body = bytearray()
        pub_body.extend(struct.pack("!H", len(topic_bytes)))
        pub_body.extend(topic_bytes)
        pub_body.extend(data)
        
        header = bytearray([0x30])  # PUBLISH QoS 0
        header.extend(self._encode_varlen(len(pub_body)))
        packet = bytes(header + pub_body)
        
        for client_sock in list(targets):
            try:
                client_sock.sendall(packet)
            except Exception:
                self._cleanup_client(client_sock)
