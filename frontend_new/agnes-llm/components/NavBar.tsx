"use client";

import React from "react";
import {Navbar, NavbarBrand, NavbarContent, NavbarItem, Link, Button, DropdownItem, DropdownTrigger, Dropdown, DropdownMenu} from "@nextui-org/react";
import Image from "next/image";
import {ChevronDown, Search, Flash} from "./Icons.jsx";
import { useRouter, usePathname } from 'next/navigation';
import "flag-icons/css/flag-icons.min.css";

export default function NavBar() {
  const router = useRouter();
  const pathname = usePathname();

  const flags = {
    uk: <span className="fi fi-gb"></span>,
    fr: <span className="fi fi-fr"></span>
  };

  const icons = {

    chevron: <ChevronDown 
      fill="currentColor"
      height={16}
      width={16}
      size={16} 
    />,
    
    search: <Search 
      className="text-success"
      fill="currentColor"
      width={90} 
    />,

    flash: <Flash 
      className="text-primary" 
      fill="currentColor" 
      size={18}
      height={18}
      width={18}
    />,
  };

  const navigation = (key:any) => {
    if (key == "browse"){
      if (!pathname.includes('corpus')){
        router.push('/corpus')
      }   
    }
    else{
      router.push('/latest_articles')
    }
  }

  const set_lang = (key:any) => {
    if (key == "english"){
      router.push('/')
    }
    else{
      router.push('/?lang=fr')
    }
  }

  return (
    <Navbar className='light' maxWidth={'full'}>
      <NavbarBrand>
        <Image
          src="/climate_action-ai-logo.png"
          alt="Agnes Logo"
          width={350}
          height={80}
        />
      </NavbarBrand>
      <NavbarContent className="hidden md:flex gap-2 mt-3" justify="center">
        <NavbarItem isActive>
          <Button as={Link} color="primary" href="/" variant="flat" size="sm" className="askai">
            Home
          </Button>
        </NavbarItem>
        <Dropdown className="gray askai">
          <NavbarItem>
            <DropdownTrigger>
              <Button
                endContent={icons.chevron}
                color="primary"
                variant="flat"
                size="sm"
                className="askai"
              >
                Browse Document Corpus
              </Button>
            </DropdownTrigger>
          </NavbarItem>
          <DropdownMenu
            aria-label="Browse Document Corpus"
            className="w-[340px] askai"
            itemClasses={{
              base: "gap-4",
            }}
            onAction={(key) => navigation(key)}
          >
            <DropdownItem
              key="browse"
              description="Browse the Climate Change Documents queried by the AI."
              startContent={icons.search}
            >
              Browse Document Corpus
            </DropdownItem>
            <DropdownItem
              key="latest"
              description="View the latest Documents added to the Document Corpus."
              startContent={icons.flash}
            >
              Latest Documents
            </DropdownItem>
          </DropdownMenu>
        </Dropdown>
        <Dropdown className="gray askai">
          <NavbarItem>
            <DropdownTrigger>
              <Button
                endContent={icons.chevron}
                color="primary"
                size="sm"
                className="askai"
              >
                Select Language
              </Button>
            </DropdownTrigger>
          </NavbarItem>
          <DropdownMenu
            aria-label="Language"
            className="w-[340px] askai"
            itemClasses={{
              base: "gap-4",
            }}
            onAction={(key) => set_lang(key)}
          >
            <DropdownItem key="english" startContent={flags.uk}>English (Default)</DropdownItem>
            <DropdownItem key="french" startContent={flags.fr}>French</DropdownItem>
          </DropdownMenu>
        </Dropdown>
      </NavbarContent>
    </Navbar>
  );
}