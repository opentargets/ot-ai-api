import { loadQAMapReduceChain } from "langchain/chains";
import { OpenAI } from "langchain/llms/openai";
import { RecursiveCharacterTextSplitter } from "langchain/text_splitter";
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
  maxConcurrency: 10,
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
}) => {
  const prompt = createPrompt({ targetSymbol, diseaseName });

  const wordCount = text.split(" ").length;
  // generate docs from textSplitter only if wordCount is bigger than 4000 words, otherwise use the text as is
  const textSplitter = new RecursiveCharacterTextSplitter({
    chunkSize: 4000,
    chunkOverlap: 200,
    separators: ["\n\n", "\n", " "],
  });

  const docs = await textSplitter.createDocuments([text]);

  logger.info(JSON.stringify({ wordCount, docsLength: docs.length }));

  let apiResponse;
  const chain = loadQAMapReduceChain(model);
  logger.info("reauest to gpt");
  apiResponse = await chain.call({
    input_documents: docs,
    question: prompt,
  });
  return apiResponse;
};
