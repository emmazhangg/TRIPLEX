# RAW_DIR=/path/to/raw/dir
# PROCESSED_DIR=/path/to/result/dir

# RAW_DIR=/home/shared/spRNAseq/visium/inhouse/SMC/NSCLC
# PROCESSED_DIR=input/smc/lung

RAW_DIR=/home/shared/spRNAseq/hest_data/wsis
PROCESSED_DIR=$1

# Preprocess ST data for training

# ## Prepare patches and st data
# python src/preprocess/prepare_data.py --input_dir $RAW_DIR \
#                                 --output_dir $PROCESSED_DIR \
#                                 --mode train

# ## Prepare geneset for training
# python src/preprocess/get_geneset.py --st_dir $PROCESSED_DIR'/adata' --output_dir $PROCESSED_DIR

# ## Prepare geneset for training
# python src/preprocess/split_data.py --input_dir $PROCESSED_DIR

## Extract features for TRIPLEX
### Global features
python src/preprocess/extract_img_features.py  \
        --patch_dataroot $PROCESSED_DIR'/patches' \
        --embed_dataroot $PROCESSED_DIR'/emb/global' \
        --num_n 1

### Neighbor features
EXTENSION='.tif'
python src/preprocess/extract_img_features.py \
        --wsi_dataroot $RAW_DIR \
        --patch_dataroot $PROCESSED_DIR'/patches' \
        --embed_dataroot $PROCESSED_DIR'/emb/neighbor' \
        --slide_ext $EXTENSION \
        --num_n 5
