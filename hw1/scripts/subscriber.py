#!/usr/bin/env python

import rospy
from std_msgs.msg import String

def callback(data):
    rospy.loginfo('received: %s', data.data)

def subscriber():
    rospy.init_node('subscriber', anonymous=True)
    rospy.Subscriber("random_strings", String, callback)
    rospy.loginfo('Listening on the chatter topic...')
    rospy.spin()
if __name__ == '__main__':
    subscriber()
