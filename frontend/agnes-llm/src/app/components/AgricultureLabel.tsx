import React from "react";
import Image from "next/image";

export default function AgricultureLabel ({name}:any){
  return <div>
    <Image
          src="/agriculture-icon.png"
          alt="Agnes Logo"
          width={50}
          height={60}
    />
    <br/>
    <h6>{name}</h6>
  </div>;
}