import React from "react";
import {Navbar, NavbarBrand, NavbarContent, NavbarItem, Link} from "@nextui-org/react";
import Image from "next/image";
import SearchBox from "./SearchBox";

export default function NavBar() {
  return (
    <Navbar>
      <NavbarBrand>
        <a href="/">
          <Image
            src="/climate_action-ai-logo.png"
            alt="Climate Action AI Logo"
            width={265}
            height={40}
            priority
          />
        </a>
      </NavbarBrand>
      <NavbarContent className="hidden sm:flex gap-6">
        <NavbarItem isActive>
          <Link href="/" aria-current="page">
            Home
          </Link>
        </NavbarItem>
        <NavbarItem>
          <Link href="#" color="foreground">
            About
          </Link>
        </NavbarItem>
        <NavbarItem>
          <SearchBox/>
        </NavbarItem>
      </NavbarContent>
    </Navbar>
  );
}