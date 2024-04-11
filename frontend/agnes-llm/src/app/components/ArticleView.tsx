import React, { useState, useEffect } from 'react';
import {Card, CardHeader, CardBody, CardFooter, Divider, Link as UILink} from "@nextui-org/react";
import { Container, Row, Col } from "reactstrap";
import Link from 'next/link';
import { useRouter } from 'next/navigation'

export default function ArticleView({article_id}:any) {
  const [data, set_data] = useState({
    name: "",
    condensed_summary: "",
    category: "",
    negotiation_stream:"",
    negotiation_stream_id:"",
    summary:"",
    created_at:"",
    url:""
  })

  const router = useRouter();

  useEffect(() => {
    fetch('http://localhost:8000/api/article/'+article_id)
      .then((res) => res.json())
      .then((data:any) => {
        set_data(data)
    })
  }, []);

  return (
          <Card className="max-w-[1000px] center mt-10">
            <CardHeader className="flex gap-3">
              <Container className="flex flex-col">
                <Row>
                  <Col>
                    <nav className="breadcrumbs">
                      <Link href={{
                        pathname: '/',
                        query: {
                          back_link: data.negotiation_stream_id
                        }
                      }} className="breadcrumbs__item">
                        ← {data.negotiation_stream}
                      </Link>
                      <a onClick={() => router.back()} className="breadcrumbs__item">
                        ← {data.category}
                      </a>
                    </nav>
                  </Col>
                </Row>
                <Row>
                  <Col className="col-2 fontsmall"><b>Document Title:</b></Col>
                  <Col className="col-10 fontsmall">{data.name}</Col>
                </Row>
                <Row>
                  <Col className="col-2 fontsmall"><b>Negotiation Stream:</b></Col>
                  <Col className="col-10 fontsmall">{data.negotiation_stream}</Col>
                </Row>
                <Row>
                  <Col className="col-2 fontsmall"><b>Category:</b></Col>
                  <Col className="col-10 fontsmall">{data.category}</Col>
                </Row>
                <Row>
                  <Col className="col-2 fontsmall"><b>Created Date:</b></Col>
                  <Col className="col-10 fontsmall">{data.created_at}</Col>
                </Row>
              </Container>
            </CardHeader>
            <Divider/>
            <CardBody>
              <Container className="flex flex-col">
                <Row>
                    <Col className="col-12 fontsmall">
                    <p className="fontsmall">
                      <b>Summary</b>
                      <br/><br/>
                      {data.summary}
                    </p>
                    </Col> 
                </Row>
              </Container>
            </CardBody>
            <Divider/>
            <CardFooter>
              <UILink
                className="fontsmall"
                isExternal
                showAnchorIcon
                href={data.url}
              >
                Visit Document on {(data.category).split("-")[0]} Site
              </UILink>
            </CardFooter>
          </Card>
  );
}