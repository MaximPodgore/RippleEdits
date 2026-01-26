# Evaluating the Ripple Effects of Knowledge Editing in RAG systems

This repository contains code from the paper: ["Evaluating the Ripple Effects of Knowledge Editing in Language Models"](https://arxiv.org/abs/2307.12976), which has now been extended to allow for benchmarking of RAG systems

## Change Notes

Previously, the benchmarker used id's instead of labels for feeding data and answering questions. I think that's nonoptimal, so I changed the incoming data and modified the system to convert id's to labels when asking the test questions.

I added an SNET query executor and model editor. I updated the get_label function since the wikidata package's function stopped working.

Aside from that, I just added a `main.py` and `setup.ipynb` so that running the benchmarker for SNET's GraphRAG is easy.

## Running locally

Clone the repo and then run the following commands:
```shell
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
