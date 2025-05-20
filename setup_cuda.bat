@echo off
conda create -n bumbot_cuda python=3.12 -y
conda activate bumbot_cuda
conda install pytorch torchvision torchaudio pytorch-cuda=12.1 -c pytorch -c nvidia -y
pip install -r requirements.txt
