<div align="center">

# 🎧 SongCLIP

**A CLIP-style dual-encoder that learns "what song comes next" from listening sequences**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0%2B-EE4C2C?style=flat-square&logo=pytorch&logoColor=white)](https://pytorch.org/)
[![Dataset](https://img.shields.io/badge/Dataset-FMA-1DB954?style=flat-square&logo=googleplay&logoColor=white)](https://github.com/mdeff/fma)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](#-license)

*Contrastive learning, borrowed from CLIP, applied to music sequences instead of images and text.*

</div>

---



## 🌟 Overview

SongCLIP learns to predict **what song comes next** in a listening session by embedding both the listening *sequence* and each *candidate song* into a shared vector space — the same contrastive idea behind OpenAI's CLIP, just swapping (image, text) for (sequence, song).

> **Why this instead of a normal recommender?** Contrastive dual-encoders scale well: once trained, recommending is just a nearest-neighbor search in embedding space against however many candidate songs you have — no need to score every song individually.
tive loss.</sub>
</div>
