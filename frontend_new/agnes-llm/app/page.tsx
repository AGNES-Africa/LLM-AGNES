'use client'

import { ChatWindow } from "@/components/ChatWindow";
import { ChatWindowFr } from "@/components/ChatWindowFr";
import Image from "next/image";
import { useSearchParams } from 'next/navigation'

export default function Home() {
  const searchParams = useSearchParams();
 
  const lang = searchParams.get('lang');
  if(!lang){
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
              This model runs queries against a curated corpus of Climate Change Documents. The corpus of Documents can be accessed <a href="/corpus/">here</a>.
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
              To use the model, type a question into the dialog box below, and press the 'Ask AI' button.
            </span>
          </li>
        </ul>
      </div>
    );
    return (
      <ChatWindow
        endpoint="api/chat"
        emoji="🤖"
        titleText="AGNES LLM"
        placeholder="Type your question here"
        emptyStateComponent={InfoCard}
      ></ChatWindow>
    );
  }
  else{
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
              Il s’agit d’un modèle de langage de grande taille destiné à soutenir les négociateurs sur le changement climatique.
            </span>
          </li>
          <li className="text-l">
            ◉
            <span className="ml-2 text-sm">
            Avec un accent particulier sur les négociateurs africains, l’objectif de ce projet est de fournir aux négociateurs les informations les plus pertinentes à portée de main, en temps réel, améliorant ainsi leurs performances à la SB60, à la COP 29 et au-delà.
            </span>
          </li>
          <li className="text-l">
            ◉
            <span className="ml-2 text-sm">
              Ce modèle exécute des requêtes sur un corpus organisé de documents sur le changement climatique. Le corpus de documents est accessible <a href="/corpus/">ici</a>.
            </span>
          </li>
          <li className="text-l">
            ◉
            <span className="ml-2 text-sm">
              Le modèle génère des réponses pertinentes à des requêtes spécifiques en lien avec la littérature sous-jacente sur le changement climatique.
            </span>
          </li>
          <li className="text-l">
            ◉
            <span className="ml-2 text-sm">
              Pour utiliser le modèle, saisissez une question dans la boîte de dialogue ci-dessous et appuyez sur le bouton 'Demander à l'IA'.
            </span>
          </li>
        </ul>
      </div>
    );
    return (
      <ChatWindowFr
        endpoint="api/chatFr"
        emoji="🤖"
        titleText="AGNES LLM"
        placeholder="Tapez votre question ici"
        emptyStateComponent={InfoCard}
      ></ChatWindowFr>
    );
  }
}
