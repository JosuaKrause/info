/*
 * Homepage of Josua Krause
 * Copyright (C) 2016  Josua Krause
 * Copyright (C) 2024  Josua Krause
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

function adjustSizes() {
  var header_height = d3.select('#smt_header').node().clientHeight;
  var hd_margin_and_border = 22;
  var el_margin_small = 15;
  d3.select('#smt_pad').style({
    height: hd_margin_and_border + header_height + 'px',
  });
  d3.selectAll('.smt_anchor').style({
    top: -(el_margin_small + header_height) + 'px',
  });
}

function start() {
  window.addEventListener('resize', adjustSizes);
  adjustSizes();
  var w = '100%';
  var h = 300;
  var radius = 8;
  var textHeight = 20;
  var timeline = new Timeline(
    d3.select('#div-timeline'),
    d3.select('#div-legend'),
    w,
    h,
    radius,
    textHeight,
  );
  d3.json('material/timeline.json', function (err, data) {
    if (err) {
      console.warn(err);
      d3.select('#timeline-row').style({
        display: 'none',
      });
      return;
    }
    timeline.typeNames(data['type_names']);
    timeline.typeOrder(data['type_order']);
    timeline.events(data['events']);
    timeline.initVisibleGroups({ '.type_committee': false });
    timeline.update();
  });
}
