/**
 * Created by krause on 2016-04-22.
 */
function Timeline(content, legend, wtext, h, radius, textHeight) {
  var svg = content.append("svg").attr({
    "width": wtext,
    "height": h + textHeight,
  }).style({
    "border": "solid black 1px"
  });
  var w = svg.node().clientWidth;
  if(w === 0) { // taking care of firefox
    w = svg.node().getBoundingClientRect()["width"] - 2; // border: 1px
  }
  var visAxisG = svg.append("g");
  var inner = svg.append("g");
  var base = inner.append("g");

  var typeNames = {};
  this.typeNames = function(_) {
    if(!arguments.length) return typeNames;
    typeNames = _;
  };

  var events = [];
  this.events = function(_) {
    if(!arguments.length) return events;
    events = _;
  };

  function fitInto(pixWidth, pixHeight, w, h, fit) {
    var rw = pixWidth / w;
    var rh = pixHeight / h;
    return fit ? Math.min(rw, rh) : Math.max(rw, rh);
  }

  function zoomTo(x, y, factor, scale, off) {
    var f = factor;
    var newScale = scale * factor;
    newScale <= 0 && console.warn("factor: " + factor + " zoom: " + newScale);
    off[0] = (off[0] - x) * f + x;
    off[1] = (off[1] - y) * f + y;
    return newScale;
  }

  function asTransition(sel, smooth) {
    if(!smooth) return sel;
    return sel.transition().duration(750).ease("easeInOutCubic");
  };

  this.update = function() {
    var types = {};
    var groups = {};
    events.forEach(function(e) {
      types[e["id"]] = Math.min(+e["time"], e["id"] in types ? types[e["id"]] : Number.POSITIVE_INFINITY);
      groups[e["group"]] = true;
    });
    var groupScale = d3.scale.category10().domain(Object.keys(groups));

    var lSel = legend.selectAll("div.legend-entry").data(Object.keys(groups), function(g) {
      return g;
    });
    lSel.exit().remove();
    var lSelE = lSel.enter().append("div").classed("legend-entry", true);
    lSelE.append("span").classed("legend-color", true);
    lSelE.append("span").text(" ").style({
      "vertical-align": "middle",
    });
    lSelE.append("span").classed("legend-text", true);
    lSel.selectAll(".legend-text").text(function(g) {
      return typeNames[g] || "???";
    }).style({
      "vertical-align": "middle",
      // "cursor": "pointer",
    });
    // .on("click", function(g) {
    //   jumpToElem({
    //     "link": "#" + g
    //   });
    // });
    lSel.selectAll(".legend-color").style({
      "width": "1em",
      "height": "1em",
      "border": "solid 1px black",
      "background-color": function(g) {
        return groupScale(g);
      },
      "display": "inline-block",
      "vertical-align": "middle",
    });

    var typeList = Object.keys(types);
    typeList.sort(function(ta, tb) {
      return d3.ascending(types[ta], types[tb]);
    });
    var minY = 0;
    var yPos = {};
    typeList.forEach(function(tid, ix) {
      yPos[tid] = h - ix * (radius + 1);
      minY = Math.min(h - ix * (radius + 1), minY);
    });
    var times = events.map(function(e) {
      return +e["time"] * 1000;
    });
    var xScale = d3.time.scale().domain([ d3.min(times), d3.max(times) ]).range([ 0, w ]).nice();
    var visScale = xScale.copy();
    var xAxis = d3.svg.axis().scale(visScale).tickSize(-h).tickSubdivide(true);
    var visAxis = visAxisG.classed({
      "x": true,
      "axis": true
    }).attr({
      "transform": "translate(" + [ 0, h ] + ")"
    }).call(xAxis);

    function zoom() {
      var move = d3.event.translate;
      var s = d3.event.scale;
      applyZoom(move, s, false);
    }

    var zoomObj = d3.behavior.zoom().scaleExtent([ 0.5, 8 ]).on("zoom", zoom);
    svg.call(zoomObj).on("dblclick.zoom", function() {
      showAll(true);
    });

    function showRectangle(rect, margin, fit, smooth) {
      var screenW = w - 2 * margin;
      var screenH = h - 2 * margin;
      var factor = fitInto(screenW, screenH, rect["width"], rect["height"], fit);
      var scale = 1;
      var move = [
        margin + (screenW - rect["width"]) * 0.5 - rect["x"],
        margin + (screenH - rect["height"]) * 0.5 - rect["y"],
      ];
      scale = zoomTo(screenW * 0.5 + margin, screenH * 0.5 + margin, factor, scale, move);
      zoomObj.translate(move);
      zoomObj.scale(scale);
      applyZoom(move, scale, smooth);
    }

    function applyZoom(move, scale, smooth) {
      asTransition(inner, smooth).attr({
        "transform": "translate(" + move + ") scale(" + scale + ")"
      });
      visScale.range([ move[0], move[0] + w * scale ]);
      asTransition(visAxis, smooth).call(xAxis);
      asTransition(label, smooth).attr({
        "font-size": 16 / scale,
      });
    }

    function showAll(smooth) {
      showRectangle({
        "x": 0,
        "y": minY,
        "width": w,
        "height": h - minY,
      }, 5, true, smooth);
    }

    var sel = base.selectAll("rect.event").data(events);
    sel.exit().remove();
    sel.enter().append("rect").classed("event", true);

    function jumpToElem(e) {
      window.location.href = e["link"];
    }

    sel.attr({
      "x": function(e) {
        return xScale(+e["time"] * 1000);
      },
      "y": function(e) {
        return yPos[e["id"]];
      },
      "width": radius,
      "height": radius,
      "fill": function(e) {
        return groupScale(e["group"]);
      },
      "stroke": "black",
      "stroke-width": 0.5,
    }).style({
      "cursor": "pointer",
    }).on("mouseover", function(e) {
      var cur = d3.select(this);
      cur.transition().duration(100).attr({
        "stroke-width": 1,
      });
      label.attr({
        "x": cur.attr("x") - 2,
        "y": cur.attr("y") - 2,
        "text-anchor": "end",
        "alignment-baseline": "bottom",
        "cursor": "pointer",
      }).text(e["name"]).on("click", function() {
        jumpToElem(e);
      }).transition().duration(100).attr({
        "opacity": 1,
      });
      Object.keys(canceled).forEach(function(task) {
        canceled[task] = true;
      });
    }).on("mouseout", function(e) {
      var cur = d3.select(this);
      cur.transition().duration(100).attr({
        "stroke-width": 0.5,
      });
      var task = tasks;
      tasks += 1;
      canceled[task] = false;
      setTimeout(function() {
        var isCanceled = canceled[task];
        delete canceled[task];
        if(isCanceled) {
          return;
        }
        label.on("click", null).attr({
          "cursor": "default",
        }).transition().duration(1000).attr({
          "opacity": 0,
        });
      }, 3000);
    }).on("click", function(e) {
      jumpToElem(e);
    });
    var label = base.append("text").classed("label", true).attr({
      "opacity": 1,
      "cursor": "default",
    });
    var canceled = {};
    var tasks = 0;

    showAll(false);
  };
} // Timeline
