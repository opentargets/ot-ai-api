import express from "express";
import { WandbTracer } from "@wandb/sdk/integrations/langchain";
import { getPublicationPlainText } from "../controllers/publication.js";
import {
  getPublicationSummary,
  streamTest,
  getPubSummaryPayload,
} from "../controllers/publicationSummary.js";
import * as dotenv from "dotenv";

dotenv.config();
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

  const wbIdWithRandom = `${pmcId}_${targetSymbol}_${diseaseName}_${Math.floor(
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
    res.status(503).json({ error: "Error getting publication summary" });
  }
  res.send(publicationSummary);
  await WandbTracer.finish();
});

export default router;
