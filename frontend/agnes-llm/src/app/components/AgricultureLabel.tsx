import React, { Component } from "react";
import Image from "next/image";

class AgricultureLabel extends Component {
  render() {
    return <div>
      <Image
            src="/agriculture-icon.png"
            alt="Agnes Logo"
            width={50}
            height={60}
      />
      <br/>
      {this.props.name}
    </div>;
  }
}
export default AgricultureLabel;