import os
import sys
import time
import shutil
import zipfile
from pathlib import Path
import subprocess
import platform
from tqdm import tqdm

import numpy as np
import nibabel as nib

from totalsegmentator.libs import get_config_dir
import dicom2nifti
import dicom2nifti.settings as settings

def convert_dicom_to_nifti(dicom_dir:str, output_path:str):
    settings.disable_validate_slicecount()
    settings.disable_validate_slice_increment()
    settings.disable_validate_orientation()
    settings.disable_validate_orthogonal()

    dicom2nifti.dicom_series_to_nifti(
                dicom_dir,
                output_path,
                reorient_nifti=True,
            )

def command_exists(command):
    return shutil.which(command) is not None


def download_dcm2niix():
    import urllib.request
    print("  Downloading dcm2niix...")

    if platform.system() == "Windows":
        url = "https://github.com/rordenlab/dcm2niix/releases/latest/download/dcm2niix_win.zip"
    elif platform.system() == "Darwin":  # Mac
        raise ValueError("For MacOS automatic installation of dcm2niix not possible. Install it manually.")
        # Problem: not zip files
        # if platform.machine().startswith("arm") or platform.machine().startswith("aarch"):  # arm
        #     url = "https://github.com/rordenlab/dcm2niix/releases/latest/download/macos_dcm2niix.pkg"
        # else:  # intel
        #     # unclear if this is the right link (is the same as for arm)
        #     url = "https://github.com/rordenlab/dcm2niix/releases/latest/download/macos_dcm2niix.pkg"
    elif platform.system() == "Linux":
        url = "https://github.com/rordenlab/dcm2niix/releases/latest/download/dcm2niix_lnx.zip"
    else:
        raise ValueError("Unknown operating system. Can not download the right version of dcm2niix.")

    config_dir = get_config_dir()

    urllib.request.urlretrieve(url, config_dir / "dcm2niix.zip")
    with zipfile.ZipFile(config_dir / "dcm2niix.zip", 'r') as zip_ref:
        zip_ref.extractall(config_dir)

    # Give execution permission to the script
    os.chmod(config_dir / "dcm2niix", 0o755)

    # Clean up
    os.remove(config_dir / "dcm2niix.zip")
    os.remove(config_dir / "dcm2niibatch")


def dcm_to_nifti(input_path:str, output_path:str, verbose=False):
    """
    input_path: a directory of dicom slices
    output_path: a nifti file path
    """
    convert_dicom_to_nifti(input_path, output_path)


def save_mask_as_rtstruct(img_data, selected_classes, dcm_reference_file, output_path):
    """
    dcm_reference_file: a directory with dcm slices ??
    """
    from rt_utils import RTStructBuilder
    import logging
    logging.basicConfig(level=logging.WARNING)  # avoid messages from rt_utils

    # create new RT Struct - requires original DICOM
    rtstruct = RTStructBuilder.create_new(dicom_series_path=dcm_reference_file)

    # add mask to RT Struct
    for class_idx, class_name in tqdm(selected_classes.items()):
        binary_img = img_data == class_idx
        if binary_img.sum() > 0:  # only save none-empty images
            # add segmentation to RT Struct
            rtstruct.add_roi(
                mask=binary_img,  # has to be a binary numpy array
                name=class_name
            )

    rtstruct.save(str(output_path))
