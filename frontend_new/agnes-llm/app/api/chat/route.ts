import { NextRequest, NextResponse } from "next/server";
import { Message as VercelChatMessage } from "ai";
import { RunnableBranch } from "@langchain/core/runnables";
import { StringOutputParser } from "@langchain/core/output_parsers"

import {
  DistanceStrategy,
  PGVectorStore,
} from "@langchain/community/vectorstores/pgvector";
import { PoolConfig } from "pg";

import { AIMessage, ChatMessage, HumanMessage } from "@langchain/core/messages";
import { ChatOpenAI, OpenAIEmbeddings } from "@langchain/openai";
import { createStuffDocumentsChain } from "langchain/chains/combine_documents";
import {
  ChatPromptTemplate,
  MessagesPlaceholder,
} from "@langchain/core/prompts";

import type { BaseMessage } from "@langchain/core/messages";
import {
  RunnablePassthrough,
  RunnableSequence,
} from "@langchain/core/runnables";

export const runtime = "nodejs";

const convertVercelMessageToLangChainMessage = (message: VercelChatMessage) => {
  if (message.role === "user") {
    return new HumanMessage(message.content);
  } else if (message.role === "assistant") {
    return new AIMessage(message.content);
  } else {
    return new ChatMessage(message.content, message.role);
  }
};

const AGENT_SYSTEM_TEMPLATE = `You are an expert on climate change negotiations. Answer the user's questions based on the context below:

<context>
{context}
</context>
`;

/**
 * This handler initializes and calls a retrieval agent. It requires an OpenAI
 * Functions model. See the docs for more information:
 *
 * https://js.langchain.com/docs/use_cases/question_answering/conversational_retrieval_agents
 */
export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    /**
     * We represent intermediate steps as system messages for display purposes,
     * but don't want them in the chat history.
     */
    const messages = (body.messages ?? []).filter(
      (message: VercelChatMessage) =>
        message.role === "user" || message.role === "assistant",
    );
    const previousMessages = messages
      .slice(0, -1)
      .map(convertVercelMessageToLangChainMessage);
    const currentMessageContent = messages[messages.length - 1].content;
   
    const config = {
      postgresConnectionOptions: {
        type: "postgres",
        host: process.env.HOST_NAME,
        port: 5432,
        user: process.env.USER_NAME,
        password: process.env.PASSWORD,
        database: process.env.DB_NAME,
        ssl: true
      } as PoolConfig,
      schemaName: "embed",
      tableName: "llm_documents_with_metadata",
      columns: {
        idColumnName: "id",
        vectorColumnName: "vector",
        contentColumnName: "content",
        metadataColumnName: "url",
      },
      // supported distance strategies: cosine (default), innerProduct, or euclidean
      distanceStrategy: "cosine" as DistanceStrategy
    };

    const vectorstore = new PGVectorStore(
      new OpenAIEmbeddings({apiKey: process.env.OPENAI_API_KEY, model: "text-embedding-3-small"}),
      config
    );

    const retriever = vectorstore.asRetriever();
   
    const prompt = ChatPromptTemplate.fromMessages([
      ["system", AGENT_SYSTEM_TEMPLATE],
      new MessagesPlaceholder("input"),
    ]);

    const chatModel = new ChatOpenAI({
      modelName: "gpt-3.5-turbo-1106",
      temperature: 0.01,
      // IMPORTANT: Must "streaming: true" on OpenAI to enable final output streaming below.
      streaming: true,
    });

    const documentChain = await createStuffDocumentsChain({
      llm: chatModel,
      prompt: prompt,
    });

    const parseRetrieverInput = (params: { input: BaseMessage[] }) => {
      return params.input[params.input.length - 1].content;
    };

    const queryTransformPrompt = ChatPromptTemplate.fromMessages([
      new MessagesPlaceholder("input"),
      [
        "user",
        "Given the above conversation, generate a search query to look up in order to get information relevant to the conversation. Only respond with the query, nothing else.",
      ],
    ]);

    const queryTransformingRetrieverChain = RunnableBranch.from([
      [
        (params: { input: BaseMessage[] }) => params.input.length === 1,
        RunnableSequence.from([parseRetrieverInput, retriever]),
      ],
      queryTransformPrompt
        .pipe(chatModel)
        .pipe(new StringOutputParser())
        .pipe(retriever),
    ]).withConfig({ runName: "chat_retriever_chain" });

    const conversationalRetrievalChain = RunnablePassthrough.assign({
      context: queryTransformingRetrieverChain,
    }).assign({
      answer: documentChain,
    });

    let res = await conversationalRetrievalChain.invoke({
      input: [
        new HumanMessage(currentMessageContent),
      ],
    });

    let sources:any = [];
    if (res.context){
      if(res.context.length > 0){
        for (let i = 0; i < res.context.length; i++) {
          let metadata = res.context[i].metadata
          if(!sources.includes(metadata)){
            sources.push(metadata)
          }
        }
      }
    }
    return NextResponse.json({ answer: res.answer, sources: sources });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: e.status ?? 500 });
  }
}
