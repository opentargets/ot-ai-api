import express from "express";
import {WandbTracer} from '@wandb/sdk/integrations/langchain';
import { getPublicationPlainText } from "../controllers/publication.js";
import {
  getPublicationSummary,
  streamTest,
} from "../controllers/publicationSummary.js";
import * as dotenv from "dotenv";

dotenv.config();
const router = express.Router();

router.post("/publication/summary/stream", async (req, res) => {
  const pmcId = req.body.payload.pmcId;
  const targetSymbol = req.body.payload.targetSymbol;
  const diseaseName = req.body.payload.diseaseName;
  streamTest({ res });
});

const validatePubummaryPayload = async ({
  payload: { pmcId, targetSymbol, diseaseName },
}) => {
  if (!pmcId || !targetSymbol || !diseaseName) {
    throw new Error("BROKEN");
  }
};

router.post("/publication/summary/", async (req, res, next) => {
  const pmcId = req.body.payload.pmcId;
  const targetSymbol = req.body.payload.targetSymbol;
  const diseaseName = req.body.payload.diseaseName;

  const wbIdWithRandom = `${pmcId}_${targetSymbol}_${diseaseName}_${Math.floor(Math.random() * 1000)}`;
  const wbTracer = await WandbTracer.init(
        {project: "ot-explain", id: wbIdWithRandom},
        false,
      );
  // const wbTracer = null;
  
  try {
    await validatePubummaryPayload(req.body);
  } catch (err) {
    next(err);
  }
  // validatePubummaryPayload(req.body);

  console.log({ pmcId, targetSymbol, diseaseName });
  const plainText = await getPublicationPlainText({ id: pmcId });
  const json = await getPublicationSummary({
    text: plainText,
    targetSymbol,
    diseaseName,
    pmcId,
    wbTracer,
    response: res,
  });
  res.send(json);
  await WandbTracer.finish();
});

export default router;
