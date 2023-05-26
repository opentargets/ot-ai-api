import { loadQAMapReduceChain } from "langchain/chains";
import { OpenAI } from "langchain/llms/openai";
import { PromptTemplate } from "langchain/prompts";
import { RecursiveCharacterTextSplitter } from "langchain/text_splitter";

import * as dotenv from "dotenv";
dotenv.config();

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

  console.log({ wordCount, docsLength: docs.length });

  const chain = loadQAMapReduceChain(model);
  const apiResponse = await chain.call({
    input_documents: docs,
    question: prompt,
  });

  return apiResponse;
};
