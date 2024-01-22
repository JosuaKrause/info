/*
 * Homepage of Josua Krause
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
// @ts-check

/**
 * @typedef {{
 *  group: string,
 *  id: string,
 *  link: string,
 *  name: string,
 *  time: number,
 *  endTime?: number,
 * }} TimelineEvent
 */
/**
 * @typedef {{
 *  type_names: { [key: string]: string },
 *  type_order: string[],
 *  events: TimelineEvent[],
 * }} TimelineData
 */
/**
 * @template T
 * @typedef D3Selection<T>
 * @prop {(tag: string) => D3Selection<T>} append
 * @prop {{
 *  (obj: { [key: string]: string | number | boolean | ((g: T) => string | number | boolean) }): D3Selection<T>;
 *  (name: string): string;
 * }} attr
 * @prop {(obj: { [key: string]: string | number | boolean | ((g: T) => string | number | boolean) }) => D3Selection<T>} style
 * @prop {() => HTMLElement} node
 * @prop {() => D3Selection<T>} transition
 * @prop {(time: number) => D3Selection<T>} duration
 * @prop {(curve: string) => D3Selection<T>} ease
 * @prop {(query: string) => D3Selection<T>} selectAll
 * @prop {{
 *  <D>(data: D[], cb: (g: D) => D): D3Selection<D>;
 *  <D>(data: D[]): D3Selection<D>;
 * }} data
 * @prop {() => D3Selection<T>} enter
 * @prop {() => D3Selection<T>} exit
 * @prop {() => D3Selection<T>} remove
 * @prop {(clazzes: { [key: string]: boolean }) => D3Selection<T>} classed
 * @prop {(text: ((g: T) => string) | string) => D3Selection<T>} text
 * @prop {(cb: ((g: T) => void)) => D3Selection<T>} each
 * @prop {(cb: ((g: D3Selection<T>) => void)) => D3Selection<T>} call
 * @prop {(eventName: string, cb: (g: T) => void) => D3Selection<T>} on
 */
/**
 * @template T
 * @typedef {{
 *  domain: (values: T[]) => D3Scale<T>,
 *  range: (values: T[]) => D3Scale<T>,
 *  nice: () => D3Scale<T>,
 *  copy: () => D3Scale<T>,
 *  (g: T): T,
 * }} D3Scale<T>
 */
/**
 * @typedef {{
 *  scale: (scale: D3Scale<number>) => D3Axis,
 *  tickSize: (size: number) => D3Axis,
 *  tickSubdivide: (subdivide: boolean) => D3Axis,
 *  tickFormat: (cb: (date: Date) => string | number) => D3Axis,
 *  <T>(sel: D3Selection<T>): void,
 * }} D3Axis
 */
/**
 * @typedef {{
 *  scaleExtent: (range: number[]) => D3Zoom,
 *  translate: (translate: number[]) => number[] | null,
 *  scale: (scale: number) => number | null,
 *  on: (name: 'zoom', cb: () => void) => D3Zoom,
 *  <T>(sel: D3Selection<T>): void,
 * }} D3Zoom
 */
/**
 * @typedef D3
 * @prop {<T>(query: string) => D3Selection<T>} select
 * @prop {<T>(query: string) => D3Selection<T>} selectAll
 * @prop {(url: string, cb: (err: Error | null, data: TimelineData) => void) => void} json
 * @prop {{ category10: () => D3Scale<string> }} scale
 * @prop {{ scale: () => D3Scale<number> }} time
 * @prop {{ axis: () => D3Axis }} svg
 * @prop {{ zoom: () => D3Zoom }} behavior
 * @prop {{ translate: number[], scale: number }} event
 * @prop {(a: number, b: number) => number} ascending
 * @prop {(values: number[]) => number} min
 * @prop {(values: number[]) => number} max
 */

/** @type {D3} */
// @ts-ignore Property 'd3' does not exist on type 'Window & typeof globalThis'.
export const d3 = window.d3;
