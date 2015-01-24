import functools

import numpy as np

from pylearn2.models.autoencoder import DenoisingAutoencoder
from pylearn2.models.model import Model
from pylearn2.linear.matrixmul import MatrixMul


class SparseRFAutoencoder(DenoisingAutoencoder):
    """
    A denoising autoencoder with sparse local receptive fields.
    """

    def __init__(self, nhid, numCons, sigma, imageSize, **kwargs):
        """
        Parameters:
        ----------

        nhid: number of hidden units

        numCons: number of connections per hidden unit

        sigma: standard deviation matrix

        imageSize = size of an image

        """
        super(SparseRFAutoencoder, self).__init__(nhid=nhid, **kwargs)
        self.numCons = numCons
        self.sigma = sigma
        self.imageSize = imageSize

        self._set_hidden_unit_locations()
        self.mask = self._create_connection_mask()

    def __str__(self):
        props_to_print = dict([(prop_name, getattr(self, prop_name))
                                for prop_name in ['nhid', 'numCons', 'sigma']])

        return "%s(%s)" % (self.__class__.__name__, props_to_print)

    def _set_hidden_unit_locations(self):
        self.hiddenUnitLocs = np.round(self.imageSize / 2)

    def _create_connection_mask(self):
        ## Define some useful local variables for sake of clarity ##
        imgHeight = self.imageSize[0]
        imgLength = self.imageSize[1]
        numPixels = imgHeight * imgLength
        numHiddenUnits = self.hiddenUnitLocs.shape[0]

        ## Initialize the Connection Matrix to all zeroes ##
        connectionMatrix = np.zeros(shape=(numHiddenUnits,numPixels))
        currHiddenUnit = 0 # index to keep track of which hidden unit we're working on.

        ## Create a variance parameter by squaring each element in sigma, used in Gaussian ##
        variance = [[elem * elem for elem in inner] for inner in self.sigma]

        ## Loop through the Hidden Units to Create Samples ##
        for k in self.hiddenUnitLocs:

            i = 0
            while i < self.numCons:

                # Get random Gaussian sample which returns an array of tuples
                [[x, y]] = np.random.multivariate_normal(k, variance, 1)

                # Round the sample to nearest integer
                x = round(x, 0)
                y = round(y, 0)

                # Check to see if it's out of bounds.
                if (x >= imgLength) or (y >= imgHeight) or (x < 0) or (y < 0):
                    continue

                # Calculate which pixel number it is to add to the map.
                pixelLoc = (y) * imgLength + (x)

                if (connectionMatrix[currHiddenUnit][pixelLoc] == 1):
                    continue

                connectionMatrix[currHiddenUnit][pixelLoc] = 1
                i += 1

            currHiddenUnit += 1

        return connectionMatrix

    @functools.wraps(Model._modify_updates)
    def _modify_updates(self, updates):
        W = self.weights
        if W in updates:
            updates[W] = updates[W] * self.mask


if __name__ == "__main__":
    import dataset
    dataset.create_datasets()

    from pylearn2.scripts.train import train
    train(config="custom.yaml")
