import { loadQAMapReduceChain } from "langchain/chains";
import { OpenAI } from "langchain/llms/openai";
import { RecursiveCharacterTextSplitter } from "langchain/text_splitter";
import wandb from "@wandb/sdk";

import * as dotenv from "dotenv";
import logger from "../utils/logger.js";

dotenv.config();

async function payloadValidator({ req, res }) {
  if (!req.body.payload) {
    res.status(400).json({ error: "Missing payload" });
  }
  if (!req.body.payload.pmcId) {
    res.status(400).json({ error: "Missing pmcId in payload" });
  }
  if (!req.body.payload.targetSymbol) {
    res.status(400).json({ error: "Missing targetSymbol in payload" });
  }
  if (!req.body.payload.diseaseName) {
    res.status(400).json({ error: "Missing diseaseName in payload" });
  }

  return req.body.payload;
}

export async function getPubSummaryPayload({ req, res }) {
  const { pmcId, targetSymbol, diseaseName } = await payloadValidator({
    req,
    res,
  });

  return { pmcId, targetSymbol, diseaseName };
}

// query setup
// summarization docs https://js.langchain.com/docs/api/chains/functions/loadQAMapReduceChain
const model = new OpenAI({
  modelName: "gpt-3.5-turbo",
  openAIApiKey: process.env.OPENAI_TOKEN,
  temperature: 0.5,
});

const createPrompt = ({ targetSymbol, diseaseName }) => {
  return `
  Can you provide a concise summary about the relationship between ${targetSymbol} and ${diseaseName} according to this study?`;
};

export const streamTest = ({ res }) => {
  var sendAndSleep = function (response, counter) {
    if (counter > 10) {
      response.end();
    } else {
      response.write(" ;i=" + counter);
      counter++;
      setTimeout(function () {
        sendAndSleep(response, counter);
      }, 1000);
    }
  };

  res.setHeader("Content-Type", "text/html; charset=utf-8");
  res.setHeader("Transfer-Encoding", "chunked");

  res.write("Thinking...");
  sendAndSleep(res, 1);
};

export const getPublicationSummary = async ({
  text,
  targetSymbol,
  diseaseName,
  pmcId,
  wbTracer,
}) => {
  const prompt = createPrompt({ targetSymbol, diseaseName });

  const wordCount = text.split(" ").length;
  const chunkSize = 14000; // max character count per chunk
  const textSplitter = new RecursiveCharacterTextSplitter({
    chunkSize,
    separators: ["\n\n", "\n", " "],
  });

  const docs = await textSplitter.createDocuments([text]);

  logger.info(JSON.stringify({ wordCount, docsLength: docs.length }));

  const chain = loadQAMapReduceChain(model);
  logger.info("reauest to gpt");
  if (wbTracer !== null) {
    wandb.log({
      targetSymbol: targetSymbol,
      diseaseName: diseaseName,
      pmcId: pmcId,
      chunkSize: chunkSize,
      wordCount: wordCount,
      docsLength: docs.length,
    });
    const apiResponse = await chain.call(
      {
        input_documents: docs,
        question: prompt,
      },
      wbTracer
    );
    if (apiResponse.text.includes("no concise summary")) {
      wandb.log({ successFlag: 0 });
    } else {
      wandb.log({ successFlag: 1 });
    }
  } else {
    return await chain.call({
      input_documents: docs,
      question: prompt,
    });
  }
};
