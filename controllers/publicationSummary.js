import wandb from "@wandb/sdk";
import { loadQAMapReduceChain } from "langchain/chains";
import { OpenAI } from "langchain/llms/openai";
import { RecursiveCharacterTextSplitter } from "langchain/text_splitter";

import * as dotenv from "dotenv";
import fs from "fs";
import logger from "../utils/logger.js";

dotenv.config();

// query setup
// summarization docs https://js.langchain.com/docs/api/chains/functions/loadQAMapReduceChain
const getOpenAIToken = () => {
  if (process.env.OPENAI_TOKEN_FILE) {
    try {
      return fs.readFileSync(process.env.OPENAI_TOKEN_FILE, 'utf8').trim();
    } catch (error) {
      logger.error(`Error reading OPENAI_TOKEN_FILE: ${error.message}`);
      throw new Error('Failed to read OpenAI token file');
    }
  }
  else if (process.env.OPENAI_TOKEN) {
    return process.env.OPENAI_TOKEN;
  }

  throw new Error('OPENAI_TOKEN or OPENAI_TOKEN_FILE must be provided');
};

const model = new OpenAI({
  modelName: "gpt-4o-mini",
  openAIApiKey: getOpenAIToken(),
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
  wbTracer = null,
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
  logger.info("request to openai");
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
    return apiResponse;
  } else {
    const apiResponse = await chain.call({
      input_documents: docs,
      question: prompt,
    });
    return apiResponse;
  }
};
