import React from "react";
import Image from "next/image";

export default function ClimateActionLabel ({name}:any){
  return <div>
    <Image
          src="/climate_action-icon.png"
          alt="Agnes Logo"
          width={130}
          height={60}
    />
    <br/>
    <h6>{name}</h6>
  </div>;
}