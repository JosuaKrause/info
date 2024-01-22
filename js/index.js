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

import { d3 } from './d3.js';
import { Timeline } from './timeline.js';

function adjustSizes() {
  const headerHeight = d3.select('#smt_header').node().clientHeight;
  const hdMarginAndBorder = 22;
  const elMarginSmall = 15;
  d3.select('#smt_pad').style({
    height: `${hdMarginAndBorder + headerHeight}px`,
  });
  d3.selectAll('.smt_anchor').style({
    top: `${-(elMarginSmall + headerHeight)}px`,
  });
}

function start() {
  window.addEventListener('resize', adjustSizes);
  adjustSizes();
  const w = '100%';
  const h = 300;
  const radius = 8;
  const textHeight = 20;
  const timeline = new Timeline(
    d3.select('#div-timeline'),
    d3.select('#div-legend'),
    w,
    h,
    radius,
    textHeight,
  );
  d3.json('material/timeline.json', (err, data) => {
    if (err) {
      console.warn(err);
      d3.select('#timeline-row').style({
        display: 'none',
      });
      return;
    }
    timeline.typeNames(data.type_names);
    timeline.typeOrder(data.type_order);
    timeline.events(data.events);
    timeline.initVisibleGroups({ '.type_committee': false });
    timeline.update();
  });

  const isBot = /bot|crawl|spider/i.test(navigator.userAgent);
  const gde = d3.selectAll('.gdiv_employment');
  gde.on('click', () => {
    gde.classed({ fadeout: false });
  });
  if (isBot) {
    gde.classed({ fadeout: false });
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', start);
} else {
  start();
}
