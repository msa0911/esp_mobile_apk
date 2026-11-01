import time
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from std_msgs.msg import Int16

class JoystickControl(Node):
    def __init__(self):
        super().__init__('joystick_control')
        self.declare_parameter('forward_axis', 1)
        self.declare_parameter('turn_axis', 0)
        self.declare_parameter('forward_sign', 1.0)
        self.declare_parameter('turn_sign', 1.0)
        self.declare_parameter('enable_button', 0)
        self.declare_parameter('require_enable_button', True)
        self.declare_parameter('max_pwm', 180)
        self.declare_parameter('deadzone', 0.12)
        self.declare_parameter('joy_timeout', 0.5)
        self.left_pub = self.create_publisher(Int16, '/left_wheel', 10)
        self.right_pub = self.create_publisher(Int16, '/right_wheel', 10)
        self.create_subscription(Joy, '/joy', self.on_joy, 10)
        self.last_joy = 0.0
        self.left = self.right = 0
        self.timer = self.create_timer(0.1, self.publish_commands)
        self.get_logger().info('Joystick ready. Hold enable button to drive.')

    def on_joy(self, msg):
        self.last_joy = time.monotonic()
        fa = int(self.get_parameter('forward_axis').value)
        ta = int(self.get_parameter('turn_axis').value)
        eb = int(self.get_parameter('enable_button').value)
        required = bool(self.get_parameter('require_enable_button').value)
        if fa < 0 or ta < 0 or fa >= len(msg.axes) or ta >= len(msg.axes):
            self.left = self.right = 0
            self.get_logger().warn('Joystick axis index not available', throttle_duration_sec=5.0)
            return
        if required and (eb < 0 or eb >= len(msg.buttons) or not msg.buttons[eb]):
            self.left = self.right = 0
            return
        deadzone = float(self.get_parameter('deadzone').value)
        forward = float(msg.axes[fa]) * float(self.get_parameter('forward_sign').value)
        turn = float(msg.axes[ta]) * float(self.get_parameter('turn_sign').value)
        forward = 0.0 if abs(forward) < deadzone else forward
        turn = 0.0 if abs(turn) < deadzone else turn
        # Normalize mixed commands to preserve curvature without exceeding range.
        left, right = forward - turn, forward + turn
        scale = max(1.0, abs(left), abs(right))
        max_pwm = max(0, min(255, int(self.get_parameter('max_pwm').value)))
        self.left = round(left / scale * max_pwm)
        self.right = round(right / scale * max_pwm)

    def publish_commands(self):
        if time.monotonic() - self.last_joy > float(self.get_parameter('joy_timeout').value):
            self.left = self.right = 0
        self.left_pub.publish(Int16(data=int(self.left)))
        self.right_pub.publish(Int16(data=int(self.right)))

    def stop(self):
        self.left_pub.publish(Int16(data=0))
        self.right_pub.publish(Int16(data=0))

def main(args=None):
    rclpy.init(args=args)
    node = JoystickControl()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.stop()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
