/**
 * D3.js Timeline Visualization for NarraSeed
 * Renders time-series data with turning points and narrative arc
 */

function renderTimeline(containerId, data) {
  const container = document.getElementById(containerId);
  container.innerHTML = "";

  if (!data || !data.segments || data.segments.length === 0) {
    container.innerHTML = "<p>No timeline data available.</p>";
    return;
  }

  const svgContainer = document.createElement("div");
  svgContainer.style.width = "100%";
  svgContainer.style.height = "300px";
  svgContainer.style.position = "relative";
  container.appendChild(svgContainer);

  const margin = { top: 20, right: 30, bottom: 40, left: 60 };
  const width = svgContainer.clientWidth - margin.left - margin.right;
  const height = svgContainer.clientHeight - margin.top - margin.bottom;

  const svg = d3
    .select(svgContainer)
    .append("svg")
    .attr("width", svgContainer.clientWidth)
    .attr("height", svgContainer.clientHeight)
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

  const yScale = d3
    .scaleLinear()
    .domain([0, 1])
    .range([height, 0]);

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

  // Draw confidence band (light fill)
  const area = d3
    .area()
    .x((d) => xScale(d.x))
    .y0((d) => yScale(Math.max(0, d.y - 0.1)))
    .y1((d) => yScale(Math.min(1, d.y + 0.1)))
    .curve(d3.curveMonotoneX);

  svg
    .append("path")
    .datum(dataPoints)
    .attr("fill", "#D4A574")
    .attr("opacity", 0.15)
    .attr("d", area);

  // Draw turning points
  if (data.segments && data.segments.length > 0) {
    const turningIndices = [];
    try {
      // Extract turning points from story text or use evenly spaced markers
      const segmentCount = Math.min(5, Math.max(2, Math.floor(dataPoints.length / 3)));
      for (let i = 0; i < segmentCount; i++) {
        turningIndices.push(Math.floor((i * dataPoints.length) / segmentCount));
      }
    } catch {
      turningIndices.push(Math.floor(dataPoints.length / 2));
    }

    const turningPoints = turningIndices
      .filter((idx) => idx < dataPoints.length)
      .map((idx) => dataPoints[idx]);

    svg
      .selectAll(".turning-point")
      .data(turningPoints)
      .enter()
      .append("circle")
      .attr("class", "turning-point")
      .attr("cx", (d) => xScale(d.x))
      .attr("cy", (d) => yScale(d.y))
      .attr("r", 5)
      .attr("fill", "#8FAE7E")
      .attr("stroke", "#FFFFFF")
      .attr("stroke-width", 2)
      .style("cursor", "pointer")
      .on("mouseover", function () {
        d3.select(this)
          .transition()
          .duration(200)
          .attr("r", 7)
          .attr("fill", "#C67B5C");
      })
      .on("mouseout", function () {
        d3.select(this)
          .transition()
          .duration(200)
          .attr("r", 5)
          .attr("fill", "#8FAE7E");
      });
  }

  // X-axis
  svg
    .append("g")
    .attr("transform", `translate(0,${height})`)
    .call(d3.axisBottom(xScale))
    .append("text")
    .attr("x", width / 2)
    .attr("y", 35)
    .attr("fill", "#5C5750")
    .attr("text-anchor", "middle")
    .attr("font-size", "12px")
    .text("Time");

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
    .text("Value");

  // Arc badge
  const badgeContainer = document.createElement("div");
  badgeContainer.style.marginTop = "16px";
  badgeContainer.innerHTML = `
    <div style="display: flex; gap: 12px; flex-wrap: wrap;">
      <span class="badge" style="background-color: rgba(198, 123, 92, 0.12); color: #C67B5C; padding: 6px 12px; border-radius: 20px; font-size: 12px; font-weight: 600;">
        ${data.arc || "Unknown Arc"}
      </span>
      <span class="badge" style="background-color: rgba(143, 174, 126, 0.12); color: #8FAE7E; padding: 6px 12px; border-radius: 20px; font-size: 12px; font-weight: 600;">
        Confidence: ${((data.grounding?.confidence || 0.85) * 100).toFixed(0)}%
      </span>
    </div>
  `;
  container.appendChild(badgeContainer);
}
