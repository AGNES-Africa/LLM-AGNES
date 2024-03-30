import React, { Component } from "react";
import Image from "next/image";

class ClimateActionLabel extends Component {
  render() {
    return <div>
      <Image
            src="/climate_action-icon.png"
            alt="Agnes Logo"
            width={130}
            height={60}
      />
      <br/>
      {this.props.name}
    </div>;
  }
}
export default ClimateActionLabel;