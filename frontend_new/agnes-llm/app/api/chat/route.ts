import { NextRequest, NextResponse } from "next/server";
import { Message as VercelChatMessage } from "ai";
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
  RunnableBranch
} from "@langchain/core/runnables";

import {
  BaseRetriever,
  type BaseRetrieverInput,
} from "@langchain/core/retrievers";
import type { CallbackManagerForRetrieverRun } from "@langchain/core/callbacks/manager";
import { Document } from "@langchain/core/documents";

import {removeStopwords, eng}  from "stopword";
import {compareTwoStrings} from "string-similarity";

interface CustomRetrieverInput extends BaseRetrieverInput {}
const additional_stop_words = ["decision","decisions","latest","recent","main","key","point","points","idea","ideas","unfccc"];
const postgresOptions = {
  type: "postgres",
  host: process.env.HOST_NAME,
  port: 5432,
  user: process.env.USER_NAME,
  password: process.env.PASSWORD,
  database: process.env.DB_NAME,
  ssl: true
}

class CustomRetriever extends BaseRetriever {
  lc_namespace = ["langchain", "retrievers"];

  constructor(fields?: CustomRetrieverInput) {
    super(fields);
  }

  async _getRelevantDocuments(
    query: string,
    runManager?: CallbackManagerForRetrieverRun
  ): Promise<Document[]> {

    const punctRE = /[\u2000-\u206F\u2E00-\u2E7F\\'!"#$%&()*+,\-.\/:;<=>?@\[\]^_`{|}~]/g;
    query = query.replace(punctRE, '');
  
    const config = {
      postgresConnectionOptions: postgresOptions as PoolConfig,
      schemaName: "embed",
      tableName: "vw_decisions_documents",
      columns: {
        idColumnName: "id",
        vectorColumnName: "title_vector",
        contentColumnName: "title",
        metadataColumnName: "metadata",
      },
      distanceStrategy: "cosine" as DistanceStrategy
    };
  
    const vectorstore = new PGVectorStore(
      new OpenAIEmbeddings({apiKey: process.env.OPENAI_API_KEY, model: "text-embedding-3-small"}),
      config
    );

    const retriever = vectorstore.asRetriever();

    const query_mod = removeStopwords(query.split(" "),eng.concat(additional_stop_words)).join(" ").toLowerCase();
    
    let docs = await retriever._getRelevantDocuments(query_mod);

    let metadata_filtered = []
    for (let i in docs) {
      let pageContent = docs[i].pageContent.split("-")[1]
      let metadata = docs[i].metadata
      let id = parseInt(metadata["id"])
      let created = metadata["created"]
      let pageContent_mod = removeStopwords(pageContent.split(" "), eng.concat(additional_stop_words)).join(" ").toLowerCase() 
      let similarity_score = compareTwoStrings(query_mod, pageContent_mod)
      if ( similarity_score > 0.5 ){
        metadata_filtered.push({"id":id,"created":created})
      }
    }
    metadata_filtered.sort(function(a,b){
      return new Date(b.created).getTime() - new Date(a.created).getTime();
    });
  
    let document_ids = []
    metadata_filtered = metadata_filtered.slice(0,2)
    for (let i in metadata_filtered) {
      document_ids.push(metadata_filtered[i].id)
    }

    let decisions_docs: Document[] = [];

    if(document_ids.length > 0){
      const config2 = {
        postgresConnectionOptions: postgresOptions as PoolConfig,
        schemaName: "embed",
        tableName: "vw_decisions_embeddings",
        columns: {
          idColumnName: "id",
          vectorColumnName: "vector",
          contentColumnName: "content",
          metadataColumnName: "metadata",
        },
        distanceStrategy: "cosine" as DistanceStrategy
      };

      const vectorstore2 = new PGVectorStore(
        new OpenAIEmbeddings({apiKey: process.env.OPENAI_API_KEY, model: "text-embedding-3-small"}),
        config2
      );
    
      const retriever2 = vectorstore2.asRetriever({filter:{document_id:{"in":document_ids}}});
      decisions_docs = await retriever2._getRelevantDocuments(query);
    }
    
    const config3 = {
      postgresConnectionOptions: postgresOptions as PoolConfig,
      schemaName: "embed",
      tableName: "vw_proceedings_embeddings",
      columns: {
        idColumnName: "id",
        vectorColumnName: "vector",
        contentColumnName: "content",
        metadataColumnName: "metadata",
      },
      distanceStrategy: "cosine" as DistanceStrategy
    };

    const vectorstore3 = new PGVectorStore(
      new OpenAIEmbeddings({apiKey: process.env.OPENAI_API_KEY, model: "text-embedding-3-small"}),
      config3
    );
  
    const retriever3 = vectorstore3.asRetriever();
    let proceedings_docs = await retriever3._getRelevantDocuments(query);

    if(decisions_docs.length > 0){
      return decisions_docs
    }
    return decisions_docs.concat(proceedings_docs);
  }
}

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

const AGENT_SYSTEM_TEMPLATE = `You are an expert on climate change negotiations. 
Answer the user's questions based on the below context. 
If the context doesn't contain any relevant information to the question, don't make something up and ask the user to rephrase his/her question:

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

    //const retriever = vectorstore.asRetriever();
    const retriever = new CustomRetriever({});
   
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
      input: previousMessages.concat([
        new HumanMessage(currentMessageContent),
      ]),
    });

    let sources:any = [];

    if(
      (!res.answer.toLowerCase().includes("if you have any questions")) && 
      (!res.answer.toLowerCase().includes("do you have")) && 
      (!res.answer.toLowerCase().includes("here to help")) && 
      (!res.answer.toLowerCase().includes("here to provide")) && 
      (!res.answer.toLowerCase().includes("rephrase")) && 
      (!res.answer.toLowerCase().includes("cannot provide")) && 
      (!res.answer.toLowerCase().includes("can't provide")) &&
      (!res.answer.toLowerCase().includes("please provide")) && 
      (!res.answer.toLowerCase().includes("sorry")) &&
      (!res.answer.toLowerCase().includes("i can help")) &&
      (!res.answer.toLowerCase().includes("feel free")) &&
      (!res.answer.toLowerCase().includes("if you have")) &&
      (!res.answer.toLowerCase().includes("i recommend"))
    ){
      if (res.context){
        if(res.context.length > 0){
          let processed_urls: string[] = []
          for (let i = 0; i < res.context.length; i++) {
            let metadata = {
              "title": res.context[i].metadata.title,
              "url": res.context[i].metadata.url
            }
            if(!processed_urls.includes(metadata.url)){
              processed_urls.push(metadata.url)
              sources.push(metadata)
            }
          }
        }
      }
    }
    return NextResponse.json({ answer: res.answer, sources: sources });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: e.status ?? 500 });
  }
}
