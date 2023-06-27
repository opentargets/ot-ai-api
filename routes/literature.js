import express from "express";
import { WandbTracer } from "@wandb/sdk/integrations/langchain";
import * as dotenv from "dotenv";

import { getPublicationPlainText } from "../controllers/publication.js";
import {
  getPublicationSummary,
  streamTest,
} from "../controllers/publicationSummary.js";
import { isDevelopment } from "../utils/index.js";
import logger from "../utils/logger.js";

dotenv.config();
const router = express.Router();

async function payloadValidator({ req }) {
  let error = false;
  if (!req.body.payload) {
    error = "Missing payload";
  }
  if (!req.body.payload.pmcId) {
    error = "Missing pmcId in payload";
  }
  if (!req.body.payload.targetSymbol) {
    error = "Missing targetSymbol in payload";
  }
  if (!req.body.payload.diseaseName) {
    error = "Missing diseaseName in payload";
  }
  return { error };
}

router.post("/publication/summary/stream", async (req, res) => {
  res.setHeader("Content-Type", "application/ndjson");
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("Connection", "keep-alive");
  res.flushHeaders();

  streamTest({ res });
});

router.post("/publication/summary/", async (req, res) => {
  const payloadError = await payloadValidator({ req });
  if (payloadError.error) {
    return res.status(400).json(payloadError);
  }

  const { pmcId, targetSymbol, diseaseName } = req.body.payload;

  const prettyDiseaseName = diseaseName.replace(/\s/g, "_");
  const queryId = `${pmcId}_${targetSymbol}_${prettyDiseaseName}`;
  const wbIdWithRandom = `${queryId}_${Math.floor(Math.random() * 1000)}`;
  let wbTracer = null;
  if (isDevelopment) {
    wbTracer = await WandbTracer.init(
      { project: "ot-explain", id: wbIdWithRandom },
      false
    );
  }

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
      pmcId,
      wbTracer,
      response: res,
    });
  } catch {
    return res.status(503).json({ error: "Error getting publication summary" });
  }
  res.json(publicationSummary);
  if (wbTracer) {
    await WandbTracer.finish();
  }
});

export default router;
