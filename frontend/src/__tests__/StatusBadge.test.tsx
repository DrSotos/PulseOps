import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { StatusBadge } from "../components/ui/StatusBadge";

describe("StatusBadge Component", () => {
  it("renders operational badge", () => {
    render(<StatusBadge status="operational" />);
    expect(screen.getByText("Operational")).toBeDefined();
  });

  it("renders degraded badge", () => {
    render(<StatusBadge status="degraded" />);
    expect(screen.getByText("Degraded")).toBeDefined();
  });

  it("renders outage badge for down state", () => {
    render(<StatusBadge status="down" />);
    expect(screen.getByText("Outage")).toBeDefined();
  });

  it("renders paused badge", () => {
    render(<StatusBadge status="paused" />);
    expect(screen.getByText("Paused")).toBeDefined();
  });
});

