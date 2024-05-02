"use client"

import React, { useState, useEffect, useRef } from 'react';
import HighchartsReact from 'highcharts-react-official';
import Highcharts from 'highcharts';
import HighchartsSunburst from 'highcharts/modules/sunburst';
import { useRouter } from 'next/navigation';
import { useSearchParams } from 'next/navigation'

HighchartsSunburst(Highcharts);

export default function SunburstChart(){
    const [data, set_data] = useState([{
        id: '0.0',
        parent: '',
        name: 'Streams'
    }])
    const router = useRouter();

    const search_params = useSearchParams()
    const root_node = search_params.get('back_link') // Logs "search"
    const highcharts_colors:any = Highcharts.getOptions().colors

    useEffect(() => {
        const fetchData = async () => {
            const data = await fetch('https://agnes-llm-backend.azurewebsites.net/api/db_hierarchy', {
                method: "GET",
                headers: {
                    accept: "application/json",
                },
            })
            .then((res) => res.json())
            .then((data:any) => {
                let arr:any = [{
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
                                value: (((data[i].children)[j]).children[k]).size,
                                stream_id: i+1,
                                category_id: (((data[i].children)[j]).children[k]).id
                            })
                        }
                    }
                }
                set_data(arr)
            })
        return data
        }
        fetchData();
    }, []);

    const chartOptions:any = {
        credits: {
            enabled: false
        },
        visibleLevels: {
            from: 0,
            to: 3
        },
        chart: {
            height: '55%',
            backgroundColor: 'transparent',
            events: {
                load(this, e:any) {
                    //e.preventDefault()
                    console.log("load")
                },
                redraw(this, e:any) {
                    //e.preventDefault()
                    console.log("redraw")
                },
                render(this, e:any) {
                    //e.preventDefault()
                    console.log("render")
                },
            }
        },
        shadow: true,
        colors: ['transparent'].concat(highcharts_colors),
        title: {
            text: ''
        },
        levelSize: 1,
        series: [{
            type: 'sunburst',
            data: data,
            dataLabels: {
                useHTML: false,
                enabled: true
            },
            name: 'Root',
            allowDrillToNode: true,
            borderRadius: 3,
            cursor: 'pointer',
            point: {
                events: {
                    click: function(e:any) {
                        var chart = e.point.series.chart
                        if((e.point.id == '1') || (e.point.id == '2') || (e.point.id == '3') || (e.point.id == '4')){
                            triggerLevel(3, chart)
                        }
                        else if(e.point.id.split(".").length == 2) {
                            triggerLevel(4, chart)
                        }
                        else if(e.point.id.split(".").length == 3) {
                            router.push('/category/'+e.point.stream_id+'/'+e.point.category_id+'/'+e.point.id);
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
                    align: 'left',
                    x: 225
                },
                buttonTheme: {
                    fill: '#f7f7f7',
                    padding: 8,
                    stroke: '#cccccc',
                    'stroke-width': 1
                },
                events: {
                    click: function(br:any, e:any) {
                        var chart = e.levelOptions.point.series.chart;
                        setTimeout(function () {
                            if(br.newLevel == 1){
                                showLevel(2, chart)
                                hideLevel(3, chart)
                                hideLevel(4, chart)
                            }
                            if(br.newLevel == 2){
                                showLevel(3, chart)
                                hideLevel(4, chart)
                            }
                            if(br.newLevel == 3){
                            }
                        }, 100);
                    }
                }
            }
        }
    }
    
    function onRender(chart:any, e:any) {
        if(root_node != null){
            chart.showLoading();
            setTimeout(function(){
                if (chart.hasOwnProperty("series")){
                    let series = chart.series[0]
                    console.log(series)
                    if ((root_node === '1') || (root_node === '2') || (root_node === '3')){
                        series.setRootNode(root_node)
                        showLevel(3, chart)
                    }
                    else{
                        series.setRootNode(root_node)
                        showLevel(3, chart)
                        showLevel(4, chart)
                    }
                }
                chart.hideLoading();
            },3500)
        }
    };

    function showLevel(levelId:any, chart:any) {
        var id = levelId

        if (chart.hasOwnProperty('userOptions')){
            if (chart.userOptions.hasOwnProperty("series")){
                var levels = chart.userOptions.series[0].levels // Whole levels object
                var level = levels.filter((elem: { level: any; }) => { // Find level to hide
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
        }
    }

    function hideLevel(levelId:any, chart:any) {
        var id = levelId // Level that you want to hide
        if (chart.hasOwnProperty('userOptions')){
            if (chart.userOptions.hasOwnProperty("series")){
                var levels = chart.userOptions.series[0].levels // Whole levels object
                var level = levels.filter((elem: { level: any; }) => { // Find level to hide
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
        }
    }
      
    function triggerLevel(levelId:any, chart:any, alternate=true) {
        var id = levelId // Level that you want to hide

        if (chart.hasOwnProperty('userOptions')){
            if (chart.userOptions.hasOwnProperty("series")){
        
                var levels = chart.userOptions.series[0].levels // Whole levels object
                var level = levels.filter((elem: { level: any; }) => { // Find level to hide
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
        }
    }

    return (
          <div className='light'>
            <HighchartsReact
              highcharts={Highcharts}
              options={chartOptions}
              callback = {onRender}
              allowChartUpdate = { true }
              webviewStyles={{backgroundColor: 'transparent'}}
            />
          </div>
    )

}