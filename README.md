# pyiron-apt-playground

This repository shows a demonstration of the APT analysis tools [paraprobe-toolbox](https://gitlab.com/paraprobe/paraprobe-toolbox) and [compositionspace](https://github.com/eisenforschung/CompositionSpace) along with pyiron.

The easiest way to use this repository is launch it through mybinder:

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/srmnitc/pyiron-paraprobe-playground/HEAD)

To set it up locally, you need [conda](https://docs.conda.io/en/latest/) installed. It is recommended to first install [mamba](https://mamba.readthedocs.io/en/latest/):

```
conda install mamba
```

The rest of the commands can be run either with `conda` or `mamba`. First clone this repository.

```
git clone https://github.com/srmnitc/pyiron-apt.git
```

Create an environment using the provided environment file. For more conda commands, see [here](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html).

```
cd pyiron-apt
mamba env create -f binder/environment.yml
```

Then activate the environment,

```
conda activate apt
```

Do the pre-setup for pyiron

```
mv binder/.pyiron ~/
mkdir ~/pyiron
cp -rf binder/pyiron/resources ~/pyiron/
```

You might need do `chmod u+x filename` for the files in the `pyiron/resources/paraprobe-ranger/bin` folder.

We are ready to run the code now.

Start a jupyter instance by,

```
jupyter lab
```




