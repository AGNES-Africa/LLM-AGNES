"use client"

import React, { useState, useEffect, useRef } from 'react';
import HighchartsReact from 'highcharts-react-official';
import Highcharts from 'highcharts';
import HighchartsSunburst from 'highcharts/modules/sunburst';
import { renderToStaticMarkup } from "react-dom/server";
import ClimateActionLabel from "./ClimateActionLabel";
import AgricultureLabel from "./AgricultureLabel";
import GeneralLabel from "./GeneralLabel";

HighchartsSunburst(Highcharts);

export default function SunburstChart(){
    const [data, set_data] = useState([{
        id: '0.0',
        parent: '',
        name: 'Streams'
    }])

    let sunburst_icon = null

    const sunburstDiv = useRef(null);

    useEffect(() => {
        fetch('http://localhost:8000/api/db_hierarchy')
          .then((res) => res.json())
          .then((data:any) => {
            let arr = [{
                id: '0',
                parent: '',
                name: 'Climate Action Streams'
            }]

            for (let i = 0; i < data.length; i++) {
                arr.push({
                    id: (i+1).toString(),
                    parent: '0',
                    name: data[i].name
                })
                for (let j = 0; j < data[i].children.length; j++) {
                    arr.push({
                        id: (i+1) + "." + (j+1),
                        parent: (i+1).toString(),
                        name: ((data[i].children)[j]).name
                    })

                    for (let k = 0; k < data[i].children[j].children.length; k++) {
                        arr.push({
                            id: (i+1) + "." + (j+1) + "." + (k+1),
                            parent: (i+1) + "." + (j+1),
                            name: (((data[i].children)[j]).children[k]).name,
                            value: 10
                        })
                    }
                }
            }
            set_data(arr)
        })
    }, []);

    const chartOptions = {
        credits: {
            enabled: false
        },
        visibleLevels: {
            from: 0,
            to: 3
        },
        chart: {
            height: '55%',
            backgroundColor: 'transparent'
        },
        shadow: true,
        colors: ['transparent'].concat(Highcharts.getOptions().colors),
        title: {
            text: ''
        },
        levelSize: 1,
        series: [{
            type: 'sunburst',
            data: data,
            dataLabels: {
                useHTML: true,
                enabled: true,
                formatter: function () {
                    if (this.point.name == "Climate Action Streams"){
                        return renderToStaticMarkup(<ClimateActionLabel name={this.point.name} />);
                    }
                    if (this.point.name == "Agriculture"){
                        return renderToStaticMarkup(<AgricultureLabel name={this.point.name} />);
                    }
                    return renderToStaticMarkup(<GeneralLabel name={this.point.name} />);
                }
            },
            name: 'Root',
            allowDrillToNode: true,
            borderRadius: 3,
            cursor: 'pointer',
            point: {
                events: {
                    click: function(e) {
                        var chart = this.series.chart;
                        if((e.point.id == '1') || (e.point.id == '2') || (e.point.id == '3') || (e.point.id == '4')){
                            triggerLevel(3, chart)
                        }
                        else if(e.point.id.split(".").length == 2) {
                            triggerLevel(4, chart)
                        }
                    }
                }
            },
            levels: [{
                level: 1,
                levelSize: {
                    value: 1
                },
                levelIsConstant: false,
                dataLabels: {
                    filter: {
                        property: 'outerArcLength',
                        operator: '>',
                        value: 64
                    }
                }
            }, {
                level: 2,
                colorByPoint: true,
                levelSize: {
                    value: 1
                }
        
            }, {
                level: 3,
                colorVariation: {
                    key: 'brightness',
                    to: -0.5
                },
                hidden: true,
                levelSize: {
                    value: 0
                },
                dataLabels:{
                    enabled:false
                }
            }, {
                level: 4,
                hidden: true,
                levelSize: {
                    value: 0
                },
                dataLabels:{
                    enabled:false
                }
            }]
        }],
        tooltip: {
            enabled: false
        },
        navigation: {
            breadcrumbs: {
                showFullPath: false,
                position:{
                    align: 'left'
                },
                buttonTheme: {
                    fill: '#f7f7f7',
                    padding: 8,
                    stroke: '#cccccc',
                    'stroke-width': 1
                },
                events: {
                    click: function(e,br) {
                        var chart = this.chart;
                        setTimeout(function () {
                            if(e.newLevel == 1){
                                showLevel(2, chart)
                                hideLevel(3, chart)
                                hideLevel(4, chart)
                            }
                            if(e.newLevel == 2){
                                showLevel(3, chart)
                                hideLevel(4, chart)
                            }
                            if(e.newLevel == 3){
                                    //open list
                            }
                        }, 100);
                    }
                }
            }
        }
    }

    function onRender(chart) {
        //pass
    };

    function showLevel(levelId, chart) {
        var id = levelId 
        var levels = chart.userOptions.series[0].levels // Whole levels object
        var level = levels.filter(elem => { // Find level to hide
            return elem.level === levelId
        })
        var index = levels.indexOf(level[0]) // Get index of level
        var newLevelOptions;
        
        level[0].hidden = false // set flag
        newLevelOptions = Object.assign({}, level[0], { // Merge specific level options
            levelSize: {
                value: 1
            },
            dataLabels: Object.assign({}, level[0].dataLabels, {
                enabled: true
            })
        })
        
        levels[index] = newLevelOptions // Assign new options
        
        chart.series[0].update({ // Update chart levels
            levels: levels
        })
    }

    function hideLevel(levelId, chart) {
        //console.log(levelId)
        //console.log(chart)
        var id = levelId // Level that you want to hide
        var levels = chart.userOptions.series[0].levels // Whole levels object
        var level = levels.filter(elem => { // Find level to hide
            return elem.level === levelId
        })
        var index = levels.indexOf(level[0]) // Get index of level to hide
        var newLevelOptions;
        
        level[0].hidden = true // set flag
        newLevelOptions = Object.assign({}, level[0], {
            levelSize: {
                value: 0
            },
            dataLabels: Object.assign({}, level[0].dataLabels, {
                enabled: false
            })
        })
        
        levels[index] = newLevelOptions // Assign new options
        chart.series[0].update({ // Update chart levels
            levels: levels
        })
    }
      
    function triggerLevel(levelId, chart, alternate=true) {
        //console.log(levelId)
        //console.log(chart)
        var id = levelId // Level that you want to hide
        var levels = chart.userOptions.series[0].levels // Whole levels object
        var level = levels.filter(elem => { // Find level to hide
            return elem.level === levelId
        })
        var index = levels.indexOf(level[0]) // Get index of level to hide
        var newLevelOptions;
        
        if (level[0].hidden) { // if level is hidden
            level[0].hidden = false // set flag
            newLevelOptions = Object.assign({}, level[0], { // Merge specific level options
                levelSize: {
                    value: 1
                },
                dataLabels: Object.assign({}, level[0].dataLabels, {
                    enabled: true
                })
            })
        } else { // If level is visible
            if (alternate){
                level[0].hidden = true // set flag
                newLevelOptions = Object.assign({}, level[0], {
                    levelSize: {
                        value: 0
                    },
                    dataLabels: Object.assign({}, level[0].dataLabels, {
                        enabled: false
                    })
                })
            }
        }
        
        levels[index] = newLevelOptions // Assign new options
        chart.series[0].update({ // Update chart levels
            levels: levels
        })
    }

    return (
          <div className='light'>
            <HighchartsReact
              highcharts={Highcharts}
              options={chartOptions}
              callback = {onRender}
              webviewStyles={{backgroundColor: 'transparent'}}
            />
          </div>
    )

}