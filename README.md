# Tech Stack Recommender

A Content-Based Filtering recommendation engine built with FastAPI, Python, numpy, and pandas. It uses TF-IDF and Cosine Similarity to map raw user skills and interests to professional tech stacks and roles, featuring a modern web interface to guide users through their "cold start" phase.

## Installation

Ensure you have Python 3.10+ and Poetry installed.

```bash
poetry install
```

## Running the App

```bash
poetry run uvicorn app.main:app --reload
```
