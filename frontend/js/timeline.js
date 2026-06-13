/**
 * D3.js Timeline Visualization for NarraSeed
 * Renders time-series data with turning points and narrative arc
 * Responsive: fills its bento cell container
 */

let _timelineResizeObserver = null;
let _lastTimelineData = null;

function renderTimeline(containerId, data) {
  const container = document.getElementById(containerId);
  if (!container) return;
  container.innerHTML = "";

  // Store data for resize redraw
  _lastTimelineData = data;

  if (!data || !data.segments || data.segments.length === 0) {
    container.innerHTML = "<p>No timeline data available.</p>";
    return;
  }

  // Create chart area div that fills the container
  const svgContainer = document.createElement("div");
  svgContainer.className = "chart-area";
  svgContainer.style.width = "100%";
  svgContainer.style.height = "100%";
  svgContainer.style.position = "relative";
  svgContainer.style.flex = "1";
  svgContainer.style.minHeight = "0";
  container.appendChild(svgContainer);

  // Use container's actual dimensions (responsive)
  const containerRect = container.getBoundingClientRect();
  const rawWidth = containerRect.width || 600;
  const rawHeight = containerRect.height || 300;

  const margin = { top: 20, right: 30, bottom: 40, left: 60 };
  const width = rawWidth - margin.left - margin.right;
  const height = rawHeight - margin.top - margin.bottom;

  if (width <= 0 || height <= 0) {
    // Container not yet sized — wait for resize
    return;
  }

  const svg = d3
    .select(svgContainer)
    .append("svg")
    .attr("width", "100%")
    .attr("height", "100%")
    .attr("viewBox", `0 0 ${rawWidth} ${rawHeight}`)
    .attr("preserveAspectRatio", "xMidYMid meet")
    .append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);

  // Extract y-normalized data from citations
  const dataPoints = data.citations
    .filter((c) => c.type === "data")
    .sort((a, b) => a.index - b.index)
    .map((c) => ({ x: c.index, y: c.value }));

  if (dataPoints.length === 0) {
    container.innerHTML = "<p>No data points to visualize.</p>";
    return;
  }

  const xScale = d3
    .scaleLinear()
    .domain([0, d3.max(dataPoints, (d) => d.x)])
    .range([0, width]);

  const yExtent = d3.extent(dataPoints, (d) => d.y);
  const yPadding = (yExtent[1] - yExtent[0]) * 0.08 || 1;
  const yScale = d3
    .scaleLinear()
    .domain([yExtent[0] - yPadding, yExtent[1] + yPadding])
    .nice()
    .range([height, 0]);

  // Custom formatted X Axis using parsed date/time labels
  const xAxis = d3.axisBottom(xScale).ticks(Math.min(dataPoints.length, 8));
  if (data.x_labels && data.x_labels.length > 0) {
    xAxis.tickFormat((d) => {
      const idx = Math.round(d);
      return data.x_labels[idx] !== undefined ? data.x_labels[idx] : idx;
    });
  }

  // Create or select floating tooltip
  let tooltip = d3.select("body").select(".timeline-tooltip");
  if (tooltip.empty()) {
    tooltip = d3
      .select("body")
      .append("div")
      .attr("class", "timeline-tooltip")
      .style("position", "absolute")
      .style("visibility", "hidden")
      .style("background-color", "#FFFFFF")
      .style("border", "1px solid #E8E2DA")
      .style("padding", "8px 12px")
      .style("border-radius", "12px")
      .style("box-shadow", "0 4px 16px rgba(45, 42, 38, 0.08)")
      .style("font-family", "'Plus Jakarta Sans', sans-serif")
      .style("font-size", "14px")
      .style("color", "#2D2A26")
      .style("z-index", "1000")
      .style("pointer-events", "none");
  }

  // Draw grid
  svg
    .append("g")
    .attr("class", "grid")
    .attr("opacity", 0.1)
    .call(
      d3
        .axisLeft(yScale)
        .tickSize(-width)
        .tickFormat("")
    );

  // Draw smooth line curve
  const line = d3
    .line()
    .x((d) => xScale(d.x))
    .y((d) => yScale(d.y))
    .curve(d3.curveMonotoneX);

  svg
    .append("path")
    .datum(dataPoints)
    .attr("fill", "none")
    .attr("stroke", "#C67B5C")
    .attr("stroke-width", 2.5)
    .attr("d", line);

  // Draw confidence band (light fill proportional to data range)
  const bandOffset = (yExtent[1] - yExtent[0]) * 0.05 || 0.5;
  const area = d3
    .area()
    .x((d) => xScale(d.x))
    .y0((d) => yScale(d.y - bandOffset))
    .y1((d) => yScale(d.y + bandOffset))
    .curve(d3.curveMonotoneX);

  svg
    .append("path")
    .datum(dataPoints)
    .attr("fill", "#D4A574")
    .attr("opacity", 0.15)
    .attr("d", area);

  // Draw dots for all data points
  svg
    .selectAll(".data-dot")
    .data(dataPoints)
    .enter()
    .append("circle")
    .attr("class", "data-dot")
    .attr("cx", (d) => xScale(d.x))
    .attr("cy", (d) => yScale(d.y))
    .attr("r", 3.5)
    .attr("fill", "#C67B5C")
    .attr("stroke", "#FFFFFF")
    .attr("stroke-width", 1)
    .attr("opacity", 0.8)
    .style("cursor", "pointer")
    .on("mouseover", function (event, d) {
      d3.select(this)
        .transition()
        .duration(150)
        .attr("r", 5.5)
        .attr("fill", "#B56A4B");

      const xLabel = data.x_labels && data.x_labels[d.x] ? data.x_labels[d.x] : `Point ${d.x}`;
      const origCitation = data.citations.find(c => c.type === 'data' && c.index === d.x);
      const displayVal = origCitation ? origCitation.value : d.y;

      tooltip
        .style("visibility", "visible")
        .html(`<strong>${xLabel}</strong><br/>Value: ${typeof displayVal === 'number' ? displayVal.toLocaleString(undefined, {maximumFractionDigits: 3}) : displayVal}`);
    })
    .on("mousemove", function (event) {
      tooltip
        .style("top", (event.pageY - 45) + "px")
        .style("left", (event.pageX + 15) + "px");
    })
    .on("mouseout", function () {
      d3.select(this)
        .transition()
        .duration(150)
        .attr("r", 3.5)
        .attr("fill", "#C67B5C");
      tooltip.style("visibility", "hidden");
    });

  // Draw turning points from backend analysis
  if (data.turning_points && data.turning_points.length > 0) {
    const turningPoints = data.turning_points
      .map((tp) => {
        const idx = Math.round(tp.index);
        const match = dataPoints.find((d) => d.x === idx);
        return match || null;
      })
      .filter(Boolean);

    svg
      .selectAll(".turning-point")
      .data(turningPoints)
      .enter()
      .append("circle")
      .attr("class", "turning-point")
      .attr("cx", (d) => xScale(d.x))
      .attr("cy", (d) => yScale(d.y))
      .attr("r", 7)
      .attr("fill", "#8FAE7E")
      .attr("stroke", "#FFFFFF")
      .attr("stroke-width", 2.5)
      .style("cursor", "pointer")
      .style("filter", "drop-shadow(0px 2px 4px rgba(0,0,0,0.1))")
      .on("mouseover", function (event, d) {
        d3.select(this)
          .transition()
          .duration(200)
          .attr("r", 9.5)
          .attr("fill", "#C67B5C");

        const xLabel = data.x_labels && data.x_labels[d.x] ? data.x_labels[d.x] : `Point ${d.x}`;
        const origCitation = data.citations.find(c => c.type === 'data' && c.index === d.x);
        const displayVal = origCitation ? origCitation.value : d.y;

        tooltip
          .style("visibility", "visible")
          .html(`<strong>Turning Point</strong><br/><strong>${xLabel}</strong><br/>Value: ${typeof displayVal === 'number' ? displayVal.toLocaleString(undefined, {maximumFractionDigits: 3}) : displayVal}`);
      })
      .on("mousemove", function (event) {
        tooltip
          .style("top", (event.pageY - 45) + "px")
          .style("left", (event.pageX + 15) + "px");
      })
      .on("mouseout", function () {
        d3.select(this)
          .transition()
          .duration(200)
          .attr("r", 7)
          .attr("fill", "#8FAE7E");
        tooltip.style("visibility", "hidden");
      });
  }

  // X-axis
  svg
    .append("g")
    .attr("transform", `translate(0,${height})`)
    .call(xAxis)
    .append("text")
    .attr("x", width / 2)
    .attr("y", 35)
    .attr("fill", "#5C5750")
    .attr("text-anchor", "middle")
    .attr("font-size", "12px")
    .attr("font-weight", "500")
    .text(data.metadata?.x_column ? `Time (${data.metadata.x_column})` : "Time");

  // Y-axis
  svg
    .append("g")
    .call(d3.axisLeft(yScale))
    .append("text")
    .attr("transform", "rotate(-90)")
    .attr("y", 0 - margin.left + 15)
    .attr("x", 0 - height / 2)
    .attr("dy", "1em")
    .attr("fill", "#5C5750")
    .attr("text-anchor", "middle")
    .attr("font-size", "12px")
    .attr("font-weight", "500")
    .text(data.metadata?.y_column ? `Value (${data.metadata.y_column})` : "Value");

  // Responsive redraw via ResizeObserver
  if (_timelineResizeObserver) {
    _timelineResizeObserver.disconnect();
  }
  if (window.ResizeObserver) {
    _timelineResizeObserver = new ResizeObserver(() => {
      clearTimeout(container._resizeTimer);
      container._resizeTimer = setTimeout(() => {
        if (_lastTimelineData) {
          renderTimeline(containerId, _lastTimelineData);
        }
      }, 200);
    });
    _timelineResizeObserver.observe(container);
  }
}
