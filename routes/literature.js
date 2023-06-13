import express from "express";
import { WandbTracer } from "@wandb/sdk/integrations/langchain";
import { getPublicationPlainText } from "../controllers/publication.js";
import {
  getPublicationSummary,
  streamTest,
} from "../controllers/publicationSummary.js";
import * as dotenv from "dotenv";
import logger from "../utils/logger.js";

dotenv.config();
const router = express.Router();

router.post("/publication/summary/stream", async (req, res) => {
  res.setHeader("Content-Type", "application/ndjson");
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("Connection", "keep-alive");
  res.flushHeaders();

  streamTest({ res });
});

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

router.post("/publication/summary/", async (req, res) => {
  const payloadError = await payloadValidator({ req });
  if (payloadError.error) {
    return res.status(400).json(payloadError);
  }

  const { pmcId, targetSymbol, diseaseName } = req.body.payload;

  const prettyDiseaseName = diseaseName.replace(/\s/g, "_");
  const wbIdWithRandom = `${pmcId}_${targetSymbol}_${prettyDiseaseName}_${Math.floor(
    Math.random() * 1000
  )}`;
  const wbTracer = await WandbTracer.init(
    { project: "ot-explain", id: wbIdWithRandom },
    false
  );

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
  await WandbTracer.finish();
});

export default router;
