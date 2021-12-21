import logging
import random
import os

import numpy as np

import bpy

logging.getLogger("bpy").setLevel(logging.WARNING)

import addon_utils
import mathutils


def reset_blender():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def clean_blender():
    for i in range(10):
        for attribute in dir(bpy.data):
            try:
                bpy_dataset = getattr(bpy.data, attribute)
                for key, value in bpy_dataset.items():
                    if key != 'camera' and key != 'light' and key != 'Scripting' and not (
                            attribute == 'texts' and key == 'render.py'):
                        bpy_dataset.remove(value)
            except Exception as e:
                pass


def build_camera_light():
    if 'camera' not in bpy.context.scene.objects.keys():
        cam_data = bpy.data.cameras.new('camera')
        cam = bpy.data.objects.new('camera', cam_data)
        bpy.context.collection.objects.link(cam)
        bpy.context.scene.camera = cam

    if 'light' not in bpy.context.scene.objects.keys():
        light_data = bpy.data.lights.new('light', type='POINT')
        # light_data = bpy.data.lights.new('light', type='SUN')
        light = bpy.data.objects.new('light', light_data)
        bpy.context.collection.objects.link(light)


def set_addons():
    addon_data = [
        {'name': 'VRM_Addon_for_Blender-release',
         'url': '',
         'path': './addons/VRM_Addon_for_Blender-release.zip', },
        # {'name': 'mmd_tools',
        #  'url': '',
        #  'path': './addons/mmd_tools-v1.0.1.1.zip', },
        {'name': 'cats-blender-plugin-master',
         'url': '',
         'path': './addons/cats-blender-plugin-master.zip', },
    ]
    for data in addon_data:
        addon_name = data['name']

        # check addon is installed
        installed_module_names = [module.__name__ for module in addon_utils.modules()]
        if not addon_name in installed_module_names:
            addon_path = data['path']
            bpy.ops.preferences.addon_install(overwrite=True, target='DEFAULT', filepath=addon_path)

        # check addon is loaded
        is_loaded = addon_utils.check(addon_name)
        if not is_loaded[0] and not is_loaded[1]:
            addon_utils.enable(addon_name)


def render_settings():
    bpy.data.objects['light'].location = mathutils.Vector((4, -4.2, 5))
    bpy.data.lights['light'].energy = 500

    bpy.data.objects['camera'].location = mathutils.Vector((0.30241375, -1.050002, 1.37315))
    bpy.data.objects['camera'].rotation_euler = mathutils.Euler((1.5708, 0, 0))

    bpy.context.scene.render.image_settings.file_format = 'PNG'

    # engine choosing: https://www.cgdirector.com/best-renderers-render-engines-for-blender/
    # bpy.context.scene.render.engine = 'BLENDER_EEVEE'
    bpy.context.scene.render.engine = 'CYCLES'


def import_model(path_input: str):
    file_extension = path_input.rsplit('.', 1)[-1]
    if file_extension == 'vrm':
        bpy.ops.import_scene.vrm(filepath=path_input)
    elif file_extension == 'pmx':
        # bpy.ops.mmd_tools.import_model(filepath=path_input)
        bpy.ops.cats_importer.import_any_model(filepath=path_input)
    else:
        raise ValueError(f'file extension {file_extension} not supported')


class Renderer:
    def __init__(self):
        clean_blender()
        build_camera_light()
        set_addons()
        render_settings()

        self.current_model = ''

    def import_model(self, path_model: str):
        if self.current_model != path_model:
            print('deleting old model and loading new model')
            clean_blender()
            import_model(path_model)
            self.current_model = path_model

    def render_complex(self, path_output, parameters=None):
        self.set_output_path(path_output)

        self.render()

    @staticmethod
    def render():
        bpy.ops.render.render(write_still=True)

    @staticmethod
    def set_output_path(path_output):
        bpy.context.scene.render.filepath = path_output

    def render_to_numpy_array(self):
        # switch on nodes
        bpy.context.scene.use_nodes = True
        tree = bpy.context.scene.node_tree
        links = tree.links

        # clear default nodes
        # for n in tree.nodes:
        #     tree.nodes.remove(n)

        # create input render layer node
        rl = tree.nodes.new('CompositorNodeRLayers')
        rl.location = 185, 285

        # create output node
        v = tree.nodes.new('CompositorNodeViewer')
        v.location = 750, 210
        v.use_alpha = False

        # Links
        links.new(rl.outputs[0], v.inputs[0])  # link Image output to Viewer input

        # render
        bpy.ops.render.render()

        # get viewer pixels
        pixels = bpy.data.images['Viewer Node'].pixels
        print(len(pixels))  # size is always width * height * 4 (rgba)

        # copy buffer to numpy array for faster manipulation
        arr = np.array(pixels[:])
        print(arr.shape)

    def change_shapekey(self, key, value):
        # find first object which has given key
        bpy.ops.object.select_all(action='DESELECT')  # Deselect all objects
        for obj in bpy.data.objects:
            obj.select_set(True)
            if hasattr(obj.data, 'shape_keys'):
                if key in obj.data.shape_keys.key_blocks:
                    bpy.context.view_layer.objects.active = obj
                    break
            obj.select_set(False)
        print(bpy.context.object)

        # change value
        bpy.context.object.data.shape_keys.key_blocks[key].value = value


if __name__ == '__main__':
    r = Renderer()
    path = '../samples/ini-T式雪ノ下雪乃ver100/雪ノ下雪乃ver1.00.pmx'
    r.import_model(path)

    r.set_output_path(os.path.join(os.getcwd(), 'base.png'))
    r.render()

    # r.change_shapekey('あ', 1.0)
    # r.set_output_path(os.path.join(os.getcwd(), 'a_1.png'))
    r.render()
