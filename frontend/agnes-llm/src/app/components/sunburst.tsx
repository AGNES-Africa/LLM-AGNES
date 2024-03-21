"use client";

import Sunburst from 'sunburst-chart';
import React, { useRef, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import parse from 'html-react-parser';

export default function AgnesSunburstChart() {
  const sunburstDiv = useRef(null);
  let [node_stack, setNodeStack] = useState(`<div class='breadcrumb flat'>
    <a class='drop-container'>
      Climate Action Streams
    </a>
  </div>`)
  const [data, setData] = useState(null);
  const [isLoading, setLoading] = useState(true);
  const router = useRouter();

  const getNodeStack = (d:any) => {
    var stack = [];
    var curNode = d;
    while (curNode) {
      if(curNode.data){
        stack.unshift("<a>"+curNode.data.name+"</a>");
      }
      curNode = curNode.parent;
    }
    return "<div class='breadcrumb flat'>"+stack.join("")+"</div>";
  };

  useEffect(() => {
    fetch('http://localhost:8000/api/db_hierarchy')
      .then((res) => res.json())
      .then((data:any) => {
        setData(data)
        setLoading(false)

        data[0]["color"] = '#176857'
        data[1]["color"] = '#213f7f'
        data[2] = {"name": "Finance", color:"#8e5fa8", size:3}
        data[3] = {"name": "Stream", color:"#818EA8", size:2}

        const data1 = {
          "name": 'Climate Action Streams', color : '#1C2F3F', //'#0063db',
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
              const data_node = node.__dataNode
              node_stack = getNodeStack(data_node)
              setNodeStack(node_stack)
              console.log(node_stack)
              if(node.children == null){
                if (data_node != null){
                  const stream_id = data_node?.parent?.parent?.id
                  router.push('/category/'+stream_id+'/'+node.id)
                }
              }
              else{
                sunburst.focusOnNode(node)
              }
            }
          })
          (sunburstDiv.current!);
      })
  }, [sunburstDiv]);
  return <div>
    <div className="flex flex-col flex-wrap gap-4 text-sm">
      {parse(node_stack)}
    </div>
    <div className="flex flex-col flex-wrap" id="sunburst-chart" ref={sunburstDiv}></div>
  </div>;
}