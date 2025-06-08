# Agentic Recommender System

A modular, production-ready, agentic content-based recommender system built with Python. This project demonstrates advanced engineering, agent-based orchestration, and modern NLP for scalable, personalized recommendations. Designed for extensibility and real-world deployment, it integrates with external APIs and supports robust configuration and retraining.


## 🚀 Features

- **Agentic Architecture:** Modular agents for data ingestion, processing, and recommendation.
- **Content-Based Filtering:** Uses NLP models for semantic similarity and personalized recommendations.
- **Google Sheets Integration:** Seamless data ingestion and export with Google Sheets.
- **Similarity Search:** Fast, scalable similarity search utilities.
- **Production-Ready:** Dockerized, environment-managed, and easy to deploy.
- **Model Management:** Supports custom and pre-trained models, with retraining and evaluation workflows.
- **Extensible Utilities:** Easily add new data sources, models, or agents.

---
## Models Used:
- bert-base-uncased for classification
- all-mpnet-base-v2 for embedding generation

## ⚡ Quickstart

### 1. Clone the Repository

```sh
git clone https://github.com/Gurudeep310/agentic-recommender-system.git
cd agentic-recommender-system/mcp-recommender-system-agent/app
```

### 2. Install Dependencies

```sh
uv init.
uv add "mcp[cli]"
uv add -r requirements.txt

pip install -r requirements.txt
```

### 3. Configure Environment

- Add your `local.env` and update credentials (GCP Service Account json, The email for it should have access to Google Sheets) as needed.

### 4. Run the System

This builds the docker and waits for someone to start the container. Once the container is started it streams the logs.
For this project the MCP Client was Cursor or Claude.
```
./run_recommendation_system.sh
```

### 5. MCP Server Configuration (to be added to Cursor or Claude)
```json
{
    "mcpServers": {
        "recommendation-system": {
            "command": "docker",
            "args": [
                "run",
                "-i",
                "--rm",
                "--init",
                "-e","DOCKER_CONTAINER=true",
                "-v","<Path for your folder where the app folder recides>:/root/<Path for your folder where the app folder recides>",
                "recommendation-system"
            ]
        },
        "AI-Sticky-Notes":{
            "command": "uv",
            "args": ["run", "--with", "mcp[cli]", "mcp", "run", "<Path for your file where the python app recides>"]
        }
    }
}
```

AI-Sticky-Notes:
- This is not dockerized. Its a simple Agentic flow. Try this to get initial motivation. (Small steps lead to a bigger leap !! )

Recommendation-System:
Eg: Folder Paths:
Folder 1
  - App
/Users/<USER NAME>/<FOLDER 1>:/root/<FOLDER 1>
    
---

## 🧠 How It Works

- **Agents** orchestrate data flow and recommendation logic.
- **NLP Models** (e.g., Transformers) encode content for semantic similarity.
- **Similarity Search** finds the most relevant items for each user.
- **Google Sheets** can be used as a data source or output sink.
- **Results** (models, configs) are stored in the `results/` directory for reproducibility.
---

## 🛠️ Technologies

- Python 3.8+
- Model Context Protocol (MCP)
- PyTorch, HuggingFace Transformers
- Docker
- Google Sheets API
- Custom NLP and similarity utilities
---

## 📈 Example Use Cases

- Personalized content feeds
- Product or article recommendations
- Semantic search and retrieval
- Research and prototyping for recommender systems

---
---

## 👤 Author

Gurudeep  
[LinkedIn](https://www.linkedin.com/in/gurudeep-muvvala-n-v-sai/)

---

## ⭐ Why This Project?

This project is a showcase of advanced Python engineering, agentic design, and real-world ML/NLP deployment. It demonstrates my ability to build scalable, modular, and production-ready systems—skills directly applicable to industry roles in data science, machine learning, and software engineering.

---
