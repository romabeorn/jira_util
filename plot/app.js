var dataJSON = {}

function getColor(id) {
    id = parseInt(id);

    switch (id) {
        case 1:
            return "#c85656";
            break;

        case 2:
            return "#fa9722";
            break;

        case 3:
            return "#23a1c4";
            break;

        case 4:
            return "#339219";
            break;

        case 5:
            return "#8adc74";
            break;
    }
}

function getRandomColor() {
    var letters = '0123456789ABCDEF';
    var color = '#';
    for (var i = 0; i < 6; i++) {
        color += letters[Math.floor(Math.random() * 16)];
    }
    return color;
}

var ctx = document.getElementById("myChart").getContext('2d');


function getDataFromServer() {

    // let data = {
    // 	message: 'Hello, Roman! Please, send me json data of your bugs... =)'
    // }

    $.ajax({
        type: "GET",
        url: "http://localhost:8000/plot/bigData.json"
    }).done(function(data) {
        console.log(data)

        if (data != null) {
            dataJSON = JSON.parse(data);
            console.log
            var resultMass = []

            for (let i = 0; i < dataJSON.BigData.length; i++) {

                var data = [];
                var color = getColor(dataJSON.BigData[i].issueProps.priorityId);

                for (let j = 0; j < dataJSON.BigData[i].versions.length; j++) {
                    if (dataJSON.BigData[i].versions[j].visible) {
                        data.push({
                            x: dataJSON.BigData[i].versions[j].name,
                            y: dataJSON.BigData[i].id,
                            desc: "description of the bug",
                            status: "status"
                        })
                    } else {
                        data.push({})
                    }
                }

                resultMass.push({
                    data: data,

                    label: dataJSON.BigData[i].bugName,
                    issueProps: dataJSON.BigData[i].issueProps,

                    borderColor: (dataJSON.BigData[i].issueProps.statusId === "6") ? "#000000d6" : color,
                    backgroundColor: color,
                    hoverBackgroundColor: color,
                    radius: 6,
                    hoverRadius: 10,
                    fill: false
                })
            }

            var myChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: dataJSON.Labels,
                    datasets: resultMass
                },
                options: {
                    title: {
                        display: true,
                        fontSize: 25,
                        text: `Analysing bug's statuses in Test Runs (JIRA Structure)`
                    },
                    scales: {
                        yAxes: [{
                            ticks: {
                                min: 0,
                                // max: 100,
                                stepSize: 1,
                                suggestedMin: 0.5,
                                suggestedMax: 5.5,
                                callback: function(label, index, labels) {
                                    if (label == 0) {
                                        return 'BEGIN'
                                    }
                                    return dataJSON.BigData[label - 1].bugName;
                                }
                            }
                        }]
                    },
                    tooltips: {
                        bodyFontColor: "#000000", //#000000
                        bodyFontSize: 15,
                        bodyFontStyle: "bold",
                        bodyFontColor: '#FFFFFF',
                        bodyFontFamily: "'Helvetica', 'Arial', sans-serif",
                        footerFontSize: 20,

                        callbacks: {
                            label: function(tooltipItem, data) {
                                var value = data.datasets[0].data[tooltipItem.index];

                                var message = ``;

                                if (tooltipItem.index == 0) {
                                    return message;
                                } else if (tooltipItem.index == 1) {
                                    return message;
                                } else if (tooltipItem.index == 2) {
                                    return message;
                                } else {
                                    return message;
                                }
                            },
                            title: function(tooltipItems, data) {
                                //Return value for title

                                var name = data.datasets[tooltipItems[0].datasetIndex].issueProps.name;
                                var title = data.datasets[tooltipItems[0].datasetIndex].issueProps.summary;

                                return tooltipItems[0].xLabel + " | " + name + " | " + title;
                            },
                            afterLabel: function(tooltipItem, data) {

                                console.log(data.datasets[tooltipItem.datasetIndex])
                                // Description: \n${data.datasets[tooltipItem.datasetIndex].issueProps.description}
                                var tooltipText =
                                    `Condition: ${data.datasets[tooltipItem.datasetIndex].issueProps.issuetype}
                                    \nStatus: ${data.datasets[tooltipItem.datasetIndex].issueProps.status}
                                    \nPriority: ${data.datasets[tooltipItem.datasetIndex].issueProps.priority}
                                    \nCreator: ${data.datasets[tooltipItem.datasetIndex].issueProps.creator}
                                    \nAssignee: ${data.datasets[tooltipItem.datasetIndex].issueProps.assignee}`

                                return tooltipText;
                            }
                        }
                    }
                }
            })

        } else {
            alert('data is not definded....')
        }
    });
}


window.onload = function() {
    getDataFromServer()
}




var labels = ['VM 1.0.0', 'VM 1.0.1', 'VM 1.0.2', 'VM 1.0.3', 'VM 1.0.4', 'VM 1.1.0', 'VM 1.1.1', 'VM 1.1.2', 'VM 1.1.3', 'VM 1.1.4', 'VM 1.1.5'];

var dataSet = [{
        data: [{},
            {
                x: 'VM 1.0.1',
                y: 1
            }, {
                x: 'VM 1.0.2',
                y: 1
            }, {
                x: 'VM 1.0.3',
                y: 1
            },
            {},
            {},
            {
                x: 'VM 1.1.1',
                y: 1
            },
            {},
            {
                x: 'VM 1.1.3',
                y: 1
            }

        ],

        label: "BUG 1",
        borderColor: "#3e95cd",
        backgroundColor: "#3e95cd",
        hoverBackgroundColor: "lightgreen",
        radius: 6,
        hoverRadius: 10,
        fill: false
    },

    {
        data: [{
            x: 'VM 1.0.1',
            y: 2
        }, {
            x: 'VM 1.0.2',
            y: 2
        }, {
            x: 'VM 1.0.4',
            y: 2
        }],
        label: "BUG 2",
        borderColor: "#8e5ea2",
        backgroundColor: "#8e5ea2",
        radius: 6,
        hoverRadius: 10,
        fill: false
    },

    {
        data: [{
                x: 'VM 1.1.1',
                y: 2
            }, {
                x: 'VM 1.1.2',
                y: 2
            }, {
                x: 'VM 1.1.3',
                y: 2
            }, {
                x: 'VM 1.1.4',
                y: 2
            },
            null,
            null,
            {
                x: 'VM 1.1.7',
                y: 2
            },

        ],
        label: "BUG 2",
        borderColor: "#8e5ea2",
        backgroundColor: "#8e5ea2",
        radius: 6,
        hoverRadius: 10,
        fill: false
    },
    {
        data: [{
            x: 'VM 1.0.4',
            y: 3
        }, {
            x: 'VM 1.1.0',
            y: 3
        }, {
            x: 'VM 1.1.1',
            y: 3
        }, {
            x: 'VM 1.1.2',
            y: 3
        }],
        label: "BUG 3",
        borderColor: "#ff0016",
        backgroundColor: "#ff0016",
        radius: 6,
        hoverRadius: 10,
        fill: false
    }
]