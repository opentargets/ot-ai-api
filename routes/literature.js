import express from "express";
import { getPublicationPlainText } from "../controllers/publication.js";
import {
  getPublicationSummary,
  streamTest,
} from "../controllers/publicationSummary.js";

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
    response: res,
  });
  res.send(json);
});

export default router;
