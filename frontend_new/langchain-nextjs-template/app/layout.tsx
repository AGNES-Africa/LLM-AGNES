"use client";

import "./globals.css";
import { Public_Sans } from "next/font/google";
import {Providers} from "./providers";
import NavBar from "@/components/NavBar";
import Starfield from "@/components/AnimatedBackground";
import 'bootstrap/dist/css/bootstrap.min.css';
import { Container, Row} from "reactstrap";

import React, {useEffect, useState} from "react";
import Particles, {initParticlesEngine} from "@tsparticles/react";
import {loadFull} from "tsparticles";
const publicSans = Public_Sans({ subsets: ["latin"] });

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [init, setInit] = useState(false);

  useEffect(() => {
      if (init) {
          return;
      }

      initParticlesEngine(async (engine) => {
          await loadFull(engine);
      }).then(() => {
          setInit(true);
      });
  }, []);

  return (
    <html lang="en">
      <head>
        <title>Climate Action AI</title>
        <link rel="shortcut icon" href="llm_logo.png" />
      </head>
      <body>
      <Providers>
      <Container>
      <div className="gray">
        {init && <Particles options={
          {
            "background": {
              "color": "#282c34"
            },
            "particles": {
              "color": {
                "value": "#ffffff"
              },
              "links": {
                "color": "#ffffff",
                "distance": 150,
                "enable": true,
                "opacity": 0.09,
                "width": 1
              },
              "collisions": {
                "enable": true
              },
              "move": {
                "enable": true,
                "outModes": "bounce",
                "random": false,
                "speed": 6,
                "straight": false
              },
              "number": {
                "density": {
                  "enable": true
                },
                "value": 80
              },
              "opacity": {
                "value": 0.09
              },
              "shape": {
                "type": "circle"
              },
              "size": {
                "value": 5
              }
            }
          }
          
        }/>}
        <Row>
          <NavBar/>
        </Row>
        <Row className="mt-2">
          {children}
        </Row>
      </div>
      </Container>
      </Providers>
      </body>
    </html>
  );
}
