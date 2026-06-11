# Stakeholder-Specific Agora Publication Retriever and Summarizer

N = 2
embedding-model = text-embedding-3-small
chat-model = gpt-4o

## tl;dr
This simple app lets you query in natural language about Agora's N most influential publications. The top related publications can then be summarized specifically to the type of stakeholder the user has selected.

## Workflow
There are five screens appearing in this order:
* Setup: User must provide API key and base URL for an OpenAI-standard endpoint
* Stakeholder type selection: User is asked what stakeholder type they relate the most with: researcher, policy maker, business, interested citizen
* Question: There is a text input with a placeholder: "Ask a question about the energy transition." and example questions like "Will AI data centers accelerate climate change?"
* Results: The most relevant text pieces are shown in a list with a relevancy score. There is the title of the PDF, the page number, a text snippet and a "Summarize this for me!" button in each item. Top 5 results are shown.
* Summary: After the user has clicked one of the summarization buttons, a summary pops up which is tailored to the type of stakeholder the user has selected earlier. For summarization, include the 2 chunks before and 2 chunks after the selected chunk (from the same PDF) as context for summarization.

The latter four screens all have a "Back" button which resets the state to the step before and lets the user navigate freely. Also the retrieval results are cleared when going back.

## Data
Use perplexity to list the N most influential publications of Agora Energiewende in English. The original data is saved in ./original-publications. 

## Requirements
1. The app should be usable frontend-only, i.e., no backend dependencies. One exception is the use of AI endpoints.

## Architecture
We want to provide the data statically.

Because of requirement 1., we want a single HTML file index.html with all the data already included. This should be fine for an MVP with N publications.

There is a preprocessing.py script which directly manipulates the index.html. 

## Preprocessing
The script preprocessing.py will chunk all available PDFs in ./original-publications considering only text, vectorize them using the embedding model defined above, and store them with proper metadata in the index.html.

### Chunking strategy
For now, we use a fixed-size approach, i.e, 200 tokens with 30 tokens overlap. Smaller chunks improve retrieval precision for sparse keyword mentions.

### How to run it
Create a venv: `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`

And run the script: `source .venv/bin/activate && set -a && source .env && set +a && python preprocessing.py`

## App
The static site index.html will show one of the aforementioned screens depending on the internal state: 

{ apiKey, baseURL, stakeholder, query, publications[] }

The user query will be embedded with embedding-model too. We can assume that the user's provided base URL has it. The similarity search between the preprocessed vectors and the use query will be done directly with cosine similarity.

Summarization is done using chat-model which is hard-coded.

## Next steps
* Proper database -> more data, injest data dynamically
* Go beyond text-only chunking
* Section-based chunking strategy