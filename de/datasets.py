import array
import glob
import os

import numpy as np
from pylearn2.datasets import dense_design_matrix
from pylearn2.utils import serial, string_utils


def read_iml(filename, width, height, dtype='uint16'):
    """Reads an IML file and returns as an ndarray."""

    with open(filename, 'rb') as handle:
        s = handle.read()
    arr = array.array('H', s)
    arr.byteswap()

    if width and height:
        arr = np.array(arr, dtype=dtype).reshape(height, width)

    return arr


def get_patch(img, patch_size=(32, 32), width_slice=None, height_slice=None):
    width = img.shape[1]
    height = img.shape[0]
    left_margin = (width-patch_size[1])/2
    top_margin = (height-patch_size[0])/2
    img_patch = img[top_margin: top_margin+patch_size[0],
                    left_margin:left_margin+patch_size[1]].flatten(1)
    return img_patch.reshape(patch_size)


class ImageDataset(dense_design_matrix.DenseDesignMatrix):
    """
    """
    ALL_DATASETS = ['train', 'test', 'valid']
    ALL_LOADERS = {
        '.iml': read_iml, }

    @classmethod
    def get_image_files(cls, img_dir, filter_fn=lambda *arg: True):
        images = []
        image_loaders = []
        for image_filepath in glob.glob(os.path.join(img_dir, '*.*')):
            _, ext = os.path.splitext(image_filepath)
            if ext in list(cls.ALL_LOADERS.keys()) and filter_fn(image_filepath):
                images.append(image_filepath)
                image_loaders.append(cls.ALL_LOADERS[ext])
        return images, image_loaders

    def __init__(self, which_set, width, height, axes=('b', 0, 1, 'c'),
                 patch_size=(32, 32), img_dir=None, ntrain=200,
                 ntest=25, nvalid=25):

        assert which_set in self.ALL_DATASETS, \
            "Set specified is not a valid set. Please use 'train' or " \
            "'test' or 'valid'"

        # We define here:
        self.img_shape = patch_size
        self.img_size = np.prod(patch_size)
        self.img_dir = img_dir

        # Get files
        nimages = ntrain + ntest + nvalid
        images, image_loaders = self.__class__.get_image_files(self.img_dir)
        if len(images) < nimages:
            # Note: could download using requests via
            # http://cin-11.medizin.uni-tuebingen.de:61280/vanhateren/iml/
            raise Exception("%d images needed for dataset; %d found in %s" % (
                nimages,
                len(images),
                self.img_dir))

        if which_set == 'train':
            img_indices = np.arange(ntrain)
        elif which_set == 'test':
            img_indices = ntrain + np.arange(0, ntest)
        elif which_set == 'valid':
            img_indices = ntrain + ntest + np.arange(0, nvalid)

        X = np.empty((len(img_indices), self.img_size))

        # Take 250 images, convert to 32x32, store in X
        for ii, img_idx in enumerate(img_indices):
            if ii > 0 and ii % 10 == 0:
                print '%d of %d' % (ii + 1, len(img_indices))
            image_file = images[img_idx]
            img = image_loaders[img_idx](image_file, width=width, height=height)
            img_patch = get_patch(img, patch_size=patch_size)
            X[ii, :] = img_patch.flatten(1)

        # Post-processing
        self.subtracted_mean = X.mean(axis=0)
        X = X - self.subtracted_mean
        self.max_val = np.abs(X).max(axis=0)
        X = X / self.max_val

        view_converter = dense_design_matrix.DefaultViewConverter(
            patch_size + (1,),
            axes)

        super(VanHateren, self).__init__(
            X=X,
            view_converter=view_converter,
            axes=axes)

    def normalize_image(self, image_data):
        return (image_data - self.subtracted_mean) / self.max_val

    def denormalize_image(self, image_data):
        return (image_data * self.max_val) + self.subtracted_mean



class VanHateren(ImageDataset):

    DATA_DIR = string_utils.preprocess('${PYLEARN2_DATA_PATH}/vanhateren')
    VH_WIDTH = 1536
    VH_HEIGHT = 1024

    def __init__(self, **kwargs):
        super(VanHateren, self).__init__(
            width=self.VH_WIDTH,
            height=self.VH_HEIGHT,
            **kwargs)

    @classmethod
    def create_datasets(cls, datasets=None, overwrite=False,
                        img_dir=DATA_DIR, output_dir=DATA_DIR):
        """Creates the requested datasets, and writes them to disk.
        """
        datasets = datasets or cls.ALL_DATASETS
        serial.mkdir(output_dir)

        for dataset_name in list(datasets):
            file_path_fn = lambda ext: os.path.join(
                output_dir,
                '%s.%s' % (dataset_name, ext))

            output_files = dict([(ext, file_path_fn(ext))
                                 for ext in ['pkl', 'npy']])
            files_missing = np.any([not os.path.isfile(f)
                                    for f in output_files.values()])

            if overwrite or np.any(files_missing):
                print("Loading the %s data" % dataset_name)
                dataset = cls(which_set=dataset_name, img_dir=img_dir)

                print("Saving the %s data" % dataset_name)
                dataset.use_design_loc(output_files['npy'])
                serial.save(output_files['pkl'], dataset)


##class DEDataset(dense_design_matrix.DenseDesignMatrix):
    """
    X: encoded values of some image set.
    Y: classification values.

    Contains a SparseRFAutoencoder object, which it trains on
    the VanHateren dataset.
    """
"""
    def __init__(self, which_set, encoder, image_dataset
                 axes=('b', 0, 1, 'c'),
                 patch_size=(32, 32), img_dir=None, ntrain=200,
                 ntest=25, nvalid=25):
        self.encoder = encoder
        X = encoder.encode(image_dataset)
        Y = np.ones((X.shape[0],))
        super(VanHateren, self).__init__(X=X, Y=Y, **kwargs)
"""
if __name__ == "__main__":
    VanHateren.create_datasets(overwrite=True)
