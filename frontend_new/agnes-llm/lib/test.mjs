import {
  PGVectorStore,
} from "@langchain/community/vectorstores/pgvector";
import { ChatOpenAI, OpenAIEmbeddings } from "@langchain/openai";

import { createRetrieverTool } from "langchain/tools/retriever";
import { AgentExecutor, createToolCallingAgent } from "langchain/agents";
import { ChromaTranslator } from "langchain/retrievers/self_query/chroma";

import {
  ChatPromptTemplate,
  MessagesPlaceholder,
} from "@langchain/core/prompts";

import {compareTwoStrings} from "string-similarity";
import {removeStopwords, eng}  from "stopword";
import { z } from "zod";
import { Comparison} from "langchain/chains/query_constructor/ir";
import { Operation} from "langchain/chains/query_constructor/ir";

const AGENT_SYSTEM_TEMPLATE = `You are an expert on climate change negotiations. All responses must be accurate. Use the available tools to look up the answers to all questions.`;
const postgresOptions = {
  type: "postgres",
  host: process.env.HOST_NAME,
  port: 5432,
  user: process.env.USER_NAME,
  password: process.env.PASSWORD,
  database: process.env.DB_NAME,
  ssl: true
}

try {
  const config = {
    postgresConnectionOptions: postgresOptions,
    schemaName: "embed",
    tableName: "llm_metadata",
    columns: {
      idColumnName: "id",
      vectorColumnName: "title_vector",
      contentColumnName: "title",
      metadataColumnName: "metadata",
    },
    // supported distance strategies: cosine (default), innerProduct, or euclidean
    distanceStrategy: "cosine"
  };

  const vectorstore = new PGVectorStore(
    new OpenAIEmbeddings({apiKey: process.env.OPENAI_API_KEY, model: "text-embedding-3-small"}),
    config
  );

  const retriever = vectorstore.asRetriever(20);

  let query = "What is the Koronivia Joint work?"
  // const punctRE = /[\u2000-\u206F\u2E00-\u2E7F\\'!"#$%&()*+,\-.\/:;<=>?@\[\]^_`{|}~]/g;
  // query = query.replace(punctRE, '')

  // let docs = await retriever._getRelevantDocuments(query)
  
  // const query_mod = removeStopwords(query.split(" "),eng.concat(["decision","decisions","latest","recent","main","key","point","points","idea","ideas"])).join(" ").toLowerCase()
  // console.log(query_mod)
  // console.log("--------------------")

  // let docs_filtered = []
  // for (let i in docs) {
  //   let pageContent = docs[i].pageContent.split("-")[1]
  //   let metadata = docs[i].metadata
  //   let id = parseInt(metadata.split("@")[0])
  //   let created = metadata.split("@")[1]
  //   let pageContent_mod = removeStopwords(pageContent.split(" "), eng).join(" ").toLowerCase() 
  //   let similarity_score = compareTwoStrings(query_mod, pageContent_mod)
  //   if ( similarity_score > 0.45 ){
  //     console.log(pageContent_mod)
  //     console.log(similarity_score)
  //     docs_filtered.push({"id":id,"created":created})
  //   }
  // }
  // docs_filtered.sort(function(a,b){
  //   return new Date(b.created) - new Date(a.created);
  // });

  // docs_filtered = docs_filtered.slice(0,2)
  // console.log(docs_filtered)

  const config2 = {
    postgresConnectionOptions: postgresOptions,
    schemaName: "embed",
    tableName: "document_embeddings2",
    columns: {
      idColumnName: "id",
      vectorColumnName: "vector",
      contentColumnName: "content",
      metadataColumnName: "document_id",
    },
    // supported distance strategies: cosine (default), innerProduct, or euclidean
    distanceStrategy: "cosine"
  };

  const vectorstore2 = new PGVectorStore(
    new OpenAIEmbeddings({apiKey: process.env.OPENAI_API_KEY, model: "text-embedding-3-small"}),
    config2
  );

  const searchSchema = z.object({
    query: z.string(),
    document_id: z.number().optional()
  });
  
  const searchQuery = {
    query: query,
    document_id: 1
  };

  function constructComparisons(
    query
  ){
    const comparisons = [];
    if (query.author !== undefined) {
      comparisons.push(
        new Comparison("eq", "document_id", query.document_id)
      );
    }
    return comparisons;
  }

  const comparisons = constructComparisons(query);
  const _filter = new Operation("and", comparisons);

  const retriever2 = vectorstore2.asRetriever({filter:{"document_id":{"in":[1]}}});
  let docs2 = retriever2._getRelevantDocuments("Sharm el-Sheikh");
  console.log(docs2)
  // const tool = createRetrieverTool(retriever, {
  //   name: "llm_documents",
  //   description: "Searches and returns information on climate change negotiation streams",
  // });

  // const prompt = ChatPromptTemplate.fromMessages([
  //   ["system", AGENT_SYSTEM_TEMPLATE],
  //   new MessagesPlaceholder("chat_history"),
  //   ["human", "{input}"],
  //   new MessagesPlaceholder("agent_scratchpad"),
  // ]);

  // const chatModel = new ChatOpenAI({
  //   modelName: "gpt-3.5-turbo-1106",
  //   temperature: 0.2,
  //   // IMPORTANT: Must "streaming: true" on OpenAI to enable final output streaming below.
  //   streaming: true,
  // });

  // const agent = createToolCallingAgent({
  //   llm: chatModel,
  //   tools: [tool],
  //   prompt,
  // });

  // const agentExecutor = new AgentExecutor({
  //   agent,
  //   tools: [tool],
  //   // Set this if you want to receive all intermediate steps in the output of .invoke().
  //   returnIntermediateSteps: true,
  // });

  // console.log(agentExecutor)

  // console.log("------------------")

  // const result = await agentExecutor.invoke({
  //   input: "What are the decisions on agriculture",
  //   chat_history: []
  // });

  // console.log(result)

    //const results = await vectorstore.similaritySearch("Sharm el-Sheikh", 1);

    //console.log(retriever);

    //console.log(results);
} catch (e) {
    console.log(e)
}

