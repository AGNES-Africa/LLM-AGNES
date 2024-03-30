import React from "react";
import {Navbar, NavbarBrand, NavbarContent, NavbarItem, Link, Button} from "@nextui-org/react";
import Image from "next/image";
import {SearchIcon} from './SearchIcon';

export default function NavBar() {
  return (
    <Navbar className='light'>
      <NavbarBrand>
        <a href="/">
          <Image
            src="/agnes-logo.png"
            alt="Agnes Logo"
            width={180}
            height={60}
            className="mr-4"
          />
        </a>
        <a href="/">
          <Image
            src="/climate_action-ai-logo.png"
            alt="Agnes Logo"
            width={290}
            height={60}
          />
        </a>
      </NavbarBrand>
      <NavbarItem>
        <Button color="primary" size="sm" variant="shadow">
          Browse Latest Documents
        </Button>
      </NavbarItem>
      <NavbarItem>
        <Button color="primary" size="sm" variant="shadow" endContent={<SearchIcon/>}>
          Keyword Search
        </Button>
      </NavbarItem>
    </Navbar>
  );
}