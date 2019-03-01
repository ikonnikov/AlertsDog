# -*- coding: utf-8 -*-

import os


def load_script(root, name):
    path = os.path.join(root, name)

    with open(path, 'rb') as f:
        return f.read()
