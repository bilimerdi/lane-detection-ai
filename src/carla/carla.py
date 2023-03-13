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

IM_WIDTH = 640
IM_HEIGHT = 480


def process_image(image):
    i = np.array(image.raw_data)
    i2 = i.reshape((IM_HEIGHT, IM_WIDTH, 4))
    i3 = i2[:, :, 3]
    cv2.imshow("", i3)
    cv2.waitKey(1)
    return i3/255.0


# bir server olusturdugumuzda genellikle silmek uzere kullanilabilecek liste olustururuz.

actor_list = []

try:
    client = carla.Client("localhost", 2000)
    # client.set_timeout(2.0)

    world = client.get_world()

    # world = client.get_blueprint_library()

    blueprint_library = world.get_blueprint_library()

    # araba secimi
    bp = blueprint_library.filter("model3")[0]

    # spawn
    spawn_point = random.choice(world.get_map().get_spawn_points())

    vehicle = world.spawn_actor(bp, spawn_point)

    # kendi hareket eden arac olusturmak
    # vehicle.set_autopilot(True)

    # kendi kontrolumuzu ayarlamamiz icin
    # steer=yonlendirmek, yani aracin duz gittiginden eminiz
    vehicle.apply_control(carla.VehicleControl(throttle=1.0, steer=0.0))
    actor_list.append(vehicle)

    # sensor ekleme - rgb kamera ekleme

    cam_bp = blueprint_library.find("sensor.camera.rgb")
    cam_bp.set_attribute("image_size_x", f"{IM_WIDTH}")
    cam_bp.set_attribute("image_size_y", f"{IM_HEIGHT}")
    cam_bp.set_attribute("fov", "110")

    spawn_point = carla.Transform(carla.Location(x=2.5, z=0.7))

    sensor = world.spawn_actor(cam_bp, spawn_point, attach_to=vehicle)

    actor_list.append(sensor)

    time.sleep(5)


finally:
    for actor in actor_list:
        actor.destroy()
        print("All cleaned up!")
