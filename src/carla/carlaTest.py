from __future__ import print_function


import glob
import os
import sys

try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

# ==============================================================================
# -- imports -------------------------------------------------------------------
# ==============================================================================
import carla
import time
import numpy as np
import cv2
import random
import pygame

IM_WIDTH = 640
IM_HEIGHT = 480


def process_image(image):
    image_data = np.array(image.raw_data)
    image_data = image_data.reshape((image.height, image.width, 4))

    image_data = image_data[:, :, :3]

    cv2.imshow('Carla RGB Camera', image_data)

    cv2.waitKey(1)


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

# kendi hareket eden arac olusturmak
# vehicle.set_autopilot(True)

# kendi kontrolumuzu ayarlamamiz icin
# steer=yonlendirmek, yani aracin duz gittiginden eminiz
# vehicle.apply_control(carla.VehicleControl(throttle=1.0, steer=0.0))

# Define a function to handle keyboard events


def handle_events():
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                vehicle_control.throttle = 1.0
            elif event.key == pygame.K_DOWN:
                vehicle_control.brake = 1.0
            elif event.key == pygame.K_LEFT:
                vehicle_control.steer = -0.5
            elif event.key == pygame.K_RIGHT:
                vehicle_control.steer = 0.5
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

# Start the Pygame event loop
pygame.init()
clock = pygame.time.Clock()


while True:
    # Handle keyboard events
    handle_events()

    # Apply the updated vehicle control
    vehicle.apply_control(vehicle_control)

    # Tick the simulation and advance the Pygame clock
    world.tick()
    clock.tick_busy_loop(60)

    spawn_point = carla.Transform(carla.Location(x=2.5, z=0.7))

    cam_bp = blueprint_library.find("sensor.camera.rgb")
    cam_bp.set_attribute("image_size_x", f"{IM_WIDTH}")
    cam_bp.set_attribute("image_size_y", f"{IM_HEIGHT}")
    cam_bp.set_attribute("fov", "100")

    camera_sensor = world.spawn_actor(cam_bp, spawn_point, attach_to=vehicle)

    actor_list.append(camera_sensor)

    # camera_sensor.listen(process_image)


# Destroy the vehicle
vehicle.destroy()
