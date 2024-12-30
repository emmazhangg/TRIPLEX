# TRIPLEX 🧬

TRIPLEX is a deep learning framework designed for predicting spatial transcriptomics from histology images by integrating multi-resolution features. 

[![PyTorch](https://img.shields.io/badge/PyTorch-ee4c2c?logo=pytorch&logoColor=white)](https://pytorch.org/)
[![PyTorch Lightning](https://img.shields.io/badge/pytorch-lightning-blue.svg?logo=PyTorch%20Lightning)](https://lightning.ai/docs/pytorch/stable/)

<img src="./figures/TRIPLEX_main.jpg" title="TRIPLEX"/>

It is now integrated with [HEST](https://github.com/mahmoodlab/HEST) and [CLAM](https://github.com/mahmoodlab/CLAM) for data preparation.

## Table of Contents
- [Requirements](#requirements)
- [Installation](#installation)
- [Project Structure](#project-structure)
- [Usage](#usage)
  - [Preprocessing](#preprocessing)
  - [Training](#training)
  - [Evaluation](#evaluation)
  - [Inference](#inference)
- [Configuration](#configuration)
- [Citation](#Citation)

---

## Requirements

- Python 3.10+
- PyTorch 2.0+
- PyTorch Lightning 2.0+
- CUDA-enabled GPU (recommended)

TRIPLEX is tested on Python 3.11, PyTorch 2.4.1, PyTorch Lightning 2.4.0, and CUDA 12.1.

---

## Installation

Clone this repository:

```bash
git clone https://github.com/NEXGEM/TRIPLEX.git
cd triplex
```

Create a conda environment:

```bash
conda create -n TRIPLEX python=3.11
```

Install Pytorch 

```bash
pip install torch==2.4.1 torchvision==0.19.1 --index-url https://download.pytorch.org/whl/cu121
```

Install HEST

- Dependencies (CUDA-related Python packages)

```bash
pip install \
    --extra-index-url=https://pypi.nvidia.com \
    cudf-cu12==24.6.0 \
    dask-cudf-cu12==24.6.0 \
    cucim-cu12==24.6.0 \
    raft-dask-cu12==24.6.0
```

- HEST

```bash
git clone https://github.com/mahmoodlab/HEST.git 
cd HEST 
pip install -e .
```

Instann FlashAttention

```bash
pip install flash-attn --no-build-isolation
```

Install remaining dependencies:

```bash
pip install -r requirements.txt
```

---

## Project Structure

```
.
├── config/                 # Configuration files for experiments
├── docker/                 # Docker-related setup files
├── figures/                # Figures
├── src/                    # Source code
│   ├── dataset/            # Dataset loading and preprocessing modules
│   ├── model/              # Model architectures
│   ├── preprocess/         # Codes for preprocessing data
│   ├── experiment/         # Codes for organizing experiment results
│   ├── main.py             # Main script for training, evaluation, and inference
│   ├── utils.py            # Utility functions
├── script/                 # Example scripts for runs 
├── README.md               # Project documentation
├── requirements.txt        # Python dependencies
```

---

## Usage

### Preprocessing

Before training or inference, raw data must be preprocessed. Modify the paths in the respective shell scripts and run them:

#### **Create patches from WSI (Only for inference)**
```bash
python src/preprocess/CLAM/create_patches_fp.py \
        --source $RAW_DIR \
        --save_dir $PROCESSED_DIR \
        --patch_size 256 \
        --seg \
        --patch \
        --stitch \
        --patch_level $PATCH_LEVEL 
```

#### **Prepare patches and st data**
For training:
- HEST
```bash
python src/preprocess/prepare_data.py --input_dir $RAW_DIR \
                                --output_dir $PROCESSED_DIR \
                                --mode hest
```

- New data
```bash
python src/preprocess/prepare_data.py --input_dir $RAW_DIR \
                                --output_dir $PROCESSED_DIR \
                                --mode train
```

For inference:
```bash
python src/preprocess/prepare_data.py --input_dir $RAW_DIR \
                                --output_dir $PROCESSED_DIR \
                                --mode inference \
                                --patch_size 256 \
                                --slide_level 0 \
                                --slide_ext $EXTENSION
```

#### **Get geneset for training (no need for hest benchmark)**
```bash
python src/preprocess/get_geneset.py --st_dir $PROCESSED_DIR'/adata' \
                                    --output_dir $PROCESSED_DIR
```

#### **Extract image features using foundation model (UNI)**
Gloabl features:
- training
```bash
### Global features
python src/preprocess/extract_img_features.py  \
        --patch_dataroot $PROCESSED_DIR'/patches' \
        --embed_dataroot $PROCESSED_DIR'/emb/global' \
        --num_n 1 \
        --use_openslide
```

- inference
```bash
### Global features
python src/preprocess/extract_img_features.py  \
        --wsi_dataroot $RAW_DIR \
        --patch_dataroot $PROCESSED_DIR'/patches' \
        --embed_dataroot $PROCESSED_DIR'/emb/global' \
        --slide_ext $EXTENSION \
        --num_n 1 \
        --use_openslide 
```

Neighbor features:
```bash
### Global features
python src/preprocess/extract_img_features.py  \
        --wsi_dataroot $RAW_DIR \
        --patch_dataroot $PROCESSED_DIR'/patches' \
        --embed_dataroot $PROCESSED_DIR'/emb/neighbor' \
        --slide_ext $EXTENSION \
        --use_openslide \
        --num_n 5
```

> Examples

- HEST bench data
```bash
bash script/01-preprocess_hest_bench.sh /path/to/hest/wsis ./input/bench_data/CCRCC 'tif'
```

- Other HEST data
```bash
bash script/02-preprocess_hest.sh /path/to/hest/wsis ./input/ST/andersson 'tif'
```

- Your own ST data
```bash
bash script/03-preprocess_new.sh /path/to/raw ./input/path/to/processed 'tif' visium
```

- Only images (for inference)
```bash
bash script/04-preprocess_for_inference.sh /path/to/raw ./input/path/to/processed 'svs' 0
```

### 📈 Model Training

To train the model using cross-validation, run the following command:

```bash
python src/main.py --config_name=<config_path> --mode=cv --gpu=1
```

Replace `<config_path>` with the path to your configuration file.

### 📊 Evaluation

To evaluate the model:

```bash
python src/main.py --config_name=<config_path> --mode=eval --gpu=1
```

**The most recent folder inside the log folder is used for evaluation.**

### 🔍 Inference

To run inference:

```bash
python src/main.py --config_name=<config_path> --mode=inference --gpu=1 --model_path=<model_checkpoint_path>
```

Replace `<model_checkpoint_path>` with the path to your trained model checkpoint.

---

## Configuration

Configurations are managed using YAML files located in the `config/` directory. Each configuration file specifies parameters for the dataset, model, training, and evaluation. Example configuration parameters include:

```yaml



GENERAL:
  seed: 2021
  log_path: ./logs
  
TRAINING:
  num_k: 5
  learning_rate: 1.0e-4
  num_epochs: 200
  monitor: PearsonCorrCoef
  mode: max
  early_stopping:
    patience: 10
  lr_scheduler:
    patience: 5
    factor: 0.1
  
MODEL:
  model_name: TRIPLEX 
  num_outputs: 250
  emb_dim: 1024
  depth1: 2
  depth2: 2
  depth3: 4
  num_heads1: 8
  num_heads2: 16
  num_heads3: 16
  mlp_ratio1: 2
  mlp_ratio2: 2
  mlp_ratio3: 2
  dropout1: 0.15
  dropout1: 0.15
  dropout1: 0.15
  kernel_size: 3

DATA:
  data_dir: input/ST/andersson
  output_dir: output/ST/andersson
  dataset_name: TriDataset
  gene_type: 'mean'
  num_genes: 1000
  num_outputs: 250
  cpm: True
  smooth: True
  
  train_dataloader:
        batch_size: 128
        num_workers: 4
        pin_memory: False
        shuffle: True

  test_dataloader:
      batch_size: 1
      num_workers: 4
      pin_memory: False
      shuffle: False
```

Modify these files as needed for your experiments.

---

## Citation

```
@inproceedings{chung2024accurate,
  title={Accurate Spatial Gene Expression Prediction by integrating Multi-resolution features},
  author={Chung, Youngmin and Ha, Ji Hun and Im, Kyeong Chan and Lee, Joo Sang},
  booktitle={Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition},
  pages={11591--11600},
  year={2024}
}
```

---



