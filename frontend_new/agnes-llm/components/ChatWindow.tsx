"use client";

import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import { useChat } from "ai/react";
import { useRef, useState, ReactElement } from "react";
import type { FormEvent } from "react";
import type { AgentStep } from "langchain/schema";

import { ChatMessageBubble } from "@/components/ChatMessageBubble";
import { UploadDocumentsForm } from "@/components/UploadDocumentsForm";
import AudioRecorder from "@/components/AudioRecorder";
import { IntermediateStep } from "./IntermediateStep";

interface IOnFinish {
  id: string;
  audio: Blob;
}

interface IMessage {
  id: string;
  audio: Blob;
}

export function ChatWindow(props: {
  endpoint: string,
  emptyStateComponent: ReactElement,
  placeholder?: string,
  titleText?: string,
  emoji?: string;
  showIngestForm?: boolean,
  showIntermediateStepsToggle?: boolean
}) {
  const messageContainerRef = useRef<HTMLDivElement | null>(null);

  const onFinish = async ({ id, audio }: IOnFinish) => {
    if (!audio) {
      console.error("No audio file provided.");
      return;
    }

    // Prepare the form data
    const formData = new FormData();
    // Append the audio file (assuming it's a Blob) with a filename
    formData.append("file", audio, "recording.wav");

    try {
      // Call your API route instead of OpenAI directly
      const response = await fetch("/api/transcribe", {
        method: "POST",
        body: formData,
      });
  
      if (!response.ok) {
        throw new Error(`Transcription failed: ${response.statusText}`);
      }
  
      const transcription = await response.json();
      setInput(transcription.data.text);
    } catch (error) {
      console.error("Error during transcription:", error);
    }
  };
  
  const { endpoint, emptyStateComponent, placeholder, titleText = "An LLM", showIngestForm, showIntermediateStepsToggle, emoji } = props;

  const [showIntermediateSteps, setShowIntermediateSteps] = useState(false);
  const [intermediateStepsLoading, setIntermediateStepsLoading] = useState(false);
  const ingestForm = showIngestForm && <UploadDocumentsForm></UploadDocumentsForm>;
  const intemediateStepsToggle = showIntermediateStepsToggle && (
    <div>
      <input type="checkbox" id="show_intermediate_steps" name="show_intermediate_steps" checked={showIntermediateSteps} onChange={(e) => setShowIntermediateSteps(e.target.checked)}></input>
      <label htmlFor="show_intermediate_steps"> Show intermediate steps</label>
    </div>
  );

  const [sourcesForMessages, setSourcesForMessages] = useState<Record<string, any>>({});
  const [docSources, setDocSources] = useState<Array<string>>([]);

  const { messages, input, setInput, handleInputChange, handleSubmit, isLoading: chatEndpointIsLoading, setMessages } =
    useChat({
      api: endpoint,
      onResponse(response) {
        const sourcesHeader = response.headers.get("x-sources");
        const sources = sourcesHeader ? JSON.parse((Buffer.from(sourcesHeader, 'base64')).toString('utf8')) : [];
        const messageIndexHeader = response.headers.get("x-message-index");
        if (sources.length && messageIndexHeader !== null) {
          setSourcesForMessages({...sourcesForMessages, [messageIndexHeader]: sources});
        }
      },
      onError: (e) => {
        toast(e.message, {
          theme: "dark"
        });
      }
    });

  async function sendMessage(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (messageContainerRef.current) {
      messageContainerRef.current.classList.add("grow");
    }
    if (!messages.length) {
      await new Promise(resolve => setTimeout(resolve, 300));
    }
    if (chatEndpointIsLoading ?? intermediateStepsLoading) {
      return;
    }
    //if (!showIntermediateSteps) {
    //  handleSubmit(e);
    // Some extra work to show intermediate steps properly
    //} else {
    setIntermediateStepsLoading(true);
    setInput("");
    const messagesWithUserReply = messages.concat({ id: messages.length.toString(), content: input, role: "user" });
    setMessages(messagesWithUserReply);
    const response = await fetch(endpoint, {
      method: "POST",
      body: JSON.stringify({
        messages: messagesWithUserReply
      })
    });
    const json = await response.json();
    setIntermediateStepsLoading(false);
    if (response.status === 200) {
      // Represent intermediate steps as system messages for display purposes 
      const newMessages = messagesWithUserReply;
      setSourcesForMessages({...sourcesForMessages, [(newMessages.length).toString()]: json.sources});
      setMessages([...newMessages, { id: (newMessages.length).toString(), content: json.answer, role: "assistant" }]);
    } else {
      if (json.error) {
        toast(json.error, {
          theme: "dark"
        });
        throw new Error(json.error);
      }
    }
  }

  return (
    <div className={`mb-10 flex flex-col items-center p-4 md:p-8 rounded grow overflow-hidden ${(messages.length > 0 ? "border" : "")}`}>
      <h1 className={`${messages.length > 0 ? "" : "hidden"} text-2xl text-white`}>{emoji} {titleText}</h1>
      {messages.length === 0 ? emptyStateComponent : ""}
      <div
        className="flex flex-col-reverse w-full mb-4 overflow-auto transition-[flex-grow] ease-in-out"
        ref={messageContainerRef}
      >
        {messages.length > 0 ? (
          [...messages]
            .reverse()
            .map((m, i) => {
              const sourceKey = (messages.length - 1 - i).toString();
              return (m.role === "system" ? <IntermediateStep key={m.id} message={m}></IntermediateStep> : <ChatMessageBubble key={m.id} message={m} aiEmoji={emoji} sources={sourcesForMessages[sourceKey]}></ChatMessageBubble>)
            })
        ) : (
          ""
        )}
      </div>

      {messages.length === 0 && ingestForm}

      <form onSubmit={sendMessage} className="flex w-full flex-col">
        <div className="flex">
          {intemediateStepsToggle}
        </div>
        <div className="flex flex-col sm:flex-row w-full mt-4 sm:mt-6">
          <div className="flex border rounded-lg w-full mr-6">
            <input
              id="text_input"
              type="text"
              className="grow p-4 border-0 focus:ring-0 rounded-l-lg"
              value={input}
              placeholder={placeholder ?? "What is Climate Change?"}
              onChange={handleInputChange}
            />
            <AudioRecorder onFinish={onFinish} />
          </div>
         
          <button 
            type="submit"
            title="Press this button to ask the AI a question"
            className="mt-1 shrink-0 px-8 py-4 bg-sky-600 rounded w-28">
            <div role="status" className={`${(chatEndpointIsLoading || intermediateStepsLoading) ? "" : "hidden"} flex justify-center`}>
              <svg aria-hidden="true" className="w-6 h-6 text-white animate-spin dark:text-white fill-sky-800" viewBox="0 0 100 101" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M100 50.5908C100 78.2051 77.6142 100.591 50 100.591C22.3858 100.591 0 78.2051 0 50.5908C0 22.9766 22.3858 0.59082 50 0.59082C77.6142 0.59082 100 22.9766 100 50.5908ZM9.08144 50.5908C9.08144 73.1895 27.4013 91.5094 50 91.5094C72.5987 91.5094 90.9186 73.1895 90.9186 50.5908C90.9186 27.9921 72.5987 9.67226 50 9.67226C27.4013 9.67226 9.08144 27.9921 9.08144 50.5908Z" fill="currentColor"/>
                  <path d="M93.9676 39.0409C96.393 38.4038 97.8624 35.9116 97.0079 33.5539C95.2932 28.8227 92.871 24.3692 89.8167 20.348C85.8452 15.1192 80.8826 10.7238 75.2124 7.41289C69.5422 4.10194 63.2754 1.94025 56.7698 1.05124C51.7666 0.367541 46.6976 0.446843 41.7345 1.27873C39.2613 1.69328 37.813 4.19778 38.4501 6.62326C39.0873 9.04874 41.5694 10.4717 44.0505 10.1071C47.8511 9.54855 51.7191 9.52689 55.5402 10.0491C60.8642 10.7766 65.9928 12.5457 70.6331 15.2552C75.2735 17.9648 79.3347 21.5619 82.5849 25.841C84.9175 28.9121 86.7997 32.2913 88.1811 35.8758C89.083 38.2158 91.5421 39.6781 93.9676 39.0409Z" fill="currentFill"/>
              </svg>
              <span className="sr-only">Loading...</span>
            </div>
            <span className={(chatEndpointIsLoading || intermediateStepsLoading) ? "hidden" : "askai"}>Ask AI</span>
          </button>
        </div>
      </form>
      <ToastContainer/>
    </div>
  );
}
