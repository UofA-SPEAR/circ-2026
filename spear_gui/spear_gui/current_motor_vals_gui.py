# import sys
# import rclpy

# from rclpy.node import Node
# from std_msgs.msg import String

# from PySide6.QtCore import QTimer
# from PySide6.QtWidgets import QApplication, QGridLayout, QLabel, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget

# # =========================================================
# # ROS2 NODE
# # =========================================================

# class A_node(Node):
#     def __init__(self):
#         super().__init__('A_node')
#         self.topic_data = {}
#         self.subscription_list = []

#         # -------------------------------------------------
#         # helper
#         # -------------------------------------------------
#         def add_topic(topic_name):
#             self.topic_data[topic_name] = "..."

#             sub = self.create_subscription(
#                 String,
#                 topic_name,
#                 lambda msg, t=topic_name: self.listener_callback(msg, t),
#                 10
#             )
#             self.subscription_list.append(sub)

#         # -------------------------------------------------
#         # misc
#         # -------------------------------------------------
#         misc_topics = [
#             "/ex_temp",
#             "/cpu",
#             "/ram",
#             "/in_temp",
#             "/batt",
#             "/volts",
#             "/connection",
#             "/latency",
#         ]

#         # -------------------------------------------------
#         # wheel topics
#         # -------------------------------------------------
#         wheel_topics = []

#         for i in range(6):
#             wheel_topics.extend([
#                 f"/amps_wheel_{i}",
#                 f"/volts_wheel_{i}",
#                 f"/rpm_wheel_{i}",
#                 f"/req_rpm_wheel_{i}",
#             ])

#         # steering wheels only
#         for i in [0, 1, 4, 5]:
#             wheel_topics.extend([
#                 f"/steer_angle_{i}",
#                 f"/req_steer_angle_{i}",
#             ])

#         # -------------------------------------------------
#         # arm topics
#         # -------------------------------------------------
#         arm_topics = []

#         for i in range(6):
#             arm_topics.extend([
#                 f"/amps_arm_{i}",
#                 f"/volts_arm_{i}",
#                 f"/rpm_arm_{i}",
#                 f"/encoder_in_{i}",
#                 f"/encoder_out_{i}",
#             ])

#         # create all subscriptions
#         for topic in misc_topics + wheel_topics + arm_topics:
#             add_topic(topic)

#     def listener_callback(self, msg, topic_name):
#         self.topic_data[topic_name] = msg.data


# # =========================================================
# # GUI
# # =========================================================
# class Panel(QWidget):
#     def __init__(self, title):
#         super().__init__()

#         self.layout = QVBoxLayout()
#         self.setLayout(self.layout)

#         title_label = QLabel(title)
#         title_label.setObjectName("panelTitle")

#         self.layout.addWidget(title_label)

#         self.layout.setSpacing(6)
#         self.layout.setContentsMargins(12, 12, 12, 12)

#         self.setObjectName("telemetryPanel")

# class MainWindow(QMainWindow):
#     def __init__(self, node):
#         super().__init__()

#         self.node = node

#         self.setWindowTitle("Motor vals and misc")
#         self.resize(1200, 700)

#         self.labels = {}

#         main_grid = QGridLayout()

#         # =================================================
#         # helper functions
#         # =================================================

#         def create_data_label(text="..."):
#             label = QLabel(text)
#             return label

#         def add_topic_label(layout, label_text, topic, label_units):
#             row = QHBoxLayout()

#             title = QLabel(f"{label_text}: ")
#             value = QLabel("...")
#             units = QLabel(label_units)
#             self.labels[topic] = value

#             row.addWidget(title)
#             row.addWidget(value)
#             row.addWidget(units)

#             row.addStretch()
#             layout.addLayout(row)

#         # =================================================
#         # FRONT LEFT WHEEL (0)
#         # =================================================

#         steer_0_panel = Panel("FRONT LEFT")
#         steer_0_layout = steer_0_panel.layout
#         add_topic_label(steer_0_layout, "steer degrees", "/steer_angle_0", "rad")
#         add_topic_label(steer_0_layout, "req steer", "/req_steer_angle_0", "rad")
        
#         main_grid.addWidget(steer_0_panel, 0, 0)

#         wheel_0_panel = Panel("FRONT LEFT")
#         wheel_0_layout = wheel_0_panel.layout
#         add_topic_label(wheel_0_layout, "amps", "/amps_wheel_0", "A")
#         add_topic_label(wheel_0_layout, "volts", "/volts_wheel_0", "V")
#         add_topic_label(wheel_0_layout, "rpm", "/rpm_wheel_0", "rounds/min")
#         add_topic_label(wheel_0_layout, "req rpm", "/req_rpm_wheel_0", "rounds/min")

#         main_grid.addWidget(wheel_0_panel, 1, 1)

#         # =================================================
#         # FRONT RIGHT WHEEL (1)
#         # =================================================

#         steer_1_panel = Panel("FRONT RIGHT")
#         steer_1_layout = steer_1_panel.layout
#         add_topic_label(steer_1_layout, "steer degrees", "/steer_angle_1", "rad")
#         add_topic_label(steer_1_layout, "req steer", "/req_steer_angle_1", "rad")

#         main_grid.addWidget(steer_1_panel, 0, 3)

#         wheel_1_panel = Panel("FRONT RIGHT")
#         wheel_1_layout = wheel_1_panel.layout
#         add_topic_label(wheel_1_layout, "amps", "/amps_wheel_1", "A")
#         add_topic_label(wheel_1_layout, "volts", "/volts_wheel_1", "V")
#         add_topic_label(wheel_1_layout, "rpm", "/rpm_wheel_1", "rounds/min")
#         add_topic_label(wheel_1_layout, "req rpm", "/req_rpm_wheel_1", "rounds/min")

#         main_grid.addWidget(wheel_1_panel, 1, 2)

#         # =================================================
#         # MID WHEELS
#         # =================================================
#         wheel_2_panel = Panel("MID LEFT")
#         wheel_2_layout = wheel_2_panel.layout
#         # wheel_2_layout.addWidget(QLabel(" "))
#         add_topic_label(wheel_2_layout, "amps", "/amps_wheel_2", "A")
#         add_topic_label(wheel_2_layout, "volts", "/volts_wheel_2", "V")
#         add_topic_label(wheel_2_layout, "rpm", "/rpm_wheel_2", "rounds/min")
#         add_topic_label(wheel_2_layout, "req rpm", "/req_rpm_wheel_2", "rounds/min")
#         main_grid.addWidget(wheel_2_panel, 2, 1)

#         wheel_3_panel = Panel("MID RIGHT")
#         wheel_3_layout = wheel_3_panel.layout
#         # wheel_3_layout.addWidget(QLabel(" "))
#         add_topic_label(wheel_3_layout, "amps", "/amps_wheel_3", "A")
#         add_topic_label(wheel_3_layout, "volts", "/volts_wheel_3", "V")
#         add_topic_label(wheel_3_layout, "rpm", "/rpm_wheel_3", "rounds/min")
#         add_topic_label(wheel_3_layout, "req rpm", "/req_rpm_wheel_3", "rounds/min")
#         main_grid.addWidget(wheel_3_panel, 2, 2)

#         # =================================================
#         # BACK WHEELS
#         # =================================================
#         wheel_4_panel = Panel("BACK LEFT")
#         wheel_4_layout = wheel_4_panel.layout
#         # wheel_4_layout.addWidget(QLabel(" "))
#         add_topic_label(wheel_4_layout, "amps", "/amps_wheel_4", "A")
#         add_topic_label(wheel_4_layout, "volts", "/volts_wheel_4", "V")
#         add_topic_label(wheel_4_layout, "rpm", "/rpm_wheel_4", "rounds/min")
#         add_topic_label(wheel_4_layout, "req rpm", "/req_rpm_wheel_4", "rounds/min")
#         main_grid.addWidget(wheel_4_panel, 3, 1)

#         wheel_5_panel = Panel("BACK RIGHT")
#         wheel_5_layout = wheel_5_panel.layout
#         # wheel_5_layout.addWidget(QLabel(" "))
#         add_topic_label(wheel_5_layout, "amps", "/amps_wheel_5", "A")
#         add_topic_label(wheel_5_layout, "volts", "/volts_wheel_5", "V")
#         add_topic_label(wheel_5_layout, "rpm", "/rpm_wheel_5", "rounds/min")
#         add_topic_label(wheel_5_layout, "req rpm", "/req_rpm_wheel_5", "rounds/min")
#         main_grid.addWidget(wheel_5_panel, 3, 2)

#         # =================================================
#         # BACK STEERING
#         # =================================================

#         steer_4_panel = Panel("BACK LEFT")
#         steer_4_layout = steer_4_panel.layout
#         add_topic_label(steer_4_layout, "steer degrees", "/steer_angle_4", "rad")
#         add_topic_label(steer_4_layout, "req steer", "/req_steer_angle_4", "rad")
#         main_grid.addWidget(steer_4_panel, 4, 0)

#         steer_5_panel = Panel("BACK RIGHT")
#         steer_5_layout = steer_5_panel.layout
#         add_topic_label(steer_5_layout, "steer degrees", "/steer_angle_5", "rad")
#         add_topic_label(steer_5_layout, "req steer", "/req_steer_angle_5", "rad")
#         main_grid.addWidget(steer_5_panel, 4, 3)

#         # =================================================
#         # ARM
#         # =================================================

#         for arm_id in range(6):
#             panel = Panel(f"ARM {arm_id}")
#             layout = panel.layout
#             # layout = QVBoxLayout()
#             # layout.addWidget(QLabel(" "))
#             # layout.addWidget(QLabel(f"ARM {arm_id}"))

#             add_topic_label(layout, "amps", f"/amps_arm_{arm_id}", "A")
#             add_topic_label(layout, "volts", f"/volts_arm_{arm_id}", "V")
#             add_topic_label(layout, "rpm", f"/rpm_arm_{arm_id}", "rounds/min")
#             add_topic_label(layout, "encoder in", f"/encoder_in_{arm_id}", "rpm")
#             add_topic_label(layout, "encoder out", f"/encoder_out_{arm_id}", "rpm")

#             main_grid.addWidget(panel, arm_id, 5)

#         # =================================================
#         # MISC
#         # =================================================

#         misc_topics = [
#             ("External Temp", "/ex_temp", "°C"),
#             ("CPU", "/cpu", "%"),
#             ("RAM", "/ram", "%"),
#             ("Internal Temp", "/in_temp", "°C"),
#             ("Battery", "/batt", "%"),
#             ("Voltage", "/volts", "V"),
#             ("Connection", "/connection", "Mbps"),
#             ("Latency", "/latency", "ms"),
#         ]

#         for row, (label_name, topic, units) in enumerate(misc_topics):

#             layout = QVBoxLayout()
#             add_topic_label(layout, label_name, topic, units)
#             main_grid.addLayout(layout, row, 7)

#         # =================================================
#         # FINALIZE WINDOW
#         # =================================================

#         container = QWidget()
#         container.setLayout(main_grid)

#         self.setCentralWidget(container)

#         # =================================================
#         # update timer
#         # =================================================

#         self.gui_timer = QTimer()

#         self.gui_timer.timeout.connect(self.update_gui)

#         self.gui_timer.start(100)

#     # =====================================================
#     # update GUI values
#     # =====================================================

#     def update_gui(self):
#         for topic, label in self.labels.items():
#             value = self.node.topic_data.get(topic, "...")
#             label.setText(str(value))

# # =========================================================
# # MAIN
# # =========================================================

# def main(args=None):

#     rclpy.init(args=args)

#     node = A_node()

#     app = QApplication(sys.argv)
#     app.setStyleSheet("""
#         QMainWindow {
#             background-color: #0f1117;
#         }

#         QWidget {
#             color: #d6d6d6;
#             font-size: 13px;
#         }

#         #telemetryPanel {
#             background-color: #1a1d26;
#             border: 1px solid #2c3240;
#             border-radius: 12px;
#         }

#         #panelTitle {
#             font-size: 16px;
#             font-weight: bold;
#             color: #7aa2ff;
#             padding-bottom: 8px;
#         }
#         """)

#     window = MainWindow(node)

#     window.show()

#     # ROS spin timer
#     ros_timer = QTimer()

#     ros_timer.timeout.connect(
#         lambda: rclpy.spin_once(node, timeout_sec=0)
#     )

#     ros_timer.start(10)

#     app.exec()

#     node.destroy_node()

#     rclpy.shutdown()


# if __name__ == '__main__':
#     main()

# #source /opt/ros/humble/setup.bash
# #source install/setup.bash