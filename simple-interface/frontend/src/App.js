import {
  Streamlit,
  StreamlitComponentBase,
  withStreamlitConnection,
} from "streamlit-component-lib"
import React, { Component } from 'react';
import Plot from 'react-plotly.js';
import { Timeline } from 'react-svg-timeline'

import 'bootstrap/dist/css/bootstrap.min.css';

import logo from './logo.svg';
import './App.css';

var eventsLaneId = 'events-lane'
var fragmentsLaneId = 'fragments-lane'
var videoLaneId = 'video-lane'

var signalLength = 1000;
var startSignalTime = 1167606000000 - 1000 * 60 * 60;
var componentWidth = 1200;


function getVerticalLine(currentTime, axis) {
  var yaxis = 'y' + (axis + 1)
  var line = {
    type: 'line',
    x: [currentTime, currentTime],
    y: [7, 5],
    xaxis: 'x',
    name: 'Position',
    mode: 'lines',
    line: {
      color: 'black',
      width: 3
    },
    showlegend: false
  }
  if (axis > 0) 
    line['yaxis'] = yaxis;
  return line
};


class App extends StreamlitComponentBase {
  constructor(props) {
    super(props);

    var videoPath = this.props.args.video;
    var signalReceived = this.props.args.signal;
    var events = this.props.args.events;

    this.state = {
      video: videoPath,
      currentTime: 0,
      signal: signalReceived,
      events: [{
        eventId: 'start',
        tooltip: 'Start',
        laneId: eventsLaneId,
        startTimeMillis: startSignalTime,
      }],
      traces: [],
      lanes: [
        {
          laneId: videoLaneId,
          label: 'Video Time',
        },
        {
          laneId: eventsLaneId,
          label: 'Game Events',
        },
        {
          laneId: fragmentsLaneId,
          label: 'Selected Fragments',
        }
      ]
    } 
  }

  componentDidMount() {    
    this.updateCurrentTime(0);
  }

  getSignal() {
    var durationTimeline = 32

    var time = Array.from([
      ...Array(signalLength).keys()
    ], (i) => durationTimeline * i / signalLength);
    var flowSignal = Array.from({length: signalLength}, () => Math.floor(Math.random() * 40));
    var anxietySignal = Array.from({length: signalLength}, () => Math.floor(Math.random() * 40));
    var boredomSignal = Array.from({length: signalLength}, () => Math.floor(Math.random() * 40));

    return {
      duration: durationTimeline, // in seconds
      time: time, // in seconds
      flow: flowSignal,
      anxiety: anxietySignal,
      boredom: boredomSignal 
    }
  }

  getEvents() {
    var events = this.props.args.events.map(e => Object.assign({}, e))
    return events
  }

  getUpdatedEvents(currentTime) {
    var durationTimeline = this.state.signal.duration;

    var baseEvents = this.getEvents();

    var startEndEvents = [
      {
        eventId: 'start',
        tooltip: 'Start',
        laneId: eventsLaneId,
        startTimeMillis: 0,
      },
      {
        eventId: 'end',
        tooltip: 'End',
        laneId: eventsLaneId,
        startTimeMillis: durationTimeline,
      }
    ]

    var timelineEvent = {
      eventId: 'timeline-event',
      laneId: videoLaneId,
      startTimeMillis: 0,
      endTimeMillis: currentTime
    }

    var fullEvents = startEndEvents.concat(baseEvents)
    fullEvents = fullEvents.concat([timelineEvent])

    fullEvents.map((e) => {
      e.startTimeMillis = Math.round(e.startTimeMillis * 1000 + startSignalTime)
      if (e.endTimeMillis !== undefined)  
        e.endTimeMillis = Math.round(e.endTimeMillis * 1000 + startSignalTime)
    })

    return fullEvents;
  }

  getUpdatedTraces(currentTime) {
    var time = this.state.signal.time;
    var flowSignal = this.state.signal.flow;
    var boredomSignal = this.state.signal.boredom;
    var anxietySignal = this.state.signal.anxiety;

    var trace1 = {
      x: time,
      y: flowSignal,
      type: 'scatter',
      name: 'Flow'
    };

    var trace2 = {
      x: time,
      y: anxietySignal,
      xaxis: 'x',
      yaxis: 'y2',
      type: 'scatter',
      name: 'Anxiety'
    };

    var trace3 = {
      x: time,
      y: boredomSignal,
      xaxis: 'x',
      yaxis: 'y3',
      type: 'scatter',
      name: 'Boredom'
    };

    var verticalLines = Array.from(
      [...Array(3).keys()], 
      (i) => getVerticalLine(currentTime, i)
    );

    var traces = [
      trace1, 
      trace2, 
      trace3
    ].concat(verticalLines)

    return traces;
  }

  updateCurrentTime(currentTime) {
    var updatedEvents = this.getUpdatedEvents(currentTime);
    var updatedTraces = this.getUpdatedTraces(currentTime);

    this.setState({
      currentTime: currentTime,
      traces: updatedTraces,
      events: updatedEvents
    });
  }

  render() {
    var self = this;
    var durationTimeline = this.state.signal.duration;
    var videoPath = this.state.video;

    function dateFormat(ms) {
      var formatString = new Date(ms).toLocaleTimeString('en-US', { 
        hour: 'numeric', 
        minute: 'numeric', 
        second: 'numeric',
        hour12: false 
      });
      return formatString.split(" ")[0]
    }

    var signalSizeMilliseconds = 1000 * durationTimeline;

    function onVideoTimeChange(e) {
      var currentTime = e.target.currentTime;
      self.updateCurrentTime(currentTime);
    }

    return (
      <div className="App" style={{width: componentWidth}}>
        <div className="row">
          <div className="col-md-4 player">
            <video style={{width: '100%'}} height="240" controls onTimeUpdate={onVideoTimeChange}>
              <source src={videoPath} type="video/mp4"/>
              Your browser does not support the video tag.
            </video> 
          </div>
          <div className="col-md-8 indicators">
            <Plot
              data={this.state.traces}
              layout={{
                grid: {
                    rows: 3,
                    columns: 1,
                    roworder: 'top to bottom'
                },
                xaxis: {
                  rangeslider: {
                    range: [0, durationTimeline]
                  },
                },
                width: componentWidth * 2/3,
                height: 250,
                margin: {
                  l: 20,
                  r: 5,
                  b: 5,
                  t: 5,
                  pad: 4
                },
                legend: {
                  y: 1.15,
                  orientation: "h",
                  bgcolor: 'rgba(255,255,255,0)'
                }
              }}
            />
          </div>
        </div>
        <div className="row">
          <div className="col-md-12 timeline">
            <Timeline 
              x={startSignalTime}
              y={startSignalTime + signalSizeMilliseconds}
              width={componentWidth} 
              height={200} 
              events={this.state.events} 
              lanes={this.state.lanes} 
              dateFormat={dateFormat} 
              zoomLevels={[
                '1 min',
                '10 secs',
                '1 sec'
              ]}
            />
          </div>
        </div>
      </div>
    );
  }
}
export default withStreamlitConnection(App);
