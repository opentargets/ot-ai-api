# Open Targets AI API

**Open Targets AI API** is a specialized API service that provides AI-driven endpoints to support the Open Targets web application, integrating natural language processing (NLP) and data extraction features.

### Features

- **AI-Driven Endpoints**: Generates natural language summaries and insights on target-disease evidence from publications.
- **Integration with LangChain**: Facilitates NLP and AI functionalities via OpenAI models.
- **Automatic Documentation**: Accessible through Swagger and ReDoc endpoints for streamlined API exploration.

### Requirements

- **Python 3.8+**
- [**FastAPI**](https://fastapi.tiangolo.com/) for API management
- [**UV**](https://docs.astral.sh/uv/) for dependency and environment management
- **Docker** for deployment

### Setup and Installation

1. **Clone the repository**:

   ```bash
   git clone git@github.com:opentargets/ot-ai-api.git
   cd ot-ai-api
   ```

2. **Install dependencies** using UV:

   ```bash
   uv sync
   ```

3. **Run development server**:

   ```bash
   uv run fastapi dev
   ```

### Usage

- Access Swagger documentation at [http://localhost:8000/docs](http://localhost:8000/docs).
- Access ReDoc documentation at [http://localhost:8000/redoc](http://localhost:8000/redoc).

### Building production-ready bundle with docker

Build your image:

```
$ docker build . -t <your username>/ot-ai-api
```

Run your image:
For running the image you need to map the port to whatever you wish to use on your host. In this example, we simply map port 49160 of the host to port 8080 of the Docker.

Youl will also need to provide your own OpenAI key via the environment variable `OPENAI_TOKEN`.

```
$ docker run -p 49160:8080 -e "OPENAI_TOKEN=XXXXXXXXXXX" -d <your username>/ot-ai-api
```

## Copyright

Copyright 2014-2024 EMBL - European Bioinformatics Institute, Genentech, GSK, MSD, Pfizer, Sanofi and Wellcome Sanger Institute

This software was developed as part of the Open Targets project. For more information please see: http://www.opentargets.org

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
