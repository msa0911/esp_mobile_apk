import socket
import time
import threading

import rclpy
from rclpy.node import Node
from std_msgs.msg import Int16


class MotorBridge(Node):
    def __init__(self):
        super().__init__('esp32_motor_bridge')
        self.declare_parameter('host', '192.168.4.1')
        self.declare_parameter('port', 8888)
        self.declare_parameter('command_timeout', 0.5)
        self.host = self.get_parameter('host').value
        self.port = int(self.get_parameter('port').value)
        self.timeout = float(self.get_parameter('command_timeout').value)
        self.left = 0
        self.right = 0
        self.left_time = time.monotonic()
        self.right_time = time.monotonic()
        self.sock = None
        self.lock = threading.Lock()
        self.create_subscription(Int16, '/left_wheel', self.on_left, 10)
        self.create_subscription(Int16, '/right_wheel', self.on_right, 10)
        self.create_timer(0.1, self.send_command)
        self.last_warning = 0.0

    def on_left(self, msg):
        self.left = max(-255, min(255, int(msg.data)))
        self.left_time = time.monotonic()

    def on_right(self, msg):
        self.right = max(-255, min(255, int(msg.data)))
        self.right_time = time.monotonic()

    def connect(self):
        if self.sock is not None:
            return True
        try:
            self.sock = socket.create_connection((self.host, self.port), timeout=0.3)
            self.sock.settimeout(0.3)
            self.get_logger().info(f'Connected to ESP32 at {self.host}:{self.port}')
            return True
        except OSError as exc:
            now = time.monotonic()
            if now - self.last_warning > 3:
                self.get_logger().warning(f'ESP32 connection failed: {exc}')
                self.last_warning = now
            return False

    def send_command(self):
        now = time.monotonic()
        left = self.left if now - self.left_time < self.timeout else 0
        right = self.right if now - self.right_time < self.timeout else 0
        if not self.connect():
            return
        try:
            self.sock.sendall(f'L:{left},R:{right}\n'.encode('ascii'))
        except OSError as exc:
            self.get_logger().warning(f'ESP32 disconnected: {exc}')
            self.close_socket()

    def close_socket(self):
        if self.sock is not None:
            try:
                self.sock.close()
            except OSError:
                pass
            self.sock = None

    def destroy_node(self):
        if self.sock is not None:
            try:
                self.sock.sendall(b'L:0,R:0\n')
            except OSError:
                pass
        self.close_socket()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = MotorBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
