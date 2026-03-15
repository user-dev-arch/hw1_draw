# github repo
# https://github.com/user-dev-arch/hw1_draw

#!/usr/bin/env python3
import math
import threading

import rospy
from geometry_msgs.msg import Twist
from std_srvs.srv import Empty
from turtlesim.srv import Spawn, SetPen, TeleportAbsolute

# Canvas is 11.1 x 11.1 units
DIGIT_ZONES = [
    ('turtle1', 0, 1.5, 5.8, (255, 255, 255)),
    ('turtle2', 1, 4.0, 5.8, (255, 255, 255)),
    ('turtle3', 2, 6.5, 5.8, (255, 255, 255)),
    ('turtle4', 4, 9.0, 5.8, (255, 255, 255)),
]


def pen_up(turtle):
    rospy.ServiceProxy('/{}/set_pen'.format(turtle), SetPen)(255, 255, 255, 2, 1)


def pen_down(turtle, r, g, b, width=3):
    rospy.ServiceProxy('/{}/set_pen'.format(turtle), SetPen)(r, g, b, width, 0)


def teleport(turtle, x, y, angle):
    rospy.ServiceProxy('/{}/teleport_absolute'.format(turtle), TeleportAbsolute)(x, y, angle)


def move(pub, speed, turn_rate, duration, hz=30):
    # turn_rate > 0 is CCW, < 0 is CW. Arc radius = |speed / turn_rate|.
    cmd = Twist()
    cmd.linear.x = speed
    cmd.angular.z = turn_rate

    rate = rospy.Rate(hz)
    end_time = rospy.Time.now() + rospy.Duration(duration)
    while rospy.Time.now() < end_time and not rospy.is_shutdown():
        pub.publish(cmd)
        rate.sleep()

    pub.publish(Twist())


def draw_zero(turtle, cx, cy, pub, r, g, b):
    speed        = 0.80
    radius_right = 0.78
    radius_left  = 0.72

    pen_up(turtle)
    teleport(turtle, cx, cy + radius_right, 0.0)
    pen_down(turtle, r, g, b, 3)

    turn_rate_right = speed / radius_right
    move(pub, speed, -turn_rate_right, math.pi / turn_rate_right)

    turn_rate_left = speed / radius_left
    move(pub, speed, -turn_rate_left, math.pi / turn_rate_left + 0.05)


def draw_one(turtle, cx, cy, pub, r, g, b):
    top_y = cy + 0.95
    bot_y = cy - 0.95

    # Diagonal entry arm, like the right side of an upward arrow.
    arm_x = cx - 0.38
    arm_y = cy + 0.42
    heading_to_top = math.atan2(top_y - arm_y, cx - arm_x)

    pen_up(turtle)
    teleport(turtle, arm_x, arm_y, heading_to_top)
    pen_down(turtle, r, g, b, 3)
    move(pub, 0.68, +0.08, 0.96)

    # Vertical downstroke with a slight rightward lean.
    pen_up(turtle)
    teleport(turtle, cx, top_y, -math.pi / 2)
    pen_down(turtle, r, g, b, 3)
    move(pub, 0.95, -0.06, (top_y - bot_y) / 0.95)


def draw_two(turtle, cx, cy, pub, r, g, b):
    ARC_SPEED   = 0.62
    BUMP_RADIUS = 0.42
    bump_cy     = cy + 0.53

    bump_omega = ARC_SPEED / BUMP_RADIUS
    bump_time  = math.pi / bump_omega  # time for 180 degrees

    # Top bump: CW semicircle, starts left of centre facing north.
    pen_up(turtle)
    teleport(turtle, cx - BUMP_RADIUS, bump_cy, math.pi / 2)
    pen_down(turtle, r, g, b, 3)
    move(pub, ARC_SPEED, -bump_omega, bump_time)

    # Swoop down and to the left, continuing the same CW direction.
    move(pub, 0.78, -0.52, 2.15)

    # Base stroke.
    pen_up(turtle)
    teleport(turtle, cx - 0.50, cy - 0.95, 0.0)
    pen_down(turtle, r, g, b, 3)
    move(pub, 1.05, +0.04, 0.95)


def draw_four(turtle, cx, cy, pub, r, g, b):
    top_y   = cy + 0.95
    mid_y   = cy + 0.08
    bot_y   = cy - 0.95
    left_x  = cx - 0.42
    right_x = cx + 0.35
    SPEED   = 0.80

    # Left vertical, top to crossbar.
    pen_up(turtle)
    teleport(turtle, left_x, top_y, -math.pi / 2)
    pen_down(turtle, r, g, b, 3)
    move(pub, SPEED, +0.22, (top_y - mid_y) / SPEED)

    # Horizontal crossbar.
    pen_up(turtle)
    teleport(turtle, left_x, mid_y, 0.0)
    pen_down(turtle, r, g, b, 3)
    move(pub, SPEED, +0.20, (right_x - left_x) / SPEED)

    # Right vertical, full height.
    pen_up(turtle)
    teleport(turtle, right_x, top_y, -math.pi / 2)
    pen_down(turtle, r, g, b, 3)
    move(pub, SPEED, -0.13, (top_y - bot_y) / SPEED)


def draw_worker(turtle, digit, cx, cy, color):
    pub = rospy.Publisher('/{}/cmd_vel'.format(turtle), Twist, queue_size=10)
    rospy.sleep(0.8)

    pen_up(turtle)
    rospy.sleep(0.1)

    r, g, b = color
    rospy.loginfo('[{}] drawing digit {}'.format(turtle, digit))

    draw_fn = {0: draw_zero, 1: draw_one, 2: draw_two, 4: draw_four}
    if digit in draw_fn:
        draw_fn[digit](turtle, cx, cy, pub, r, g, b)

    pen_up(turtle)
    rospy.loginfo('[{}] done'.format(turtle))


def main():
    rospy.init_node('digit_drawer_U2210124')

    rospy.loginfo('Waiting for turtlesim...')
    for service in ['/spawn', '/clear', '/turtle1/set_pen', '/turtle1/teleport_absolute']:
        rospy.wait_for_service(service)

    rospy.ServiceProxy('/clear', Empty)()

    # turtle1 is created
    spawn = rospy.ServiceProxy('/spawn', Spawn)
    for name, _, x, y, _ in DIGIT_ZONES[1:]:
        try:
            spawn(x, y, 0.0, name)
        except rospy.ServiceException as e:
            rospy.logwarn('spawn failed for {}: {}'.format(name, e))

    for name, *_ in DIGIT_ZONES[1:]:
        rospy.wait_for_service('/{}/set_pen'.format(name))
        rospy.wait_for_service('/{}/teleport_absolute'.format(name))
    rospy.sleep(0.5)

    threads = [
        threading.Thread(
            target=draw_worker,
            args=(name, digit, cx, cy, color),
            daemon=True,
        )
        for name, digit, cx, cy, color in DIGIT_ZONES
    ]

    rospy.loginfo('Drawing 0 1 2 4 in parallel...')
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    rospy.loginfo('Done.')


if __name__ == '__main__':
    try:
        main()
    except rospy.ROSInterruptException:
        pass