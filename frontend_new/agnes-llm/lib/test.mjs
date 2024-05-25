import {
  PGVectorStore,
} from "@langchain/community/vectorstores/pgvector";
import { ChatOpenAI, OpenAIEmbeddings } from "@langchain/openai";

import { createRetrieverTool } from "langchain/tools/retriever";
import { AgentExecutor, createToolCallingAgent } from "langchain/agents";

import {
  ChatPromptTemplate,
  MessagesPlaceholder,
} from "@langchain/core/prompts";

const AGENT_SYSTEM_TEMPLATE = `You are an expert on climate change negotiations. All responses must be accurate. Use the available tools to look up the answers to all questions.`;

try {
    const config = {
      postgresConnectionOptions: {
        type: "postgres",
        host: process.env.HOST_NAME,
        port: 5432,
        user: process.env.USER_NAME,
        password: process.env.PASSWORD,
        database: process.env.DB_NAME,
        ssl: true
      },
      schemaName: "embed",
      tableName: "document_embeddings",
      columns: {
        idColumnName: "id",
        vectorColumnName: "vector",
        contentColumnName: "content",
        metadataColumnName: "document_id",
      },
      // supported distance strategies: cosine (default), innerProduct, or euclidean
      distanceStrategy: "cosine"
    };

    const vectorstore = new PGVectorStore(
      new OpenAIEmbeddings({apiKey: process.env.OPENAI_API_KEY, model: "text-embedding-3-small"}),
      config
    );

    const retriever = vectorstore.asRetriever();

    const tool = createRetrieverTool(retriever, {
      name: "llm_documents",
      description: "Searches and returns information on climate change negotiation streams",
    });

    const prompt = ChatPromptTemplate.fromMessages([
      ["system", AGENT_SYSTEM_TEMPLATE],
      new MessagesPlaceholder("chat_history"),
      ["human", "{input}"],
      new MessagesPlaceholder("agent_scratchpad"),
    ]);

    const chatModel = new ChatOpenAI({
      modelName: "gpt-3.5-turbo-1106",
      temperature: 0.2,
      // IMPORTANT: Must "streaming: true" on OpenAI to enable final output streaming below.
      streaming: true,
    });

    const agent = createToolCallingAgent({
      llm: chatModel,
      tools: [tool],
      prompt,
    });

    const agentExecutor = new AgentExecutor({
      agent,
      tools: [tool],
      // Set this if you want to receive all intermediate steps in the output of .invoke().
      returnIntermediateSteps: true,
    });

    console.log(agentExecutor)

    console.log("------------------")

    const result = await agentExecutor.invoke({
      input: "What are the decisions on agriculture",
      chat_history: []
    });

    console.log(result)

    //const results = await vectorstore.similaritySearch("Sharm el-Sheikh", 1);

    //console.log(retriever);

    //console.log(results);
} catch (e) {
    console.log(e)
}

