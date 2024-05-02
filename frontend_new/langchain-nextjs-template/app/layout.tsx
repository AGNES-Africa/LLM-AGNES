import "./globals.css";
import { Public_Sans } from "next/font/google";
import {Providers} from "./providers";
import NavBar from "@/components/NavBar";
import Starfield from "@/components/AnimatedBackground";
import 'bootstrap/dist/css/bootstrap.min.css';
import { Container, Row, Col } from "reactstrap";

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
        <link rel="shortcut icon" href="llm_logo.png" />
        <meta
          name="description"
          content="Starter template showing how to use LangChain in Next.js projects. See source code and deploy your own at https://github.com/langchain-ai/langchain-nextjs-template!"
        />
        <meta property="og:title" content="LangChain + Next.js Template" />
        <meta
          property="og:description"
          content="Starter template showing how to use LangChain in Next.js projects. See source code and deploy your own at https://github.com/langchain-ai/langchain-nextjs-template!"
        />
        <meta property="og:image" content="/images/og-image.png" />
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content="LangChain + Next.js Template" />
        <meta
          name="twitter:description"
          content="Starter template showing how to use LangChain in Next.js projects. See source code and deploy your own at https://github.com/langchain-ai/langchain-nextjs-template!"
        />
        <meta name="twitter:image" content="/images/og-image.png" />
      </head>
      <body className="light bg-gradient-to-tr from-black to-blue-300 text-white shadow-lg">
      <Providers>
      <Container>
      <Starfield
        starCount={1000}
        starColor={[255, 255, 255]}
        speedFactor={0.05}
        backgroundColor="black"
      />
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
