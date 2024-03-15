"use client";

import Sunburst from 'sunburst-chart';
import React, { useRef, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import {Breadcrumbs, BreadcrumbItem} from "@nextui-org/react";
const d3 = require('d3');

export default function AgnesSunburstChart() {
  const sunburstDiv = useRef(null);
  const [data, setData] = useState(null);
  const [isLoading, setLoading] = useState(true);
  const router = useRouter();

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
              console.log(data_node)
              if(node.children == null){
                if (data_node != null){
                  const stream_id = data_node?.parent?.parent?.id
                  //router.push('/category/'+stream_id+'/'+node.id)
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
    <div className="flex flex-col flex-wrap gap-4">
      <Breadcrumbs>
        <BreadcrumbItem>Climate Action Streams</BreadcrumbItem>
        <BreadcrumbItem>Agriculture</BreadcrumbItem>
        <BreadcrumbItem>UNFCCC Resources</BreadcrumbItem>
      </Breadcrumbs>
    </div>
    <div id="sunburst-chart" ref={sunburstDiv}></div>
  </div>;
}