# Agora Publication Explorer

## Parameters
* *N* = 2
* *embedding-model* = text-embedding-3-small
* *chat-model* = gpt-4o

## tl;dr
This app is meant to make Agora's publications more accessible. It works in a two-step manner. First, it lets you query in natural language about Agora's *N* most influential publications to retrieve related text parts. Then, the top related parts can be summarized specifically to the type of stakeholder the user has selected upfront.

## For the reviewers
The app is a single file by design. To run the app, checkout the repository and double click the index.html. This should open the app in the browser. The first screen will ask you for credentials. Use the ones you have send me via email. Now follow the guidance in the app. There is also a running deployment on https://bernie-dev.de/agora

### Assignment question
1. **How would you expand this MVP into a real product?** - The Agora Publication Explorer could be a tool offered publically on the Agora webpage accessible to the different types of stakeholders. It could be advertised and can be expected to get traffic as easy-to-use tools are a great way to pave the road for interested people. On the technical side, many things like data management, proper app framework, CI/CD, testing, security etc. have to be addressed first. 
2. **What risks do you see, and how would you address them?** - Especially the RAG part has to be tuned to give better results. If a product is half-baked, it might cause more harm than benefit. The could also be addressed systematically using metrics to judge the RAG's precision. Also, as AI-based parts are stochastic, you can never be 100% certain that all information is retrieved and processed correctly. I must always be stated that AI tools are meant to be helpers and don't replace your own way of researching. AI backend cost are another topic one has to think about.
3. **Who are the key stakeholders you'd want to involve in building this out?** - Collecting data on how the different stakeholders found the tool to be useful is a great way to improve it. From Agora's side, people who are actively writing publications probably have the most valuable opinion - across topics. Feedback from policy makers, businesses, and interested citizen could perhaps be retrieved through a public announcement, for example, via Linkedin.

## Workflow
There are five screens appearing in this order:
* Setup: User must provide API key and base URL for an OpenAI-standard endpoint
* Stakeholder type selection: User is asked what stakeholder type they relate the most with: researcher, policy maker, business, interested citizen
* Question: There is a text input with a placeholder: "Ask a question about the energy transition." and example questions like "Does the Energiewende have an impact on the job structure of the energy sector?"
* Results: The most relevant text pieces are shown in a list with a relevancy score. There is the title of the PDF, the page number, a text snippet and a "Summarize this for me!" button in each item. Top 5 results are shown. Are relevance score is shown per item: >70%: relevant, <70% and >50%: tangentially relevant, <50% not relevant
* Summary: After the user has clicked one of the summarization buttons, a summary pops up which is tailored to the type of stakeholder the user has selected earlier. For summarization, include the 2 chunks before and 2 chunks after the selected chunk (from the same PDF) as context for summarization.

The latter four screens all have a "Back" button which resets the state to the step before and lets the user navigate freely. Also the retrieval results are cleared when going back.

## Data
I asked perplexity to list the *N* most influential publications of Agora Energiewende in English. The original data is saved in ./original-publications. As these publication are already quite long, I decided to leave it at this for the MVP.

## Requirements
The app should be usable frontend-only, i.e., no backend dependencies. One exception is the use of AI endpoints.

## Architecture
We want to provide the data statically.

Because of requirement 1., we want a single HTML file index.html with all the data already included. This should be fine for an MVP with *N* publications.

There is a preprocessing.py script which directly manipulates the index.html. 

## Preprocessing
Run this part only if you want to vectorize new data or change the chunking strategy! The script preprocessing.py will chunk all available PDFs in ./original-publications considering only text, vectorize them using the embedding model defined above, and store them with proper metadata in the index.html. It modifies the index.html!

### Chunking strategy
For now, we use a fixed-size approach, i.e, 200 tokens with 30 tokens overlap. Smaller chunks improve retrieval precision for sparse keyword mentions. Larger chunks add more context.

### How to run it
Create a venv: `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`

And run the script: `source .venv/bin/activate && set -a && source .env && set +a && python preprocessing.py`

## App
The static site index.html will show one of the aforementioned screens depending on the internal state: 

{ apiKey, baseURL, stakeholder, query, publications[] }

The user query will be embedded with *embedding-model* too. We can assume that the user's provided base URL has it. The similarity search between the preprocessed vectors and the use query will be done directly with cosine similarity.

Summarization is done using *chat-model* which is hard-coded.

## Next steps
* Proper database -> more data, injest data dynamically
* Go beyond text-only chunking
* Section-based chunking strategy