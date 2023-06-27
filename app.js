import express from "express";
import cors from "cors";

import logger from "./utils/logger.js";
import httpLogger from "./middlewares/httpLogger.js";
import literatureRouter from "./routes/literature.js";
import healthRouter from "./routes/health.js";
import { normalizePort, isProduction, isDevelopment } from "./utils/index.js";

const port = normalizePort(process.env.PORT || "8080");
const originRegExp = /^(.*\.)?opentargets\.(org|xyz)$/;

const app = express();

app.use(httpLogger);
app.use(express.json());

if (isDevelopment) {
  app.use(cors());
}

if (isProduction) {
  app.use(
    cors({
      origin: [originRegExp],
    })
  );
}

app.use("/literature", literatureRouter);
app.use("/health", healthRouter);

app.listen(port, () => {
  logger.info(`Server listening on port ${port}`);
});
