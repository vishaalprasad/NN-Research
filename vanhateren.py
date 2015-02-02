import array
import glob
import os

import numpy as np
from pylearn2.datasets import cache, dense_design_matrix
from pylearn2.expr.preprocessing import global_contrast_normalize
from pylearn2.utils import contains_nan
from pylearn2.utils import serial
from pylearn2.utils import string_utils
from theano.compat.six.moves import xrange


class VANHATEREN(dense_design_matrix.DenseDesignMatrix):

    def __init__(self, which_set, axes=('b', 0, 1, 'c'), img_shape=[32, 32], img_dir=None,
                 ntrain=200, ntest=50, nvalid=0):
        # note: there is no such thing as the cifar10 validation set;
        # pylearn1 defined one but really it should be user-configurable
        #(as it is here)
        self.axes = axes
        self.img_shape = img_shape
        self.img_dir = img_dir or os.getcwd()

        #we define here:
        dtype = 'uint16'
        self.img_size = np.prod(self.img_shape)

        #Get files
        nimages = ntrain + ntest + nvalid
        images = glob.glob(os.path.join(self.img_dir, '*.iml'))
        if len(images) < nimages:
            raise Exception("%d images needed for dataset; %d found in %s" % (
                nimages, 
                len(images),
                self.img_dir))

        trainX = np.empty(shape=(ntrain, self.img_size))
        testX = np.empty(shape=(ntest, self.img_size))
        validX = np.empty(shape=(nvalid, self.img_size))

        i = 0
        #take 250 images, convert to 32x32, store in X
        for ii, image in enumerate(images):
            with open(image, 'rb') as handle:
                s = handle.read()
            arr = array.array('H', s)
            arr.byteswap()

            width = 1536
            height = 1024
            if len(arr) != width * height:
                import pdb; pdb.set_trace()

            img = np.array(arr, dtype=dtype).reshape(height, width)
            left_margin = (width-32)/2
            top_margin = (height-32)/2

            img_patch = img[top_margin: top_margin+32, left_margin:left_margin+32].flatten()
            if ii < ntrain:
                trainX[ii] = img_patch
            elif ii < (ntrain + ntest):
                testX[ii-ntrain] = img_patch
            else:
                validX[ii-ntrain-ntest] = img_patch

        # Post-processing
        img_max = np.max([trainX.max(), testX.max(), validX.max()])
        trainX = trainX / float(img_max)
        testX = testX / float(img_max)
        validX = validX / float(img_max)

        view_converter = dense_design_matrix.DefaultViewConverter((32, 32, 1), axes)
        if which_set == 'train':
            super(VANHATEREN, self).__init__(X=trainX,view_converter = view_converter, axes = axes)
        elif which_set == 'test': 
            super(VANHATEREN, self).__init__(X=testX, view_converter = view_converter, axes = axes)
        elif which_set == 'valid':
            super(VANHATEREN, self).__init__(X=validX, view_converter = view_converter, axes = axes)