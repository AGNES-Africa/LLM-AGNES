"use client";

import "./globals.css";
import { Public_Sans } from "next/font/google";
import {Providers} from "./providers";
import NavBar from "@/components/NavBar";
import 'bootstrap/dist/css/bootstrap.min.css';
import { Container, Row} from "reactstrap";

const publicSans = Public_Sans({ subsets: ["latin"] });

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <title>Climate Action AI</title>
        <link rel="shortcut icon" href="climate_action-ai-logo-small.png" />
      </head>
      <body>
      <Providers>
      <Container>
        <Row>
          <NavBar/>
        </Row>
        <Row className="mt-2">
          {children}
        </Row>
      </Container>
      </Providers>
      </body>
    </html>
  );
}
