/*
 * Homepage of Josua Krause
 * Copyright (C) 2016–2024  Josua Krause
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 */
// @ts-check

/** @typedef {import("./d3").D3} D3 */
/**
 * @template T
 * @typedef {import("./d3").D3Selection<T>} D3Selection<T>
 */
/** @typedef {import("./d3").TimelineEvent} TimelineEvent */
/** @typedef {{ x: number, y: number, width: number, height: number }} Rect */

export class Timeline {
  constructor(
    /** @type {D3} */ d3,
    /** @type {D3Selection<null>} */ content,
    /** @type {D3Selection<null>} */ legend,
    /** @type {string} */ wtext,
    /** @type {number} */ h,
    /** @type {number} */ radius,
    /** @type {number} */ textHeight,
  ) {
    /** @type {D3} */
    this._d3 = d3;
    /** @type {D3Selection<null>} */
    this._svg = content
      .append('svg')
      .attr({
        width: wtext,
        height: h + textHeight,
      })
      .style({
        border: 'solid black 1px',
      });
    /** @type {D3Selection<null>} */
    this._defs = this._svg.append('defs');
    /** @type {D3Selection<null>} */
    this._legend = legend;
    /** @type {number} */
    this._w = this._svg.node().clientWidth;
    if (this._w === 0) {
      // taking care of firefox
      this._w = this._svg.node().getBoundingClientRect().width - 2; // border: 1px
    }
    /** @type {number} */
    this._h = h;
    /** @type {number} */
    this._radius = radius;
    /** @type {number} */
    this._textHeight = textHeight;
    /** @type {D3Selection<null>} */
    this._visAxisG = this._svg.append('g');
    /** @type {D3Selection<null>} */
    this._inner = this._svg.append('g');
    /** @type {D3Selection<null>} */
    this._base = this._inner.append('g');
    /** @type {{ [key: string]: string }} */
    this._typeNames = {};
    /** @type {string[]} */
    this._typeOrder = [];
    /** @type {TimelineEvent[]} */
    this._events = [];
    /** @type {{ [key: string]: boolean }} */
    this._initVisibleGroups = {};
  }

  typeNames(/** @type {{ [key: string]: string } | null} */ typeNames) {
    if (typeNames) {
      this._typeNames = typeNames;
    }
    return this._typeNames;
  }

  typeOrder(/** @type {string[] | null} */ typeOrder) {
    if (typeOrder) {
      this._typeOrder = typeOrder;
    }
    return this._typeOrder;
  }

  events(/** @type {TimelineEvent[] | null} */ events) {
    if (events) {
      this._events = events;
    }
    return this._events;
  }

  initVisibleGroups(
    /** @type {{ [key: string]: boolean } | null} */ initVisibleGroups,
  ) {
    if (initVisibleGroups) {
      this._initVisibleGroups = initVisibleGroups;
    }
    return this._initVisibleGroups;
  }

  fitInto(
    /** @type {number} */ pixWidth,
    /** @type {number} */ pixHeight,
    /** @type {number} */ w,
    /** @type {number} */ h,
    /** @type {boolean} */ fit,
  ) {
    const rw = pixWidth / w;
    const rh = pixHeight / h;
    return fit ? Math.min(rw, rh) : Math.max(rw, rh);
  }

  zoomTo(
    /** @type {number} */ x,
    /** @type {number} */ y,
    /** @type {number} */ factor,
    /** @type {number} */ scale,
    /** @type {number[]} */ off,
  ) {
    const f = factor;
    const newScale = scale * factor;
    if (newScale <= 0) {
      console.warn('factor: ' + factor + ' zoom: ' + newScale);
    }
    off[0] = (off[0] - x) * f + x;
    off[1] = (off[1] - y) * f + y;
    return newScale;
  }

  asTransition(
    /** @type {D3Selection<string>} */ sel,
    /** @type {boolean} */ smooth,
  ) {
    if (!smooth) {
      return sel;
    }
    return sel.transition().duration(750).ease('easeInOutCubic');
  }

  update() {
    const d3 = this._d3;
    /** @type {{ [key: string]: number }} */
    const types = {};
    /** @type {{ [key: string]: boolean }} */
    const groups = {};
    this._events.forEach((e) => {
      types[e.id] = Math.min(+e.time, types[e.id] ?? Number.POSITIVE_INFINITY);
      groups[e.group] = true;
    });
    const groupScale = d3.scale.category10().domain(this._typeOrder);

    /** @type {{ [key: string]: boolean }} */
    const visibleGroups = {};
    Object.assign(visibleGroups, this._initVisibleGroups);

    const getGroupClass = (/** @type {string} */ g) => {
      return `.type_${g}`;
    };

    const isVisible = (/** @type {string} */ g) => {
      const groupClass = getGroupClass(g);
      return visibleGroups[groupClass] !== undefined
        ? visibleGroups[groupClass]
        : true;
    };

    const isDefault = (/** @type {string} */ g) => {
      const groupClass = getGroupClass(g);
      if (this._initVisibleGroups[groupClass] === undefined) {
        return isVisible(g);
      }
      return this._initVisibleGroups[groupClass] === visibleGroups[groupClass];
    };

    const getDefault = (/** @type {string} */ g) => {
      const groupClass = getGroupClass(g);
      if (this._initVisibleGroups[groupClass] === undefined) {
        return true;
      }
      return this._initVisibleGroups[groupClass];
    };

    const lSel = this._legend
      .selectAll('div.legend-entry')
      .data(this._typeOrder, (g) => g);
    lSel.exit().remove();
    const lSelE = lSel.enter().append('div').classed({ 'legend-entry': true });
    lSelE.append('span').classed({ 'legend-color': true });
    lSelE.append('span').text(' ').style({
      'vertical-align': 'middle',
    });
    lSelE.append('span').classed({ 'legend-text': true });
    lSel
      .selectAll('.legend-text')
      .text((g) => {
        return this._typeNames[g] || '???';
      })
      .style({
        'vertical-align': 'middle',
      });
    lSel
      .style({
        cursor: 'pointer',
      })
      .on('click', (g) => {
        const allDefault = Object.keys(groups).reduce((prev, cur) => {
          return prev && isDefault(cur);
        }, true);
        const allVisible = Object.keys(groups).reduce((prev, cur) => {
          return prev && isVisible(cur);
        }, true);
        if (allDefault) {
          Object.keys(groups).forEach((cur) => {
            visibleGroups[getGroupClass(cur)] =
              cur === g ? true : !getDefault(g);
          });
        } else if (allVisible) {
          Object.keys(groups).forEach((cur) => {
            visibleGroups[getGroupClass(cur)] = cur === g;
          });
        } else {
          visibleGroups[getGroupClass(g)] = !isVisible(g);
        }
        const allInvisible = Object.keys(groups).reduce((prev, cur) => {
          return prev && !isVisible(cur);
        }, true);
        if (allInvisible) {
          Object.keys(groups).forEach((cur) => {
            visibleGroups[getGroupClass(cur)] = getDefault(cur);
          });
        }
        updateLegendColor();
      });

    const opacityInvisible = 0.5;

    const updateLegendColor = () => {
      lSel.selectAll('.legend-text').style({
        opacity: (g) => {
          return isVisible(g) ? null : opacityInvisible;
        },
      });
      lSel.selectAll('.legend-color').style({
        width: '1em',
        height: '1em',
        border: 'solid 1px black',
        opacity: (g) => {
          return isVisible(g) ? null : opacityInvisible;
        },
        'background-color': (g) => {
          return groupScale(g);
        },
        display: 'inline-block',
        'vertical-align': 'middle',
      });
      Object.keys(groups).forEach((g) => {
        /** @type {D3Selection<string>} */
        const group = d3.selectAll(getGroupClass(g));
        group.style({
          display: isVisible(g) ? null : 'none',
        });
      });
      /** @type {D3Selection<TimelineEvent>} */
      const rects = d3.selectAll('rect.event');
      rects.style({
        opacity: (e) => {
          return isVisible(e.group) ? null : opacityInvisible;
        },
      });
      /** @type {D3Selection<null>} */
      const groupHeaders = d3.selectAll('.group_header');
      groupHeaders.style({
        display: function () {
          // NOTE: need node this
          let allInvisible = true;
          const sectionId = this.id;
          /** @type {D3Selection<null>} */
          const mgs = d3.selectAll(`.mg_${sectionId}`);
          mgs.each(function () {
            // NOTE: need node this
            /* eslint no-invalid-this: off */
            if (this.style.display !== 'none') {
              allInvisible = false;
            }
          });
          return allInvisible ? 'none' : null;
        },
      });
    };

    updateLegendColor();
    const typeList = Object.keys(types);
    typeList.sort((ta, tb) => {
      return d3.ascending(types[ta], types[tb]);
    });
    /** @type {number} */
    let minY = 0;
    /** @type {{ [key: string]: number }} */
    const yPos = {};
    typeList.forEach((tid, ix) => {
      yPos[tid] = this._h - ix * (this._radius + 1);
      minY = Math.min(this._h - ix * (this._radius + 1), minY);
    });
    const times = this._events.map((e) => {
      return +e.time * 1000;
    });
    const xScale = d3.time
      .scale()
      .domain([d3.min(times), d3.max(times)])
      .range([0, this._w])
      .nice();
    const visScale = xScale.copy();
    const xAxis = d3.svg
      .axis()
      .scale(visScale)
      .tickSize(-this._h)
      .tickSubdivide(true)
      .tickFormat((date) => {
        const res = date.getFullYear();
        return res % 2 === 1 ? '' : res;
      });
    const visAxis = this._visAxisG
      .classed({
        x: true,
        axis: true,
      })
      .attr({
        transform: `translate(${[0, this._h]})`,
      })
      .call(xAxis);

    const zoom = () => {
      const move = d3.event.translate;
      const s = d3.event.scale;
      applyZoom(move, s, false);
    };

    const zoomObj = d3.behavior.zoom().scaleExtent([0.5, 8]).on('zoom', zoom);
    this._svg.call(zoomObj).on('dblclick.zoom', () => {
      showAll(true);
    });

    const showRectangle = (
      /** @type {Rect} */ rect,
      /** @type {number} */ margin,
      /** @type {boolean} */ fit,
      /** @type {boolean} */ smooth,
    ) => {
      const screenW = this._w - 2 * margin;
      const screenH = this._h - 2 * margin;
      const factor = this.fitInto(
        screenW,
        screenH,
        rect.width,
        rect.height,
        fit,
      );
      let scale = 1;
      const move = [
        margin + (screenW - rect.width) * 0.5 - rect.x,
        margin + (screenH - rect.height) * 0.5 - rect.y,
      ];
      scale = this.zoomTo(
        screenW * 0.5 + margin,
        screenH * 0.5 + margin,
        factor,
        scale,
        move,
      );
      zoomObj.translate(move);
      zoomObj.scale(scale);
      applyZoom(move, scale, smooth);
    };

    const applyZoom = (
      /** @type {number[]} */ move,
      /** @type {number} */ scale,
      /** @type {boolean} */ smooth,
    ) => {
      this.asTransition(this._inner, smooth).attr({
        transform: `translate(${move}) scale(${scale})`,
      });
      visScale.range([move[0], move[0] + this._w * scale]);
      this.asTransition(visAxis, smooth).call(xAxis);
      this.asTransition(label, smooth).attr({
        'font-size': 16 / scale,
      });
    };

    const showAll = (/** @type {boolean} */ smooth) => {
      showRectangle(
        {
          x: 0,
          y: minY,
          width: this._w,
          height: this._h - minY,
        },
        5,
        true,
        smooth,
      );
    };

    /** @type {{ [key: string]: boolean }} */
    const canceled = {};
    let tasks = 0;
    const sel = this._base.selectAll('rect.event').data(this._events);
    sel.exit().remove();
    sel.enter().append('rect').classed({ event: true });

    const jumpToElem = (/** @type {TimelineEvent} */ e) => {
      window.location.href = e.link;
    };

    /** @type {{ [key: string]: string }} */
    const gradients = {
      fade_stroke: 'black',
    };
    sel
      .attr({
        x: (e) => {
          return xScale(+e.time * 1000);
        },
        y: (e) => {
          return yPos[e.id];
        },
        width: (e) => {
          if (!e.endTime) {
            return this._radius;
          }
          if (+e.endTime < 0) {
            return this._w - xScale(+e.time * 1000);
          }
          return (
            xScale((+e.endTime + 31 * 24 * 60 * 60) * 1000) -
            xScale(+e.time * 1000)
          );
        },
        height: this._radius,
        fill: (e) => {
          if (e.endTime && +e.endTime < 0) {
            const gname = `fade_${e.group}`;
            if (!gradients[gname]) {
              gradients[gname] = groupScale(e.group);
            }
            return `url(#${gname})`;
          }
          return groupScale(e.group);
        },
        stroke: (e) => {
          if (e.endTime && +e.endTime < 0) {
            return 'url(#fade_stroke)';
          }
          return 'black';
        },
        'stroke-width': 0.5,
      })
      .style({
        cursor: 'pointer',
      })
      .on('mouseover', function (e) {
        // NOTE: need node this
        const cur = d3.select(this);
        cur.transition().duration(100).attr({
          'stroke-width': 1,
        });
        label
          .attr({
            x: +cur.attr('x') - 2,
            y: +cur.attr('y') - 2,
            'text-anchor': 'end',
            'alignment-baseline': 'bottom',
            cursor: 'pointer',
          })
          .text(e.name)
          .on('click', () => {
            jumpToElem(e);
          })
          .transition()
          .duration(100)
          .attr({
            opacity: 1,
          });
        Object.keys(canceled).forEach((task) => {
          canceled[task] = true;
        });
      })
      .on('mouseout', function (e) {
        // NOTE: need node this
        const cur = d3.select(this);
        cur.transition().duration(100).attr({
          'stroke-width': 0.5,
        });
        const task = tasks;
        tasks += 1;
        canceled[task] = false;
        setTimeout(() => {
          const isCanceled = canceled[task];
          delete canceled[task];
          if (isCanceled) {
            return;
          }
          label
            .on('click', null)
            .attr({
              cursor: 'default',
            })
            .transition()
            .duration(1000)
            .attr({
              opacity: 0,
            });
        }, 3000);
      })
      .on('click', (e) => {
        jumpToElem(e);
      });
    const gradientList = Object.keys(gradients).map((g) => [g, gradients[g]]);
    const grads = this._defs
      .selectAll('linearGradient')
      .data(gradientList, (g) => g);
    const gradsEnter = grads.enter().append('linearGradient');
    gradsEnter.append('stop').attr({
      offset: 0,
      'stop-color': (g) => g[1],
    });
    gradsEnter.append('stop').attr({
      offset: 1,
      'stop-color': 'white',
    });
    grads.exit().remove();
    grads.attr({
      id: (g) => g[0],
    });
    const label = this._base.append('text').classed({ label: true }).attr({
      opacity: 1,
      cursor: 'default',
    });

    showAll(false);
  }
} // Timeline
