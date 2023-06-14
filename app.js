import express from "express";
import logger from "./utils/logger.js";
import httpLogger from "./middlewares/httpLogger.js";
import literatureRouter from "./routes/literature.js";
import healthRouter from "./routes/health.js";
import { normalizePort } from "./utils/index.js";

var port = normalizePort(process.env.PORT || "8080");

const app = express();
app.use(httpLogger);
app.use(express.json());

app.use("/literature", literatureRouter);
app.use("/health", healthRouter);

app.listen(port, () => {
  logger.info(`Server listening on port ${port}`);
});
