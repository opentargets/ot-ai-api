import express from "express";
import { getPublicationPlainText } from "../controllers/publication.js";
import {
  getPublicationSummary,
  streamTest,
  getPubSummaryPayload,
} from "../controllers/publicationSummary.js";
import logger from "../utils/logger.js";

const router = express.Router();

router.post("/publication/summary/stream", async (req, res) => {
  const { pmcId, targetSymbol, diseaseName } = getPubSummaryPayload({
    req,
    next,
  });

  res.setHeader("Content-Type", "application/ndjson");
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("Connection", "keep-alive");
  res.flushHeaders();

  streamTest({ res });
});

router.post("/publication/summary/", async (req, res) => {
  const summaryPayload = await getPubSummaryPayload({
    res,
    req,
  });
  const { pmcId, targetSymbol, diseaseName } = summaryPayload;

  logger.info(`Request on pub summary`);

  let plainText;
  let publicationSummary;
  try {
    plainText = await getPublicationPlainText({ id: pmcId });
  } catch {
    logger.error("Error getting publication text");
    return res.status(503).json({ error: "Error getting publication text" });
  }
  try {
    publicationSummary = await getPublicationSummary({
      text: plainText,
      targetSymbol,
      diseaseName,
      response: res,
    });
  } catch {
    res.status(503).json({ error: "Error getting publication summary" });
  }
  res.send(publicationSummary);
});

export default router;
