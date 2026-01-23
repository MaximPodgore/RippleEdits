# Evaluating the Ripple Effects of Knowledge Editing in RAG systems

This repository contains code from the paper: ["Evaluating the Ripple Effects of Knowledge Editing in Language Models"](https://arxiv.org/abs/2307.12976), which has now been extended to allow for benchmarking of RAG systems

## Running locally

To clone the repository and set up the environment, please run the following commands:
```shell
git clone https://github.com/edenbiran/RippleEdits.git
cd RippleEdits
conda create -n "rippleBenchmark" python==3.9
conda activate rippleBenchmark
pip install -r requirements.txt
pip install torch==2.0.1+cu118 -f https://download.pytorch.org/whl/torch_stable.html
```
Then use `src/setup.py` to init a db in graph_raph, load the data, check that it's done loading, and also do some tests on whether it actually worked.

After that, just run `src/main.py`


## Citation
```
@article{cohen2024evaluating,
  title={Evaluating the ripple effects of knowledge editing in language models},
  author={Cohen, Roi and Biran, Eden and Yoran, Ori and Globerson, Amir and Geva, Mor},
  journal={Transactions of the Association for Computational Linguistics},
  volume={12},
  pages={283--298},
  year={2024},
  publisher={MIT Press One Broadway, 12th Floor, Cambridge, Massachusetts 02142, USA~…}
}
```
