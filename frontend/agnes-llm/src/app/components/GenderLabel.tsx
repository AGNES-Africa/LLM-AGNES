import React from "react";
import Image from "next/image";

export default function GenderLabel ({name}:any){
  return <div>
    <Image
          src="/gender-icon.png"
          alt="Agnes Logo"
          width={50}
          height={60}
    />
    <br/>
    <h6>{name}</h6>
  </div>;
}