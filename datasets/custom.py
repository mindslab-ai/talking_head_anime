import os
import random
import subprocess
import time

import cv2
import torch

from datasets.base import BaseDataset


class SubprocessDataset(BaseDataset):
    def __init__(self, conf):
        super(SubprocessDataset, self).__init__(conf)
        with open(self.conf.path['metadata'], 'r', encoding='utf-8') as f:
            valid_models = f.readlines()

        self.data = [os.path.join(self.conf.path['root'], line.strip()) for line in valid_models]

    def __len__(self):
        return len(self.data)

    @staticmethod
    def np_img_to_torch(img):
        return torch.from_numpy(img).permute((2, 0, 1)) / 255.

    def __getitem__(self, idx):
        return_data = {}

        key_mouth = 'あ'
        val_mouth = random.random()
        val_mouth = float(f'{val_mouth:.04f}')

        key_left_eye = 'ウィンク'
        val_left_eye = random.random()
        val_left_eye = float(f'{val_left_eye:.04f}')

        key_right_eye = 'ウィンク右'
        val_right_eye = random.random()
        val_right_eye = float(f'{val_right_eye:.04f}')

        return_data['pose'] = torch.FloatTensor([val_mouth, val_left_eye, val_right_eye])

        commands = [
            'python', '-m', 'datasets.script2',
            f'{self.conf.path["metadata"]}', f'{idx}',
            f'{key_mouth}___{val_mouth}',
            f'{key_left_eye}___{val_left_eye}',
            f'{key_right_eye}___{val_right_eye}',
        ]
        command = ' '.join(commands)
        subprocess.call(command, shell=True, stdout=open(os.devnull, 'wb'))

        tmp_dir = self.conf.path['tmp']

        tmp_path = os.path.join(tmp_dir, f'{idx}_{val_mouth}_{val_left_eye}_{val_right_eye}.png')
        while not os.path.exists(tmp_path):
            time.sleep(0.5)
            print('waiting', tmp_path)
        img_target = cv2.imread(tmp_path, cv2.IMREAD_UNCHANGED)
        os.remove(tmp_path)
        return_data['img_target'] = self.np_img_to_torch(img_target)

        tmp_path = os.path.join(tmp_dir, f'{idx}.png')
        img_base_np = cv2.imread(tmp_path, cv2.IMREAD_UNCHANGED)
        return_data['img_base'] = self.np_img_to_torch(img_base_np)

        return return_data


class PlaceholderDataset(BaseDataset):
    def __init__(self, conf):
        super(PlaceholderDataset, self).__init__(conf)

    def __len__(self):
        return 10000

    def getitem(self, idx):
        return_data = {}

        return_data['img_base'] = torch.randn((4, 256, 256))
        return_data['img_target'] = torch.randn((4, 256, 256))
        return_data['pose'] = torch.Tensor([random.random(), random.random(), random.random()])

        return return_data


if __name__ == '__main__':
    from omegaconf import OmegaConf
    from torch.utils.data import DataLoader
    from utils.util import cycle

    import sys

    code_root = '/root/talking_head_anime'
    os.chdir(code_root)
    sys.path.append(os.getcwd())

    conf = OmegaConf.load('configs/datasets/custom.yaml')
    d = SubprocessDataset(conf)
    loader = DataLoader(d, batch_size=4, num_workers=4)
    it = cycle(loader)

    from tqdm import trange

    for i in trange(20):
        item = next(it)
