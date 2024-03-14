"use client";

import Sunburst from 'sunburst-chart';
import React, { useRef, useEffect, useState } from 'react';
const d3 = require('d3');

export default function AgnesSunburstChart() {
  const sunburstDiv = useRef(null);
  const [data, setData] = useState(null)
  const [isLoading, setLoading] = useState(true)

  useEffect(() => {
    fetch('http://localhost:8000/api/db_hierarchy')
      .then((res) => res.json())
      .then((data:any) => {
        setData(data)
        setLoading(false)

        data[0]["color"] = '#27563B'
        data[1]["color"] = '#D1A79B'
        data[2] = {"name": "Finance", color:"#38225B", size:6}
        data[3] = {"name": "Stream", color:"#818EA8", size:6}

        const data1 = {
          "name": 'Negotiation Streams', color : '#1C2F3F', //'#0063db',
          "children" : data 
        }
       
        const sunburst = Sunburst()
          .data(data1)
          .label('name')
          .labelOrientation('angular')
          .color('color')
          .size('size')
          .maxLevels(2)
          .radiusScaleExponent(1)
          .onClick((node) => {
            if (node != null){
              if(node.children == null){
                console.log("None")
              }
              else{
                sunburst.focusOnNode(node)
              }
            }
          })
          (sunburstDiv.current!);
      })
  }, [sunburstDiv]);
  return <div><div id="sunburst-chart" ref={sunburstDiv}></div></div>;
}