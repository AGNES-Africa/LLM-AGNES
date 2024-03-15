"use client";

import React, { useEffect, useState, useRef } from 'react';
import {Card, CardBody} from "@nextui-org/react";

export default function ArticleView({article_id}:any) {
  const [isLoading, setIsLoading] = React.useState(true);
  const [data, setData] = useState(null);
  const articleDiv = useRef(null);

  useEffect(() => {
    fetch('http://localhost:8000/api/article/'+article_id)
    .then((res) => res.json())
    .then((data:any) => {
      setData(data)
    })
  });

  return (
    <Card id="sunburst-chart">
      <CardBody>
        <p></p>
      </CardBody>
    </Card>
  );
}
