#!/bin/bash

# Fail on error
set -e

# Install Miniconda
curl -sLo miniconda.sh https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash miniconda.sh -b -p $HOME/miniconda
export PATH="$HOME/miniconda/bin:$PATH"

# Create Conda environment
conda create -y -n cad-env python=3.10
source $HOME/miniconda/bin/activate cad-env

# Install CadQuery
conda install -y -c conda-forge cadquery

# Make the environment persist across sessions
echo 'source $HOME/miniconda/bin/activate cad-env' >> $HOME/.bashrc