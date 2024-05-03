import { ChatWindow } from "@/components/ChatWindow";
import Image from "next/image";

export default function Home() {
  const InfoCard = (
    <div className="p-4 md:p-8 rounded bg-[#25252d] w-full max-h-[85%] overflow-hidden gray2">
       <Image
          src="/agnes-logo.png"
          alt="Agnes Logo"
          width={200}
          height={30}
        ></Image>
      <ul className="mt-2">
        <li className="text-l">
          ◉
          <span className="ml-2 text-sm">
            This is a Large Language Model intended to support Climate Change Negotiators.
          </span>
        </li>
        <li className="text-l">
          ◉
          <span className="ml-2 text-sm">
            With a specific focus on African negotiators, the goal of this project is to provide negotiators with the most pertinent information at their fingertips, in real-time, enhancing their performance at SB60, COP 29 and beyond.
          </span>
        </li>
        <li className="text-l">
          ◉
          <span className="ml-2 text-sm">
            This model runs queries against a curated corpus of Climate Change Documents. The corpus of Documents can be accessed here.
          </span>
        </li>
        <li className="text-l">
          ◉
          <span className="ml-2 text-sm">
            The model generates relevant responses to specific queries with line of sight to the underlying Climate Change literature.
          </span>
        </li>
        <li className="text-l">
          ◉
          <span className="ml-2 text-sm">
            To use the model, type a question into the dialog box, and press the 'Ask AI' button.
          </span>
        </li>
      </ul>
    </div>
  );
  return (
    <ChatWindow
      endpoint="api/chat"
      emoji="🏴‍☠️"
      titleText="Patchy the Chatty Pirate"
      placeholder="Type your question here"
      emptyStateComponent={InfoCard}
    ></ChatWindow>
  );
}
