/**
 * Created by krause on 2016-04-22.
 */
function Timeline(content, wtext, h, radius, textHeight) {
  var svg = content.append("svg").attr({
    "width": wtext,
    "height": h + textHeight,
  }).style({
    "border": "solid black 1px"
  });
  var w = svg.node().clientWidth;

  var events = [];
  this.events = function(_) {
    if(!arguments.length) return events;
    events = _;
  };

  this.update = function() {
    var types = {};
    var groups = {};
    events.forEach(function(e) {
      types[e["id"]] = Math.min(+e["time"], e["id"] in types ? types[e["id"]] : Number.POSITIVE_INFINITY);
      groups[e["group"]] = true;
    });
    var typeList = Object.keys(types);
    typeList.sort(function(ta, tb) {
      return d3.ascending(types[ta], types[tb]);
    });
    var yPos = {};
    typeList.forEach(function(tid, ix) {
      yPos[tid] = h - ix * radius;
    });
    var times = events.map(function(e) {
      return +e["time"] * 1000;
    });
    var xScale = d3.time.scale().domain([ d3.min(times), d3.max(times) ]).range([ 0, w ]).nice();
    var visScale = xScale.copy();
    var xAxis = d3.svg.axis().scale(visScale).tickSize(-h).tickSubdivide(true);
    var groupScale = d3.scale.category10().domain(Object.keys(groups));
    var visAxis = svg.append("g").classed({
      "x": true,
      "axis": true
    }).attr({
      "transform": "translate(" + [ 0, h ] + ")"
    }).call(xAxis);
    function zoom() {
      var move = d3.event.translate;
      var s = d3.event.scale;
      base.attr({
        "transform": "translate(" + move + ") scale(" + s + ")"
      });
      visScale.range([ move[0], move[0] + w * s ]);
      visAxis.call(xAxis);
      label.attr({
        "font-size": 16 / s
      });
    }
    var base = svg.append("g").append("g");
    svg.call(d3.behavior.zoom().scaleExtent([ 0.5, 8 ]).on("zoom", zoom));
    var sel = base.selectAll("circle.event").data(events);
    sel.exit().remove();
    sel.enter().append("circle").classed("event", true);
    sel.attr({
      "cx": function(e) {
        return xScale(+e["time"] * 1000);
      },
      "cy": function(e) {
        return yPos[e["id"]];
      },
      "r": radius,
      "fill": function(e) {
        return groupScale(e["group"]);
      }
    }).style({
      "cursor": "pointer",
    }).on("mouseover", function(e) {
      var cur = d3.select(this);
      cur.transition().duration(100).attr({
        "r": 2 * radius
      });
      label.attr({
        "display": null,
        "x": cur.attr("cx"),
        "y": cur.attr("cy")
      }).text(e["name"]);
    }).on("mouseout", function(e) {
      var cur = d3.select(this);
      cur.transition().duration(100).attr({
        "r": radius
      });
    }).on("click", function(e) {
      window.location.href = e["link"];
    });
    var label = base.append("text").classed("label", true).attr({
      "display": "none"
    });
  };
} // Timeline
