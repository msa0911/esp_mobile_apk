import sys
import time
import select
import termios
import tty

import rclpy
from rclpy.node import Node
from std_msgs.msg import Int16


class KeyboardControl(Node):
    def __init__(self):
        super().__init__('keyboard_control')
        self.left_pub = self.create_publisher(Int16, '/left_wheel', 10)
        self.right_pub = self.create_publisher(Int16, '/right_wheel', 10)
        self.speed = 210
        self.left = 0
        self.right = 0
        self.running = True
        self.last_key = time.monotonic()
        self.key_timeout = 0.4
        self.create_timer(0.1, self.publish_motors)

    def publish_motors(self):
        # Requiring fresh keyboard input prevents stale motion commands.
        if time.monotonic() - self.last_key > self.key_timeout:
            self.left = self.right = 0
        self.left_pub.publish(Int16(data=int(self.left)))
        self.right_pub.publish(Int16(data=int(self.right)))

    def process_key(self, key):
        key = key.lower()
        if key == '+':
            self.speed = min(255, self.speed + 25)
        elif key == '-':
            self.speed = max(0, self.speed - 25)
        elif key == 'w':
            self.left, self.right = self.speed, self.speed
        elif key == 's':
            self.left, self.right = -self.speed, -self.speed
        elif key == 'a':
            self.left, self.right = -self.speed, self.speed
        elif key == 'd':
            self.left, self.right = self.speed, -self.speed
        elif key == 'q':
            self.left, self.right = self.speed // 2, self.speed
        elif key == 'e':
            self.left, self.right = self.speed, self.speed // 2
        elif key == ' ':
            self.left = self.right = 0
        elif key == 'x':
            self.left = self.right = 0
            self.running = False
        else:
            return
        self.last_key = time.monotonic()
        print(f'\rLeft: {self.left:4d} | Right: {self.right:4d} | Speed: {self.speed:3d}   ', end='', flush=True)


def main(args=None):
    if not sys.stdin.isatty():
        raise RuntimeError('Run keyboard_control in an interactive terminal')
    rclpy.init(args=args)
    node = KeyboardControl()
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    print('W/S forward/back | A/D rotate | Q/E curves | +/- speed | Space stop | X exit')
    print('Hold or repeatedly press a movement key; stops after 0.4s without input.')
    try:
        tty.setcbreak(fd)
        while rclpy.ok() and node.running:
            ready, _, _ = select.select([sys.stdin], [], [], 0.02)
            if ready:
                node.process_key(sys.stdin.read(1))
            rclpy.spin_once(node, timeout_sec=0)
    except KeyboardInterrupt:
        pass
    finally:
        node.left = node.right = 0
        for _ in range(3):
            node.publish_motors()
            time.sleep(0.02)
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        node.destroy_node()
        rclpy.shutdown()
        print('\nStopped.')


if __name__ == '__main__':
    main()
