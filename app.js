import createError from "http-errors";
import express from "express";
import cookieParser from "cookie-parser";
import logger from "./utils/logger.js";
import httpLogger from "./middlewares/httpLogger.js";
import literatureRouter from "./routes/literature.js";

function normalizePort(val) {
  var port = parseInt(val, 10);
  if (isNaN(port)) {
    return val;
  }
  if (port >= 0) {
    return port;
  }
  return false;
}

var port = normalizePort(process.env.PORT || "8080");

// TODO: review app use
const invalidPathHandler = (request, response, next) => {
  logger.error("Invalid path");
  return next(createError("404", "Invalid path"));
};

const app = express();
app.use(httpLogger);
app.use(express.json());
app.use(express.urlencoded({ extended: false }));
app.use(cookieParser());
// app.use(errorHandler);
// app.use(invalidPathHandler);

// app.use("/", indexRouter);
app.use("/literature", literatureRouter);

app.listen(port, () => {
  logger.info(`Server listening on port ${port}`);
});
