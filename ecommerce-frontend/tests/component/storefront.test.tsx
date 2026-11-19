import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { ProductCard } from "../../src/components/catalog/ProductCard";
import {
  Price,
  QuantityStepper,
  StockBadge,
} from "../../src/components/ui/Primitives";
import { AdminConsolePage } from "../../src/pages/AdminPages";
import { useAuthStore } from "../../src/stores/auth-store";

function renderWithProviders(ui: React.ReactElement, initialRoute = "/") {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[initialRoute]}>{ui}</MemoryRouter>
    </QueryClientProvider>
  );
}

describe("Storefront Primitives & Components", () => {
  it("renders Price with formatted USD currency and tabular-nums", () => {
    render(<Price amount="189.50" />);
    const el = screen.getByText("$189.50");
    expect(el).toBeInTheDocument();
    expect(el).toHaveClass("tabular-nums");
  });

  it("renders StockBadge states for out-of-stock, low-stock, and in-stock", () => {
    const { rerender } = render(<StockBadge stock={0} />);
    expect(screen.getByText("Out of stock")).toBeInTheDocument();

    rerender(<StockBadge stock={3} />);
    expect(screen.getByText("Only 3 left")).toBeInTheDocument();

    rerender(<StockBadge stock={15} />);
    expect(screen.getByText(/In stock \(15\)/i)).toBeInTheDocument();
  });

  it("clamps QuantityStepper between min and max bounds", () => {
    const onChange = vi.fn();
    render(<QuantityStepper value={2} min={1} max={3} onChange={onChange} />);

    fireEvent.click(screen.getByLabelText("Increase quantity"));
    expect(onChange).toHaveBeenCalledWith(3);

    fireEvent.click(screen.getByLabelText("Decrease quantity"));
    expect(onChange).toHaveBeenCalledWith(1);
  });

  it("renders ProductCard and disables Add to Bag when stock is 0", () => {
    renderWithProviders(
      <ProductCard
        product={{
          id: "prod-test-1",
          name: "Test Mechanical Keyboard",
          description: "Gasket mount keyboard",
          price: "189.00",
          stock_quantity: 0,
          image_url: null,
          category: { id: "cat-1", name: "Workspace", slug: "workspace" },
        }}
      />
    );

    expect(screen.getByText("Test Mechanical Keyboard")).toBeInTheDocument();
    expect(screen.getByText("$189.00")).toBeInTheDocument();
    const button = screen.getByRole("button", { name: /out of stock/i });
    expect(button).toBeDisabled();
  });

  it("blocks non-admin customer role from AdminConsolePage with 403 state", () => {
    useAuthStore.setState({
      user: {
        id: "cust-1",
        email: "customer@example.com",
        full_name: "Customer User",
        is_active: true,
        role: "customer",
      },
      status: "authenticated",
      demoMode: false,
    });

    renderWithProviders(<AdminConsolePage />, "/admin/products");
    expect(
      screen.getByText(/403 — Administrator Access Required/i)
    ).toBeInTheDocument();
  });
});
