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


IM_WIDTH = 640
IM_HEIGHT = 480


def process_image(image):
    image_data = []
    image_data = np.array(image.raw_data)
    image_data = image_data.reshape((image.height, image.width, 4))

    image_data = image_data[:, :, :3]

    image_data = cv2.rotate(image_data, cv2.ROTATE_90_CLOCKWISE)

    image_data = cv2.flip(image_data, 1)

    img_surface = pygame.surfarray.make_surface(np.flip(image_data, axis=2))

    screen.blit(img_surface, (0, 0))

    pygame.display.flip()

    # deprecated
    # cv2.imshow('Carla RGB Camera', image_data)
    # cv2.waitKey(1)


# bir server olusturdugumuzda genellikle silmek uzere kullanilabilecek liste olustururuz.

actor_list = []

client = carla.Client("localhost", 2000)
# client.set_timeout(2.0)

world = client.get_world()

# world = client.get_blueprint_library()

blueprint_library = world.get_blueprint_library()

# araba secimi
vehicle_bp = blueprint_library.filter("model3")[0]

# spawn
spawn_point = random.choice(world.get_map().get_spawn_points())

vehicle = world.spawn_actor(vehicle_bp, spawn_point)


def handle_events():
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                vehicle_control.throttle = 1.0
            elif event.key == pygame.K_DOWN:
                vehicle_control.brake = 1.0
            elif event.key == pygame.K_LEFT:
                vehicle_control.steer = -0.3
            elif event.key == pygame.K_RIGHT:
                vehicle_control.steer = 0.3
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_UP:
                vehicle_control.throttle = 0.0
            elif event.key == pygame.K_DOWN:
                vehicle_control.brake = 0.0
            elif event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                vehicle_control.steer = 0.0


# Set up the vehicle's initial state
vehicle_control = carla.VehicleControl()
vehicle.apply_control(vehicle_control)

spawn_point = carla.Transform(carla.Location(x=2.5, z=0.7))

cam_bp = blueprint_library.find("sensor.camera.rgb")
cam_bp.set_attribute("image_size_x", f"{IM_WIDTH}")
cam_bp.set_attribute("image_size_y", f"{IM_HEIGHT}")
cam_bp.set_attribute("fov", "100")

pygame.init()
clock = pygame.time.Clock()

SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

while True:
    # Start the Pygame event loop

    # Handle keyboard events
    handle_events()

    # Apply the updated vehicle control
    vehicle.apply_control(vehicle_control)

    # Tick the simulation and advance the Pygame clock
    world.tick()
    clock.tick_busy_loop(60)

    camera_sensor = world.spawn_actor(cam_bp, spawn_point, attach_to=vehicle)

    actor_list.append(camera_sensor)

    camera_sensor.listen(process_image)


# Destroy the vehicle
vehicle.destroy()
