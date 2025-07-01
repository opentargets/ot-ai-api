# Open Targets AI API

This repository holds the Open Targets AI API router.

### Required stack

- [NodeJS >= v18](https://nodejs.org/en/)

### Install dependencies

```
$ npm install
```

### Running development

```
$ npm run dev
```

### Running local build

```
$ npm run start
```

### Building production-ready bundle with docker

Build your image:

```
$ docker build . -t <your username>/ot-ai-api
```

Run your image:
For running the image you need to map the port to whatever you wish to use on your host. In this example, we simply map port 49160 of the host to port 8080 of the Docker.

You will also need to provide your own OpenAI key via the environment variable `OPENAI_TOKEN` or `OPENAI_TOKEN_FILE`.

```
$ docker run -p 49160:8080 -e "OPENAI_TOKEN=XXXXXXXXXXX" -d <your username>/ot-ai-api
```

or

```
$ docker run -p 49160:8080 -e "OPENAI_TOKEN_FILE=/var/run/secrets/openai_token" -d <your username>/ot-ai-api
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
