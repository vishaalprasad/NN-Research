
if __name__ == "__main__":
    import tempfile

    weights_file = 'sparserf_example.pkl'
    params = (10, [[3, 0], [0, 3]], weights_file)

    # Create the dataset
    from de.datasets import VanHateren
    VanHateren.create_datasets()

    # Create the yaml file.
    _, config_fn = tempfile.mkstemp()
    with open("sparserf_template.yaml") as fp:
        # create yaml from templtes + params
        config_yaml = "".join(fp.readlines()) % params
    with open(config_fn, 'w') as config_fp:
        config_fp.write(config_yaml)

    # Train the network
    from pylearn2.scripts.train import train
    train(config=config_fn)

    # Visualize the weights
    from pylearn2.scripts.show_weights import show_weights
    show_weights(model_path=weights_file, border=True)

    # Visualize the reconstruction
    from de.compare_reconstruct import compare_reconstruction
    compare_reconstruction(model_path=weights_file)
