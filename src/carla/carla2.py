__author__ = "Erdi Örün, Mehmet Arif Bağcı, İlyas Çavdır"
__copyright__ = "Copyright 2023, Trakya University"
__version__ = "0.9.0"
__status__ = "Development"

import time
import numpy as np
import cv2
import random
import pygame
import pyfiglet
import glob
import os
import sys
import lane
try:
    sys.path.append(glob.glob('./dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

import carla


ascii_banner = pyfiglet.figlet_format("Lane Detection")
print(ascii_banner)
print("version: " + __version__ + " \nstatus: " + __status__)


IM_WIDTH = 1280
IM_HEIGHT = 720
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720


def process_image(image):
    # Convert the image to a numpy array
    frame = np.array(image.raw_data)

    # Reshape the array to match the camera sensor's dimensions
    frame = frame.reshape((image.height, image.width, 4))

    # Remove the alpha channel
    frame = frame[:, :, :3]

    # Process the frame with lanes
    processed_frame = process_frame_with_lanes(frame)

    # Display the processed frame using Pygame
    display_frame(processed_frame)


def process_frame_with_lanes(frame):
    # Convert the frame to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Apply Canny edge detection
    edges = cv2.Canny(blurred, 50, 150)

    # Define region of interest (ROI) vertices
    height, width = frame.shape[:2]
    roi_vertices = np.array(
        [(0, height), (width // 2, height // 2), (width, height)], np.int32)

    # Apply a mask to focus on the region of interest
    mask = np.zeros_like(edges)
    cv2.fillPoly(mask, [roi_vertices], 255)
    masked_edges = cv2.bitwise_and(edges, mask)

    # Apply Hough line transformation to detect lanes
    lines = cv2.HoughLinesP(masked_edges, 1, np.pi / 180,
                            threshold=20, minLineLength=20, maxLineGap=300)

    # Create an empty image to draw the lines
    line_image = np.zeros((height, width, 3), dtype=np.uint8)

    # Define colors for the left and right lanes
    left_lane_color = (255, 0, 0)  # Blue
    right_lane_color = (0, 0, 255)  # Red

    if lines is not None:
        # Separate the lines into left and right lanes based on slope
        left_lines = []
        right_lines = []

        for line in lines:
            for x1, y1, x2, y2 in line:
                slope = (y2 - y1) / (x2 - x1)
                if slope < 0:
                    left_lines.append(line)
                else:
                    right_lines.append(line)

        # Draw the left lane lines
        for line in left_lines:
            for x1, y1, x2, y2 in line:
                cv2.line(line_image, (x1, y1), (x2, y2), left_lane_color, 2)

        # Draw the right lane lines
        for line in right_lines:
            for x1, y1, x2, y2 in line:
                cv2.line(line_image, (x1, y1), (x2, y2), right_lane_color, 2)

    # Combine the line image with the original frame
    result = cv2.addWeighted(frame, 0.8, line_image, 1, 0)

    return result


def display_frame(frame):
    frame_flipped = cv2.flip(frame, 1)

    # Convert the frame to RGB for Pygame display
    frame_rgb = cv2.cvtColor(frame_flipped, cv2.COLOR_BGR2RGB)
    frame_rgb = np.rot90(frame_rgb)

    # Display the frame in a Pygame window
    image_surface = pygame.surfarray.make_surface(frame_rgb)
    screen.blit(image_surface, (0, 0))
    pygame.display.update()

# def process_image(image):

#     if (image == []):
#         pass
#     image_data = np.array(image.raw_data)
#     image_data = image_data.reshape((IM_HEIGHT, IM_WIDTH, 4))

#     image_data = image_data[:, :, :3]

#     # Get the current working directory

#     lane_obj = lane.Lane(orig_frame=image_data)

#     lane_line_markings = lane_obj.get_line_markings()

#     lane_obj.plot_roi(plot=False)

#     warped_frame = lane_obj.perspective_transform(plot=False)

#     histogram = lane_obj.calculate_histogram(plot=False)

#     # Find lane line pixels using the sliding window method
#     left_fit, right_fit = lane_obj.get_lane_line_indices_sliding_windows(
#         plot=False)

#     # Fill in the lane line
#     lane_obj.get_lane_line_previous_window(
#         left_fit, right_fit, plot=False)

#     # Overlay lines on the original frame
#     frame_with_lane_lines = lane_obj.overlay_lane_lines(plot=False)

#     # Calculate lane line curvature (left and right lane lines)
#     lane_obj.calculate_curvature(print_to_terminal=False)

#     # Calculate center offset
#     lane_obj.calculate_car_position(print_to_terminal=False)

#     # Display curvature and center offset on image
#     frame_with_lane_lines2 = lane_obj.display_curvature_offset(
#         frame=frame_with_lane_lines, plot=False)

#     image_data = cv2.rotate(image_data, cv2.ROTATE_90_CLOCKWISE)

#     image_data = cv2.flip(image_data, 1)

#     img_surface = pygame.surfarray.make_surface(
#         np.flip(image_data, axis=2))

#     screen.blit(img_surface, (0, 0))

#     pygame.display.flip()


actor_list = []

client = carla.Client("localhost", 2000)
# client.set_timeout(5.0)

world = client.get_world()
# world = client.load_world("Town04")

weather = carla.WeatherParameters(
    cloudiness=100.0,
    precipitation=0.1,
    sun_altitude_angle=10.0)

world.set_weather(weather)

blueprint_library = world.get_blueprint_library()

# araba secimi
vehicle_bp = blueprint_library.filter("model3")[0]

# spawn
spawn_point = random.choice(world.get_map().get_spawn_points())

vehicle = world.spawn_actor(vehicle_bp, spawn_point)

# Set up the vehicle's initial state
vehicle_control = carla.VehicleControl()

spawn_point = carla.Transform(carla.Location(x=1.7, z=1.1))
# spawn_point = carla.Transform(carla.Location(x=2.5, z=1.1))

cam_bp = blueprint_library.find("sensor.camera.rgb")
cam_bp.set_attribute("image_size_x", f"{IM_WIDTH}")
cam_bp.set_attribute("image_size_y", f"{IM_HEIGHT}")
cam_bp.set_attribute("fov", "120")

pygame.init()
clock = pygame.time.Clock()

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

camera_sensor = world.spawn_actor(cam_bp, spawn_point, attach_to=vehicle)

actor_list.append(camera_sensor)

camera_sensor.listen(process_image)


def game_loop():
    while True:
        # Start the Pygame event loop
        vehicle.apply_control(vehicle_control)

        # Handle keyboard events
        handle_events(clock.get_time())

        # Tick the simulation and advance the Pygame clock
        world.tick()
        clock.tick_busy_loop(60)


def handle_events(milliseconds):
    velocity = vehicle.get_velocity()
    speed = 3.6 * (velocity.x**2 + velocity.y**2 +
                   velocity.z**2)**0.5  # convert to km/h
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                vehicle_control.throttle = 0.7
            elif event.key == pygame.K_DOWN:
                vehicle_control.brake = 1.0
            elif event.key == pygame.K_LEFT:
                vehicle_control.steer = -0.2
            elif event.key == pygame.K_RIGHT:
                vehicle_control.steer = 0.2
            elif event.key == pygame.K_q:
                vehicle_control.gear = -1

        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_UP:
                vehicle_control.throttle = 0.0
            elif event.key == pygame.K_DOWN:
                vehicle_control.brake = 0.0
            elif event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                vehicle_control.steer = 0.0


game_loop()
