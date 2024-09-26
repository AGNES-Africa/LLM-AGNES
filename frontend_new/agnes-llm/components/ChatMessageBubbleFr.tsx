import type { Message } from "ai/react";

export function ChatMessageBubbleFr(props: { message: Message, aiEmoji?: string, sources: any[] }) {
  const colorClassName =
    props.message.role === "user" ? "bg-sky-600" : "bg-slate-50 text-black";
  const alignmentClassName =
    props.message.role === "user" ? "ml-auto" : "mr-auto";
  const prefix = props.message.role === "user" ? "🧑🏾" : props.aiEmoji;
  return (
    <div
      className={`${alignmentClassName} ${colorClassName} rounded px-4 py-2 max-w-[80%] mb-8 flex`}
    >
      <div className="mr-2">
        {prefix}
      </div>
      <div className="whitespace-pre-wrap flex flex-col chatbubble_container">
        <div className="flex flex-col chatbubble_child chatbubble_answer">{props.message.content}</div>
        {props.sources && props.sources.length ? <>
          <div className="flex flex-col chatbubble_child wordwrap">
            <br/><br/>
            <h6>
              🔍 Les Sources:
            </h6>
            {props.sources?.map((source, i) => (
              <div className="mt-2" key={"source:" + i}>
                {i + 1}.{
                  <span>&nbsp;&nbsp;{source.title}<br/>
                  <a target="_blank" href={source.url} rel="noopener noreferrer">{source.url}</a>
                  </span>
                }
              </div>
            ))}
          </div>
        </> : ""}
      </div>
    </div>
  );
}