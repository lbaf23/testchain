import torch
import os


def init_cuda():
    try:
        torch.cuda.empty_cache()
        os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb:1024"
    except Exception:
        print('cuda emtpy cache failed.', flush=True)
