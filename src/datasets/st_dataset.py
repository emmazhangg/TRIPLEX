
from glob import glob
import os

import numpy as np
import pandas as pd
import h5py
import scanpy as sc
import torch
import torchvision.transforms as transforms


class STDataset(torch.utils.data.Dataset):
    """Some Information about baselines"""
    def __init__(self):
        super(STDataset, self).__init__()
        
        self.train_transforms = transforms.Compose([
            transforms.ToPILImage(),
            transforms.RandomHorizontalFlip(),
            transforms.RandomVerticalFlip(),
            transforms.RandomApply([transforms.RandomRotation((90, 90))]),
            transforms.ToTensor(),
            transforms.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225))
        ])
        
        self.test_transforms = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225))
        ])

    def load_img(self, name: str, idx: int = None):
        """Load whole slide image of a sample.

        Args:
            name (str): name of a sample

        Returns:
            numpy.array: return whole slide image.
        """
        path = f"{self.img_dir}/{name}.h5"
        
        if idx is not None:
            with h5py.File(path, 'r') as f:
                img = f['img'][idx]
        else:
            with h5py.File(path, 'r') as f:
                img = f['img'][:]
            
        return img
    
    def load_st(self, name: str):
        """Load gene expression data of a sample.

        Args:
            name (str): name of a sample

        Returns:
            annData: return adata of st data. 
        """
        path = f"{self.st_dir}/{name}.h5ad"
        adata = sc.read_h5ad(path)
    
        return adata


class TriDataset(STDataset):
    def __init__(self, 
                mode: str,
                phase: str,
                fold: int,
                data_dir: str,
                ):
        super(TriDataset, self).__init__()
        
        if mode not in ['cv', 'eval', 'inference']:
            raise ValueError(f"mode must be 'cv' or 'eval' or 'inference', but got {mode}")
        
        if phase not in ['train', 'test']:
            raise ValueError(f"phase must be 'train' or 'test', but got {phase}")

        if mode in ['eval', 'inference'] and phase == 'train':
            print(f"mode is {mode} but phase is 'train', so phase is changed to 'test'")
            phase = 'test'
        
        self.img_dir = f"{data_dir}/patches"
        self.st_dir = f"{data_dir}/st"
        self.emb_dir = f"{data_dir}/emb"
    
        self.mode = mode
        self.phase = phase
        
        if mode == 'cv':
            data_path = f"{data_dir}/splits/{phase}_fold{fold}.csv"
            data = pd.read_csv(data_path)
            ids = data['sample_id'].to_list()
                
        elif mode == 'inference':
            ids = os.listdir(f"{self.img_dir}")
            ids = [os.path.splitext(_id)[0] for _id in ids]
            
        self.int2id = dict(enumerate(ids))
        
        if phase == 'train':
            self.adata_dict = {_id: self.load_st(_id) \
                for _id in ids}
            self.pos_dict = {_id: torch.LongTensor(adata.obs[['array_row', 'array_col']].to_numpy()) \
                for _id, adata in self.adata_dict.items()}
            self.global_embs = {_id: self.load_emb(_id, emb_name='global') \
                for _id in ids}
            
            self.lengths = [len(adata) for adata in self.st_dict.values()]
            self.cumlen = np.cumsum(self.lengths)
        
    def __getitem__(self, index):
        data = {}
        
        if self.phase == 'train':
            i = 0
            while index >= self.cumlen[i]:
                i += 1
            idx = index
            if i > 0:
                idx = index - self.cumlen[i-1]

            name = self.int2id[i]
            img = self.load_img(name, idx)
            img = self.train_transforms(img)
            
            neighbor_emb, mask = self.load_emb(name, emb_name='neighbor', idx=idx)
            adata = self.adata_dict[name]
            
            data['img'] = img
            data['mask'] = mask
            data['neighbor_emb'] = neighbor_emb
            data['label'] = adata[idx].X.toarray()
            data['pid'] = torch.LongTensor([index])
            data['sid'] = torch.arange(len(img))
            
        elif self.phase == 'test':
            name = self.int2id[index]
            img = self.load_img(name)
            img = self.test_transforms(img)
            
            global_emb = self.load_emb(name, emb_name='global')
            neighbor_emb, mask = self.load_emb(name, emb_name='neighbor')
            
            if self.mode == 'cv':
                adata = self.load_st(name)
                pos = adata.obs[['array_row', 'array_col']].to_numpy()
                data['label'] = adata.X.toarray()

            elif self.mode == 'inference':
                pos = np.load(f"{self.data_dir}/pos/{name}.npy")
            
            data['img'] = img
            data['mask'] = mask
            data['neighbor_emb'] = neighbor_emb
            data['pos'] = torch.LongTensor(pos)
            data['global_emb'] = global_emb
            
        return data
        
    def __len__(self):
        if self.mode == 'train':
            return self.cumlen[-1]
        else:
            return len(self.int2id)
        
    def load_emb(self, name: str, emb_name: str = 'global', idx: int = None):
        if emb_name not in ['global', 'neighbor']:
            raise ValueError(f"emb_name must be 'global' or 'neighbor', but got {emb_name}")
        
        path = f"{self.emb_dir}/{emb_name}/{name}.h5"
        
        with h5py.File(path, 'r') as f:
            emb = f['embeddings'][idx] if idx is not None else f['embeddings'][:]
            emb = torch.Tensor(emb)
            
            if emb_name == 'neighbor':
                mask = f['mask_tb'][idx] if idx is not None else f['mask_tb'][:]
                mask = torch.LongTensor(mask)
                return emb, mask
            
        return emb
    
